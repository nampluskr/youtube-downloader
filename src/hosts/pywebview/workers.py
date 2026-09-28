"""Info-fetch worker pool.

Runs youtube-kit's info() off the UI thread so paste/theme/selection stay
responsive while metadata is being retrieved (D-11, NFR-4). Concurrency is
capped at 3 (D-26, NFR-7) and jobs are submitted in queue order, so the top
of the queue is fetched first.
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

import youtube_kit as yk

from src.hosts.pywebview import formats
from src.hosts.pywebview.queue import QueueManager, Row

MAX_CONCURRENT_FETCHES = 3


class FetchPool:
    def __init__(self, queue: QueueManager) -> None:
        self._queue = queue
        self._executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_FETCHES)

    def submit(self, row: Row, save_folder: str, preferred_language: str = formats.PREFERRED_SUBTITLE_LANGUAGE) -> None:
        self._queue.mark_fetching(row)
        self._executor.submit(self._fetch, row, save_folder, preferred_language)

    def _fetch(self, row: Row, save_folder: str, preferred_language: str) -> None:
        # `row` is the exact object add_row_if_absent() returned — mark_*
        # matches it by identity, so if this row was removed (and the same
        # video id re-added as a new Row) in the meantime, this stale result
        # is silently dropped instead of overwriting the new row (see
        # docs/reviews/A4.md finding #1).
        out_dir = os.path.join(save_folder, row.id)
        try:
            info = yk.info(row.url, out_dir=out_dir)
        except yk.InvalidInput as exc:
            self._queue.mark_failed(row, f"Invalid URL: {exc}")
        except yk.VideoUnavailable as exc:
            self._queue.mark_failed(row, f"Unavailable: {exc}")
        except yk.YoutubeKitError as exc:
            self._queue.mark_failed(row, str(exc))
        except Exception as exc:  # unexpected — still keep the row identifiable
            self._queue.mark_failed(row, f"Unexpected error: {exc}")
        else:
            title = info.get("title") or row.id
            defaults = formats.apply_defaults(info, preferred_language=preferred_language)
            self._queue.mark_ready(row, title, info, defaults)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


class PlaylistExpander:
    """Expands a playlist URL into one queue row per video (D-8, FR-4/5).

    Runs on its own small pool, separate from FetchPool's concurrency-3 cap
    (NFR-7): NFR-7 caps concurrent per-VIDEO info fetches, not the one
    playlist-listing call that produces the entries to fetch.
    """

    def __init__(self, queue: QueueManager, fetch_pool: FetchPool) -> None:
        self._queue = queue
        self._fetch_pool = fetch_pool
        self._executor = ThreadPoolExecutor(max_workers=2)

    def submit(
        self,
        list_id: str,
        playlist_url: str,
        save_folder: str,
        preferred_language: str = formats.PREFERRED_SUBTITLE_LANGUAGE,
        on_notice: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        self._executor.submit(self._expand, list_id, playlist_url, save_folder, preferred_language, on_notice)

    def _expand(
        self,
        list_id: str,
        playlist_url: str,
        save_folder: str,
        preferred_language: str,
        on_notice: Optional[Callable[[int, int], None]],
    ) -> None:
        out_dir = os.path.join(save_folder, list_id)
        try:
            data = yk.info(playlist_url, out_dir=out_dir)
        except yk.YoutubeKitError:
            return

        duplicates = 0
        for entry in data.get("entries", []):
            video_id = entry.get("id")
            if not video_id:
                continue  # inaccessible entry (no id) — not counted as a row
            video_url = entry.get("url") or f"https://www.youtube.com/watch?v={video_id}"
            row = self._queue.add_row_if_absent(video_id, video_url)
            if row is None:
                duplicates += 1
                continue
            self._fetch_pool.submit(row, save_folder, preferred_language)

        if on_notice:
            on_notice(duplicates, 0)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


class DownloadRunner:
    """Sequential downloader (D-13, FR-23): one row at a time, top of the
    queue first, re-scanning the live queue order on every step so a move()
    during a run is respected for whichever row hasn't started yet.
    """

    def __init__(self, queue: QueueManager, settings_provider: Callable[[], dict]) -> None:
        self._queue = queue
        self._settings_provider = settings_provider
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()

    def is_active(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._running.set()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stops after the current row (FR-28): no further rows start, and
        the in-flight one is cancelled so it leaves no partial file."""
        self._running.clear()
        self._queue.cancel_active_row()

    def wait_until_idle(self, timeout: Optional[float] = None) -> bool:
        """Blocks until the runner thread has actually exited. A caller that
        is about to tear down the process (window close, FR-33) MUST call
        this with no timeout (the default) after stop() — a bounded wait can
        expire while youtube-kit is still mid-cleanup and let the caller
        destroy the window anyway, leaving a partial file on disk exactly
        like the bug this exists to close (A5 finding #1, confirmed still
        reachable with a bounded wait on Codex's re-verification pass).
        youtube-kit's cancel-triggered cleanup is a local file delete, not a
        network operation, so blocking here has no realistic unbounded case.
        An explicit `timeout` is only for tests. Returns whether the thread
        is idle when this returns."""
        with self._lock:
            thread = self._thread
        if thread is None:
            return True
        thread.join(timeout)
        return not thread.is_alive()

    def _run(self) -> None:
        try:
            while self._running.is_set():
                cancel_event = threading.Event()
                row = self._queue.claim_next_ready_row(cancel_event)
                if row is None:
                    break
                if not self._running.is_set():
                    # stop() landed between the `while` check above and the
                    # claim just now (A5 finding #2, confirmed still
                    # reachable on Codex's re-verification pass): this row
                    # was claimed after stop() already asked
                    # cancel_active_row() to cancel "the" active row, and
                    # found none yet. Cancel it here instead, before any
                    # actual download call runs.
                    cancel_event.set()
                self._download_row(row, cancel_event)
        finally:
            self._running.clear()

    def _download_row(self, row: Row, cancel_event: threading.Event) -> None:
        settings = self._settings_provider()
        save_folder = settings["save_folder"]
        container = settings["container"]
        container = None if container in (None, "auto") else container
        subtitle_format = settings["subtitle_format"]
        out_dir = os.path.join(save_folder, row.id)

        def on_progress(event: dict) -> None:
            stage = event.get("stage")
            if stage == "merge":
                self._queue.mark_merging(row)
            elif stage == "download":
                self._queue.mark_downloading(
                    row,
                    downloaded_bytes=event.get("downloaded_bytes"),
                    total_bytes=event.get("total_bytes"),
                    speed=event.get("speed"),
                    eta=event.get("eta"),
                )

        video_id = row.selected_video_format_id
        audio_id = row.selected_audio_format_id
        subtitle_id = row.selected_subtitle_id

        try:
            attempted = False
            all_reused = True

            if video_id and audio_id:
                attempted = True
                result = yk.video(
                    row.url,
                    video=video_id,
                    audio=audio_id,
                    container=container,
                    out_dir=out_dir,
                    progress=on_progress,
                    cancel=cancel_event,
                )
                all_reused = all_reused and result["status"] == "reused"
            elif audio_id:  # video "None" (D-17): audio-only (FR-15)
                attempted = True
                result = yk.audio(
                    row.url, audio=audio_id, out_dir=out_dir, progress=on_progress, cancel=cancel_event
                )
                all_reused = all_reused and result["status"] == "reused"

            if subtitle_id:
                attempted = True
                result = yk.subtitle(
                    row.url,
                    track=subtitle_id,
                    fmt=subtitle_format,
                    out_dir=out_dir,
                    progress=on_progress,
                    cancel=cancel_event,
                )
                all_reused = all_reused and result["status"] == "reused"

            if not attempted:
                self._queue.mark_failed(row, "Nothing selected to download")
            else:
                self._queue.mark_done(row, reused=all_reused)
        except yk.Cancelled:
            self._queue.mark_canceled(row)
        except yk.YoutubeKitError as exc:
            self._queue.mark_failed(row, str(exc))
        except Exception as exc:  # unexpected — still keep the row identifiable
            self._queue.mark_failed(row, f"Unexpected error: {exc}")
