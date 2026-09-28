"""JS -> Python bridge methods exposed as window.pywebview.api.

Each public method here is one row in docs/refs/STRUCTURE.md section 3.
Methods add work to the queue/fetch pool and return quickly; results reach
the frontend through Events (Python -> JS), not through return values, so
a slow fetch never blocks the caller.
"""

from typing import Optional

import youtube_kit as yk
from youtube_kit.url import parse_and_normalize_url

from src.hosts.pywebview.events import Events
from src.hosts.pywebview.queue import QueueManager
from src.hosts.pywebview.storage import default_save_folder
from src.hosts.pywebview.workers import FetchPool, PlaylistExpander


class Api:
    def __init__(self) -> None:
        self._save_folder = default_save_folder()
        self._events: Optional[Events] = None
        self._queue = QueueManager(on_change=self._push_rows)
        self._pool = FetchPool(self._queue)
        self._playlists = PlaylistExpander(self._queue, self._pool)
        self._window = None

    def bind(self, window) -> None:
        self._window = window
        self._events = Events(window)

    # ------------------------------------------------------------------
    # JS -> Python
    # ------------------------------------------------------------------

    def add_urls(self, text: str) -> None:
        duplicates = 0
        invalid = 0
        new_rows = []
        playlists = []

        for line in (text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                url_type, std_url, item_id = parse_and_normalize_url(line)
            except yk.InvalidInput:
                invalid += 1
                continue

            if url_type == "playlist":
                playlists.append({"id": item_id, "url": std_url})
                continue

            if self._queue.has_row(item_id) or any(r["id"] == item_id for r in new_rows):
                duplicates += 1
                continue

            new_rows.append({"id": item_id, "url": std_url})

        for entry in new_rows:
            row = self._queue.add_row(entry["id"], entry["url"])
            self._pool.submit(row, self._save_folder)

        for playlist in playlists:
            self._playlists.submit(playlist["id"], playlist["url"], self._save_folder, self._push_notice)

        if self._events:
            self._events.notice(duplicates, invalid)

    def remove(self, row_ids: list[str]) -> None:
        self._queue.remove(row_ids)

    def get_save_folder(self) -> str:
        return self._save_folder

    def choose_folder(self) -> Optional[str]:
        if self._window is None:
            return None
        import webview

        result = self._window.create_file_dialog(webview.FOLDER_DIALOG, directory=self._save_folder)
        if not result:
            return None
        self._save_folder = result[0]
        return self._save_folder

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _push_rows(self) -> None:
        if self._events:
            self._events.rows(self._queue.snapshot())

    def _push_notice(self, duplicates: int, invalid: int) -> None:
        if self._events:
            self._events.notice(duplicates, invalid)
