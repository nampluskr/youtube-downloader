"""Info-fetch worker pool.

Runs youtube-kit's info() off the UI thread so paste/theme/selection stay
responsive while metadata is being retrieved (D-11, NFR-4). Concurrency is
capped at 3 (D-26, NFR-7) and jobs are submitted in queue order, so the top
of the queue is fetched first.
"""

import os
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

    def submit(self, row: Row, save_folder: str) -> None:
        self._queue.mark_fetching(row)
        self._executor.submit(self._fetch, row, save_folder)

    def _fetch(self, row: Row, save_folder: str) -> None:
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
            defaults = formats.apply_defaults(info)
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
        on_notice: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        self._executor.submit(self._expand, list_id, playlist_url, save_folder, on_notice)

    def _expand(
        self,
        list_id: str,
        playlist_url: str,
        save_folder: str,
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
            self._fetch_pool.submit(row, save_folder)

        if on_notice:
            on_notice(duplicates, 0)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
