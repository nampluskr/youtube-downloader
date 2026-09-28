"""Phase 2 — queue model and URL input flow.

youtube_kit.info() is monkeypatched so these tests run offline and
deterministically; the point under test is the queue's state machine and
add_urls parsing, not youtube-kit itself (already covered by youtube-kit's
own tests).
"""

import threading
import time

from src.hosts.pywebview import workers as workers_module
from src.hosts.pywebview.api import Api
from src.hosts.pywebview.queue import FAILED, FETCHING, QUEUED, READY


class FakeEvents:
    def __init__(self):
        self.rows_calls = []
        self.notices = []

    def rows(self, revision, snapshot):
        self.rows_calls.append(snapshot)

    def notice(self, duplicates, invalid):
        self.notices.append((duplicates, invalid))


def make_api(monkeypatch, info_fn):
    monkeypatch.setattr(workers_module.yk, "info", info_fn)
    api = Api()
    api._events = FakeEvents()  # bind() needs a real window; tests use the events hook directly
    return api


def wait_until(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_single_video_url_creates_row_immediately(monkeypatch):
    gate = threading.Event()

    def fake_info(url, out_dir=None):
        gate.wait(timeout=5)
        return {"title": "Fetched Title"}

    api = make_api(monkeypatch, fake_info)
    api.add_urls("https://www.youtube.com/watch?v=JyEsEcsCqzM")

    assert wait_until(lambda: api._queue.has_row("JyEsEcsCqzM"))
    row = api._queue.snapshot()[0]
    assert row["status"] in (QUEUED, FETCHING)

    gate.set()
    assert wait_until(lambda: api._queue.snapshot()[0]["status"] == READY)
    assert api._queue.snapshot()[0]["title"] == "Fetched Title"


def test_multiline_paste_dedupes_and_flags_invalid(monkeypatch):
    api = make_api(monkeypatch, lambda url, out_dir=None: {"title": "T"})

    text = "\n".join([
        "https://www.youtube.com/watch?v=aaaaaaaaaaa",
        "https://www.youtube.com/watch?v=bbbbbbbbbbb",
        "https://www.youtube.com/watch?v=aaaaaaaaaaa",  # duplicate within paste
        "not a youtube url",
    ])
    api.add_urls(text)

    assert wait_until(lambda: len(api._queue.snapshot()) == 2)
    ids = {row["id"] for row in api._queue.snapshot()}
    assert ids == {"aaaaaaaaaaa", "bbbbbbbbbbb"}
    assert api._events.notices[-1] == (1, 1)


def test_duplicate_against_existing_queue_row_is_skipped(monkeypatch):
    api = make_api(monkeypatch, lambda url, out_dir=None: {"title": "T"})
    api.add_urls("https://www.youtube.com/watch?v=ccccccccccc")
    assert wait_until(lambda: len(api._queue.snapshot()) == 1)

    api.add_urls("https://www.youtube.com/watch?v=ccccccccccc")
    time.sleep(0.1)
    assert len(api._queue.snapshot()) == 1
    assert api._events.notices[-1] == (1, 0)


def test_fetch_failure_keeps_other_rows_and_marks_failed_row(monkeypatch):
    import youtube_kit as yk

    def fake_info(url, out_dir=None):
        if "bad" in url:
            raise yk.VideoUnavailable("gone")
        return {"title": "Good Title"}

    api = make_api(monkeypatch, fake_info)
    api.add_urls("\n".join([
        "https://www.youtube.com/watch?v=badbadbadba",
        "https://www.youtube.com/watch?v=goodgoodgoo",
    ]))

    assert wait_until(lambda: len(api._queue.snapshot()) == 2)
    assert wait_until(
        lambda: {r["id"]: r["status"] for r in api._queue.snapshot()}
        == {"badbadbadba": FAILED, "goodgoodgoo": READY}
    )
    failed_row = next(r for r in api._queue.snapshot() if r["id"] == "badbadbadba")
    assert failed_row["error"]
    good_row = next(r for r in api._queue.snapshot() if r["id"] == "goodgoodgoo")
    assert good_row["title"] == "Good Title"


def test_remove_deletes_queued_row(monkeypatch):
    gate = threading.Event()

    def fake_info(url, out_dir=None):
        gate.wait(timeout=5)
        return {"title": "T"}

    api = make_api(monkeypatch, fake_info)
    api.add_urls("https://www.youtube.com/watch?v=removemeeee")
    assert wait_until(lambda: api._queue.has_row("removemeeee"))

    api.remove(["removemeeee"])
    assert api._queue.snapshot() == []
    gate.set()


def test_playlist_url_does_not_create_row_or_count_as_invalid(monkeypatch):
    api = make_api(monkeypatch, lambda url, out_dir=None: {"title": "T"})
    api.add_urls("https://www.youtube.com/playlist?list=PLyPc3E0Xm540Yfdln9qlVyyrqRME80jJm")
    time.sleep(0.1)
    assert api._queue.snapshot() == []
    assert api._events.notices[-1] == (0, 0)


def test_add_urls_returns_before_fetch_completes(monkeypatch):
    gate = threading.Event()

    def slow_info(url, out_dir=None):
        gate.wait(timeout=5)
        return {"title": "T"}

    api = make_api(monkeypatch, slow_info)
    started = time.time()
    api.add_urls("https://www.youtube.com/watch?v=slowslowslo")
    elapsed = time.time() - started

    assert elapsed < 1.0  # NFR-4: does not block on the fetch
    gate.set()
