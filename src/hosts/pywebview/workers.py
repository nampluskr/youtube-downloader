"""Info-fetch worker pool.

Runs youtube-kit's info() off the UI thread so paste/theme/selection stay
responsive while metadata is being retrieved (D-11, NFR-4). Concurrency is
capped at 3 (D-26, NFR-7) and jobs are submitted in queue order, so the top
of the queue is fetched first.
"""

import os
from concurrent.futures import ThreadPoolExecutor

import youtube_kit as yk

from src.hosts.pywebview.queue import QueueManager, Row

MAX_CONCURRENT_FETCHES = 3


class FetchPool:
    def __init__(self, queue: QueueManager) -> None:
        self._queue = queue
        self._executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_FETCHES)

    def submit(self, row: Row, save_folder: str) -> None:
        self._queue.mark_fetching(row.id)
        self._executor.submit(self._fetch, row, save_folder)

    def _fetch(self, row: Row, save_folder: str) -> None:
        out_dir = os.path.join(save_folder, row.id)
        try:
            info = yk.info(row.url, out_dir=out_dir)
        except yk.InvalidInput as exc:
            self._queue.mark_failed(row.id, f"Invalid URL: {exc}")
        except yk.VideoUnavailable as exc:
            self._queue.mark_failed(row.id, f"Unavailable: {exc}")
        except yk.YoutubeKitError as exc:
            self._queue.mark_failed(row.id, str(exc))
        except Exception as exc:  # unexpected — still keep the row identifiable
            self._queue.mark_failed(row.id, f"Unexpected error: {exc}")
        else:
            title = info.get("title") or row.id
            self._queue.mark_ready(row.id, title, info)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
