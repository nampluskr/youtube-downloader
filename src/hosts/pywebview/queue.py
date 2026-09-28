"""Queue model — the single source of truth for row order and state.

The display order in the UI and the internal work order are the SAME list
order kept here (PLAN.md Phase 4/5 rely on this). The frontend only ever
renders a snapshot pushed from here; it never re-orders or re-derives state
on its own.
"""

import threading
from dataclasses import dataclass, field
from typing import Callable, Optional


QUEUED = "queued"
FETCHING = "fetching"
READY = "ready"
FAILED = "failed"


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
        }


class QueueManager:
    def __init__(self, on_change: Callable[[], None]) -> None:
        self._rows: list[Row] = []
        self._lock = threading.Lock()
        self._on_change = on_change

    def snapshot(self) -> list[dict]:
        with self._lock:
            return [row.snapshot() for row in self._rows]

    def has_row(self, row_id: str) -> bool:
        with self._lock:
            return any(row.id == row_id for row in self._rows)

    def add_row(self, row_id: str, url: str) -> Row:
        row = Row(id=row_id, url=url)
        with self._lock:
            self._rows.append(row)
        self._notify()
        return row

    def remove(self, row_ids: list[str]) -> None:
        wanted = set(row_ids)
        with self._lock:
            self._rows = [row for row in self._rows if row.id not in wanted]
        self._notify()

    def mark_fetching(self, row_id: str) -> None:
        self._update(row_id, status=FETCHING, error=None)

    def mark_ready(self, row_id: str, title: str, info: dict, defaults: dict) -> None:
        self._update(
            row_id,
            status=READY,
            title=title,
            info=info,
            error=None,
            resolution_label=defaults["resolution_label"],
            codec_label=defaults["codec_label"],
            audio_label=defaults["audio_label"],
            subtitle_label=defaults["subtitle_label"],
            size_label=defaults["size_label"],
        )

    def mark_failed(self, row_id: str, error: str) -> None:
        self._update(row_id, status=FAILED, error=error)

    def _update(self, row_id: str, **fields) -> None:
        with self._lock:
            for row in self._rows:
                if row.id == row_id:
                    for key, value in fields.items():
                        setattr(row, key, value)
                    break
            else:
                return
        self._notify()

    def _notify(self) -> None:
        self._on_change()
