"""Phase 3 — playlist expansion, watch+list handling, and fetch concurrency."""

import threading
import time

from src.hosts.pywebview import workers as workers_module
from src.hosts.pywebview.api import Api


class FakeEvents:
    def __init__(self):
        self.notices = []

    def rows(self, snapshot):
        pass

    def notice(self, duplicates, invalid):
        self.notices.append((duplicates, invalid))


def make_api(monkeypatch, info_fn):
    monkeypatch.setattr(workers_module.yk, "info", info_fn)
    api = Api()
    api._events = FakeEvents()
    return api


def wait_until(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_watch_url_with_list_param_creates_one_video_row(monkeypatch):
    api = make_api(monkeypatch, lambda url, out_dir=None: {"title": "T"})
    api.add_urls("https://www.youtube.com/watch?v=aaaaaaaaaaa&list=PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

    assert wait_until(lambda: len(api._queue.snapshot()) == 1)
    time.sleep(0.1)
    assert len(api._queue.snapshot()) == 1
    assert api._queue.snapshot()[0]["id"] == "aaaaaaaaaaa"


def test_playlist_url_expands_into_one_row_per_entry(monkeypatch):
    entries = [
        {"id": "vid00000001", "url": "https://www.youtube.com/watch?v=vid00000001", "title": "One"},
        {"id": "vid00000002", "url": "https://www.youtube.com/watch?v=vid00000002", "title": "Two"},
        {"id": None, "url": None, "title": "[Unavailable]"},  # inaccessible entry, no id
    ]

    def fake_info(url, out_dir=None):
        if "playlist" in url:
            return {"id": "PLtest", "title": "My Playlist", "entries": entries}
        return {"title": f"Video {url}"}

    api = make_api(monkeypatch, fake_info)
    api.add_urls("https://www.youtube.com/playlist?list=PLtest")

    assert wait_until(lambda: len(api._queue.snapshot()) == 2)
    ids = {row["id"] for row in api._queue.snapshot()}
    assert ids == {"vid00000001", "vid00000002"}
    assert wait_until(lambda: all(row["status"] == "ready" for row in api._queue.snapshot()))


def test_playlist_saves_playlist_json_under_list_id_folder(monkeypatch, tmp_path):
    calls = []

    def fake_info(url, out_dir=None):
        calls.append((url, out_dir))
        if "playlist" in url:
            return {"id": "PLfolder", "entries": []}
        return {"title": "T"}

    api = make_api(monkeypatch, fake_info)
    api._save_folder = str(tmp_path)
    api.add_urls("https://www.youtube.com/playlist?list=PLfolder")

    assert wait_until(lambda: len(calls) == 1)
    playlist_call = calls[0]
    assert playlist_call[1] == str(tmp_path / "PLfolder")


def test_fetch_pool_never_runs_more_than_three_concurrently(monkeypatch):
    active = 0
    max_active = 0
    lock = threading.Lock()

    def fake_info(url, out_dir=None):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.1)
        with lock:
            active -= 1
        return {"title": "T"}

    api = make_api(monkeypatch, fake_info)
    urls = "\n".join(
        f"https://www.youtube.com/watch?v=vid{str(i).zfill(8)}" for i in range(9)
    )
    api.add_urls(urls)

    assert wait_until(lambda: len(api._queue.snapshot()) == 9)
    assert wait_until(
        lambda: all(row["status"] == "ready" for row in api._queue.snapshot()), timeout=5
    )
    assert max_active <= 3
