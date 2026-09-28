"""JS -> Python bridge methods exposed as window.pywebview.api.

Each public method here is one row in docs/refs/STRUCTURE.md section 3.
Methods add work to the queue/fetch pool and return quickly; results reach
the frontend through Events (Python -> JS), not through return values, so
a slow fetch or download never blocks the caller.
"""

from typing import Optional

import youtube_kit as yk
from youtube_kit.url import parse_and_normalize_url

from src.hosts.pywebview import settings as settings_module
from src.hosts.pywebview.events import Events
from src.hosts.pywebview.queue import QueueManager
from src.hosts.pywebview.workers import DownloadRunner, FetchPool, PlaylistExpander


class Api:
    def __init__(self) -> None:
        self._settings = settings_module.load()
        self._events: Optional[Events] = None
        self._queue = QueueManager(on_change=self._push_rows)
        self._pool = FetchPool(self._queue)
        self._playlists = PlaylistExpander(self._queue, self._pool)
        self._runner = DownloadRunner(self._queue, self._get_settings_snapshot)
        self._window = None
        self._force_close = False

    def bind(self, window) -> None:
        self._window = window
        self._events = Events(window)
        window.events.resized += self._on_resized

    # ------------------------------------------------------------------
    # JS -> Python: queue
    # ------------------------------------------------------------------

    def add_urls(self, text: str) -> None:
        duplicates = 0
        invalid = 0
        playlists = []
        save_folder = self._settings["save_folder"]
        preferred_language = self._settings["preferred_language"]

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

            # add_row_if_absent() checks-then-inserts under one lock, so this
            # can't race a concurrent PlaylistExpander adding the same video
            # id (docs/reviews/A4.md finding #2).
            row = self._queue.add_row_if_absent(item_id, std_url)
            if row is None:
                duplicates += 1
                continue
            self._pool.submit(row, save_folder, preferred_language)

        for playlist in playlists:
            self._playlists.submit(
                playlist["id"], playlist["url"], save_folder, preferred_language, self._push_notice
            )

        if self._events:
            self._events.notice(duplicates, invalid)

    def remove(self, row_ids: list[str]) -> None:
        removed = self._queue.remove(row_ids)
        for row in removed:
            self._runner.cancel_row(row)  # FR-27: cancel if it was downloading

    def clear_completed(self) -> None:
        self._queue.clear_completed()

    def move(self, row_id: str, delta: int) -> None:
        self._queue.move(row_id, delta)

    def select(self, row_id: str, field: str, value: Optional[str]) -> None:
        self._queue.select(row_id, field, value)

    # ------------------------------------------------------------------
    # JS -> Python: download control
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._runner.start()

    def stop(self) -> None:
        self._runner.stop()

    def is_downloading(self) -> bool:
        return self._runner.is_active()

    def should_force_close(self) -> bool:
        return self._force_close

    def confirm_close(self, keep_downloading: bool) -> None:
        """Called by the frontend's close-confirmation dialog (FR-33)."""
        if keep_downloading or self._window is None:
            return
        self._force_close = True  # skip the confirm dialog if 'closing' fires again
        self._runner.stop()
        self._window.destroy()

    # ------------------------------------------------------------------
    # JS -> Python: settings
    # ------------------------------------------------------------------

    def get_settings(self) -> dict:
        return dict(self._settings)

    def save_settings(self, patch: dict) -> dict:
        for key in settings_module.defaults():
            if key in patch:
                self._settings[key] = patch[key]
        settings_module.save(self._settings)
        return dict(self._settings)

    def choose_folder(self) -> Optional[str]:
        if self._window is None:
            return None
        import webview

        result = self._window.create_file_dialog(webview.FOLDER_DIALOG, directory=self._settings["save_folder"])
        if not result:
            return None
        self._settings["save_folder"] = result[0]
        settings_module.save(self._settings)
        return self._settings["save_folder"]

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _get_settings_snapshot(self) -> dict:
        return dict(self._settings)

    def _on_resized(self, width: int, height: int) -> None:
        self._settings["window_width"] = width
        self._settings["window_height"] = height
        settings_module.save(self._settings)

    def _push_rows(self) -> None:
        if self._events:
            revision, snapshot = self._queue.snapshot_with_revision()
            self._events.rows(revision, snapshot)

    def _push_notice(self, duplicates: int, invalid: int) -> None:
        if self._events:
            self._events.notice(duplicates, invalid)
