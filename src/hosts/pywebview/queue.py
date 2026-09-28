"""Queue model — the single source of truth for row order and state.

The display order in the UI and the internal work order are the SAME list
order kept here (PLAN.md Phase 4/5 rely on this). The frontend only ever
renders a snapshot pushed from here; it never re-orders or re-derives state
on its own.
"""

import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

from src.hosts.pywebview import formats

QUEUED = "queued"
FETCHING = "fetching"
READY = "ready"
FAILED = "failed"
DOWNLOADING = "downloading"
MERGING = "merging"
DONE = "done"
EXISTS = "exists"
CANCELED = "canceled"

TERMINAL_COMPLETE = (DONE, EXISTS)
ACTIVE_DOWNLOAD = (DOWNLOADING, MERGING)


@dataclass
class Row:
    id: str
    url: str
    title: Optional[str] = None
    status: str = QUEUED
    error: Optional[str] = None
    info: Optional[dict] = field(default=None, repr=False)
    resolution_label: str = ""
    codec_label: str = ""
    audio_label: str = ""
    subtitle_label: str = ""
    size_label: str = "-"

    # Selection state (Phase 4). Options are computed once, right after
    # fetch, from the raw info() result; formats.py never invents formats
    # outside these lists (NFR-6).
    video_options: list = field(default_factory=list, repr=False)
    audio_options: list = field(default_factory=list, repr=False)
    subtitle_options: list = field(default_factory=list, repr=False)
    selected_resolution_key: Optional[str] = None
    selected_video_format_id: Optional[str] = None
    selected_audio_format_id: Optional[str] = None
    selected_subtitle_id: Optional[str] = None

    # Download progress (Phase 5). downloaded_bytes/total_bytes/speed/eta
    # mirror youtube-kit's progress event fields exactly and stay None
    # whenever the backend doesn't provide them (NFR-6 — never estimated).
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    speed: Optional[float] = None
    eta: Optional[int] = None

    # Set atomically with status when a row is claimed for download (see
    # claim_next_ready_row). Cancellation (remove/stop) reads and sets this
    # under the SAME lock that claims it, so there is no window where a
    # row is "Downloading" without a cancel_event a canceller can reach
    # (docs/reviews/A5.md finding #2).
    cancel_event: Optional["threading.Event"] = field(default=None, repr=False)

    def snapshot(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title or self.id,
            "status": self.status,
            "error": self.error,
            "resolution": self.resolution_label,
            "codec": self.codec_label,
            "audio": self.audio_label,
            "subtitle": self.subtitle_label,
            "size": self.size_label,
            "videoOptions": formats.serialize_video_options(self.video_options),
            "audioOptions": formats.serialize_audio_options(self.audio_options),
            "subtitleOptions": self.subtitle_options,
            "selectedResolutionKey": self.selected_resolution_key,
            "selectedVideoFormatId": self.selected_video_format_id,
            "selectedAudioFormatId": self.selected_audio_format_id,
            "selectedSubtitleId": self.selected_subtitle_id,
            "downloadedBytes": self.downloaded_bytes,
            "totalBytes": self.total_bytes,
            "speed": self.speed,
            "eta": self.eta,
        }


class QueueManager:
    def __init__(self, on_change: Callable[[], None]) -> None:
        self._rows: list[Row] = []
        self._lock = threading.Lock()
        self._on_change = on_change
        # Bumped under _lock on every mutation. Pushed to JS alongside each
        # snapshot so a push that was computed before a later mutation can
        # never overwrite a push that already reflects that mutation (a
        # background fetch thread and the UI thread can both call into this
        # class concurrently, and evaluate_js() can be slow enough for their
        # sends to reorder).
        self._revision = 0

    def snapshot_with_revision(self) -> tuple[int, list[dict]]:
        with self._lock:
            return self._revision, [row.snapshot() for row in self._rows]

    def snapshot(self) -> list[dict]:
        return self.snapshot_with_revision()[1]

    def has_row(self, row_id: str) -> bool:
        with self._lock:
            return any(row.id == row_id for row in self._rows)

    def add_row_if_absent(self, row_id: str, url: str) -> Optional[Row]:
        """Atomically checks-then-appends so two callers racing on the same
        video id (e.g. two playlists sharing a video, or a playlist and a
        plain paste) can never both add a row for it."""
        with self._lock:
            if any(r.id == row_id for r in self._rows):
                return None
            row = Row(id=row_id, url=url)
            self._rows.append(row)
            self._revision += 1
        self._notify()
        return row

    def remove(self, row_ids: list[str]) -> list[Row]:
        """Returns the Row objects actually removed. If any removed row is
        currently downloading/merging, its cancel_event is set right here,
        under the same lock that claim_next_ready_row() uses to install that
        event — so this can never race a download that is *about* to start
        but hasn't registered its cancel_event yet (FR-27, A5 finding #2)."""
        wanted = set(row_ids)
        with self._lock:
            removed = [row for row in self._rows if row.id in wanted]
            for row in removed:
                if row.status in ACTIVE_DOWNLOAD and row.cancel_event is not None:
                    row.cancel_event.set()
            self._rows = [row for row in self._rows if row.id not in wanted]
            self._revision += 1
        self._notify()
        return removed

    def clear_completed(self) -> None:
        """Removes Done/Exists rows only (FR-29); queued/failed/etc. stay."""
        with self._lock:
            self._rows = [row for row in self._rows if row.status not in TERMINAL_COMPLETE]
            self._revision += 1
        self._notify()

    def claim_next_ready_row(self, cancel_event: "threading.Event") -> Optional[Row]:
        """Atomically finds the top-most Ready row and flips it to
        Downloading *and* installs `cancel_event` in one locked step (D-13,
        FR-23): reading the row's selections happens AFTER this, so a
        select() call — guarded by `status != READY` — can no longer race
        with it (docs/reviews/A4.md finding #4's ordering concern, applied
        here too). Installing cancel_event in this same lock (rather than
        later, e.g. in the caller) is what lets remove()/cancel_active_row()
        reach a just-claimed row with no gap (A5 finding #2)."""
        with self._lock:
            for row in self._rows:
                if row.status == READY:
                    row.status = DOWNLOADING
                    row.cancel_event = cancel_event
                    self._revision += 1
                    claimed = row
                    break
            else:
                return None
        self._notify()
        return claimed

    def cancel_active_row(self) -> bool:
        """Cancels whichever row is currently Downloading/Merging (FR-28),
        looked up fresh under the lock so it can't race claim_next_ready_row
        either. Returns whether a row was found and canceled."""
        with self._lock:
            for row in self._rows:
                if row.status in ACTIVE_DOWNLOAD and row.cancel_event is not None:
                    row.cancel_event.set()
                    return True
            return False

    def mark_fetching(self, row: Row) -> None:
        self._update_row(row, status=FETCHING, error=None)

    def mark_ready(self, row: Row, title: str, info: dict, defaults: dict) -> None:
        self._update_row(
            row,
            status=READY,
            title=title,
            info=info,
            error=None,
            resolution_label=defaults["resolution_label"],
            codec_label=defaults["codec_label"],
            audio_label=defaults["audio_label"],
            subtitle_label=defaults["subtitle_label"],
            size_label=defaults["size_label"],
            video_options=defaults["video_options"],
            audio_options=defaults["audio_options"],
            subtitle_options=defaults["subtitle_options"],
            selected_resolution_key=defaults["resolution_key"],
            selected_video_format_id=defaults["video_format_id"],
            selected_audio_format_id=defaults["audio_format_id"],
            selected_subtitle_id=defaults["subtitle_track_id"],
        )

    def mark_failed(self, row: Row, error: str) -> None:
        self._update_row(row, status=FAILED, error=error)

    def mark_downloading(
        self,
        row: Row,
        downloaded_bytes: Optional[int] = None,
        total_bytes: Optional[int] = None,
        speed: Optional[float] = None,
        eta: Optional[int] = None,
    ) -> None:
        self._update_row(
            row,
            status=DOWNLOADING,
            downloaded_bytes=downloaded_bytes,
            total_bytes=total_bytes,
            speed=speed,
            eta=eta,
        )

    def mark_merging(self, row: Row) -> None:
        self._update_row(row, status=MERGING, speed=None, eta=None)

    def mark_done(self, row: Row, reused: bool) -> None:
        self._update_row(row, status=EXISTS if reused else DONE, error=None)

    def mark_canceled(self, row: Row) -> None:
        self._update_row(row, status=CANCELED)

    def move(self, row_id: str, delta: int) -> None:
        """delta -1 = up, +1 = down (FR-13/14). List order IS work order."""
        with self._lock:
            index = next((i for i, r in enumerate(self._rows) if r.id == row_id), None)
            if index is None:
                return
            target = index + delta
            if target < 0 or target >= len(self._rows):
                return
            self._rows[index], self._rows[target] = self._rows[target], self._rows[index]
            self._revision += 1
        self._notify()

    def select(self, row_id: str, field_name: str, value: Optional[str]) -> None:
        """Applies a user's resolution/codec/audio/subtitle choice (FR-7~11).

        Ignores any value that is not one of the row's own real options —
        never fabricates a selection (NFR-6) — and enforces D-17: audio
        cannot be set to None while a video format is selected.
        """
        with self._lock:
            row = next((r for r in self._rows if r.id == row_id), None)
            if row is None or row.status != READY:
                return

            if field_name == "resolution":
                if value is None:
                    row.selected_resolution_key = None
                    row.selected_video_format_id = None
                elif any(r["key"] == value for r in row.video_options):
                    row.selected_resolution_key = value
                    row.selected_video_format_id = formats.formats_for_resolution_key(
                        row.video_options, value
                    )[0]["id"]
                    if row.selected_audio_format_id is None and row.audio_options:
                        # D-17: a selected video forbids "None" audio.
                        audio_fmt = formats.select_default_audio(row.info) or formats.select_fallback_audio(
                            row.info
                        )
                        if audio_fmt:
                            row.selected_audio_format_id = audio_fmt["id"]
                else:
                    return
            elif field_name == "codec":
                candidates = formats.formats_for_resolution_key(row.video_options, row.selected_resolution_key)
                if value is not None and any(f["id"] == value for f in candidates):
                    row.selected_video_format_id = value
                else:
                    return
            elif field_name == "audio":
                if value is None:
                    if row.selected_video_format_id is not None:
                        return  # D-17
                    row.selected_audio_format_id = None
                elif any(o["id"] == value for o in row.audio_options):
                    row.selected_audio_format_id = value
                else:
                    return
            elif field_name == "subtitle":
                if value is None:
                    row.selected_subtitle_id = None
                elif any(o["id"] == value for o in row.subtitle_options):
                    row.selected_subtitle_id = value
                else:
                    return
            else:
                return

            labels = formats.relabel(
                row.info,
                row.selected_video_format_id,
                row.selected_audio_format_id,
                row.selected_subtitle_id,
            )
            row.resolution_label = labels["resolution_label"]
            row.codec_label = labels["codec_label"]
            row.audio_label = labels["audio_label"]
            row.subtitle_label = labels["subtitle_label"]
            row.size_label = labels["size_label"]
            self._revision += 1

        self._notify()

    def _update_row(self, row: Row, **fields) -> None:
        """Matches by object identity, not id string: if `row` was removed
        (and possibly replaced by a new row reusing the same video id), a
        fetch that was already in flight for the OLD row must not resurrect
        stale data onto the new one."""
        with self._lock:
            if not any(r is row for r in self._rows):
                return
            for key, value in fields.items():
                setattr(row, key, value)
            self._revision += 1
        self._notify()

    def _notify(self) -> None:
        self._on_change()
