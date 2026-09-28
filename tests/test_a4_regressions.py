"""Regressions found by the Phase 4 adversarial review (docs/reviews/A4.md)."""

import threading
import time

from src.hosts.pywebview import formats
from src.hosts.pywebview import workers as workers_module
from src.hosts.pywebview.api import Api
from src.hosts.pywebview.queue import READY, QueueManager


class FakeEvents:
    def __init__(self):
        self.pushed = []  # list of (revision, snapshot)

    def rows(self, revision, snapshot):
        self.pushed.append((revision, snapshot))

    def notice(self, duplicates, invalid):
        pass


def wait_until(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_finding1_stale_fetch_for_a_removed_and_readded_row_is_dropped(monkeypatch):
    """A slow fetch for a row that was removed and re-added under the same
    video id must not overwrite the NEW row's (already-selected) state."""
    gate = threading.Event()
    call_count = {"n": 0}

    def fake_info(url, out_dir=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            gate.wait(timeout=5)  # first (stale) fetch blocks here
            return {"title": "Stale"}
        return {"title": "Fresh", "video_formats": [], "audio_formats": []}

    monkeypatch.setattr(workers_module.yk, "info", fake_info)
    api = Api()
    api._events = FakeEvents()

    api.add_urls("https://www.youtube.com/watch?v=aaaaaaaaaaa")
    assert wait_until(lambda: api._queue.has_row("aaaaaaaaaaa"))

    api.remove(["aaaaaaaaaaa"])  # the first fetch is still blocked on `gate`
    api.add_urls("https://www.youtube.com/watch?v=aaaaaaaaaaa")  # re-added, new Row object
    assert wait_until(lambda: api._queue.snapshot()[0]["status"] == READY)
    assert api._queue.snapshot()[0]["title"] == "Fresh"

    gate.set()  # let the stale fetch finish and try to write its result
    time.sleep(0.2)
    row = api._queue.snapshot()[0]
    assert row["title"] == "Fresh"  # not overwritten by the stale "Stale"


def test_finding2_add_row_if_absent_never_creates_two_rows_for_one_id():
    queue = QueueManager(on_change=lambda: None)
    results = []
    barrier = threading.Barrier(2)

    def worker():
        barrier.wait()
        results.append(queue.add_row_if_absent("shared0000", "https://www.youtube.com/watch?v=shared0000"))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    created = [r for r in results if r is not None]
    assert len(created) == 1  # exactly one thread won the race
    assert len(queue.snapshot()) == 1


def test_finding3_default_selection_never_leaves_video_selected_with_none_audio():
    info = {
        "video_formats": [
            {"id": "v", "vcodec": "avc1.640028", "height": 720, "fps": 30, "size": 100},
        ],
        # No non-drc m4a track — the "ideal" audio rule finds nothing.
        "audio_formats": [
            {"id": "a-drc", "ext": "m4a", "abr": 128.0, "drc": True, "original": None},
            {"id": "a-webm", "ext": "webm", "abr": 160.0, "drc": False, "original": None},
        ],
    }
    result = formats.apply_defaults(info)
    assert result["video_format_id"] == "v"
    assert result["audio_format_id"] == "a-webm"  # fallback: best real track, not None


def test_finding4_snapshot_revision_is_monotonic_across_mutations():
    queue = QueueManager(on_change=lambda: None)
    rev0, _ = queue.snapshot_with_revision()
    queue.add_row_if_absent("bbbbbbbbbbb", "https://www.youtube.com/watch?v=bbbbbbbbbbb")
    rev1, _ = queue.snapshot_with_revision()
    queue.move("bbbbbbbbbbb", -1)  # no-op: already at the top, no real mutation
    rev2, _ = queue.snapshot_with_revision()
    queue.remove(["bbbbbbbbbbb"])
    rev3, _ = queue.snapshot_with_revision()

    assert rev1 > rev0
    assert rev2 == rev1  # a no-op move must not fabricate a new revision
    assert rev3 > rev2


def test_finding5_video_options_disambiguates_rounding_collisions():
    info = {
        "video_formats": [
            {"id": "v-2997", "vcodec": "avc1.aa", "ext": "mp4", "height": 1080, "fps": 29.97, "size": 1},
            {"id": "v-30", "vcodec": "vp09.00", "ext": "webm", "height": 1080, "fps": 30, "size": 2},
        ]
    }
    options = formats.video_options(info)
    labels = [o["label"] for o in options]
    assert len(labels) == len(set(labels))  # no two options look identical
    assert any("29.97" in label for label in labels)


def test_finding5_still_disambiguates_when_precise_fps_also_collides():
    """Second A4 verification pass: formats that are identical in every
    displayable field (height/fps/codec/ext) except id must still not share
    a label — nothing but the id can tell them apart in that case."""
    info = {
        "video_formats": [
            {"id": "dup-a", "vcodec": "avc1.aa", "ext": "mp4", "height": 720, "fps": 30, "size": 1},
            {"id": "dup-b", "vcodec": "avc1.aa", "ext": "mp4", "height": 720, "fps": 30, "size": 2},
        ]
    }
    options = formats.video_options(info)
    labels = [o["label"] for o in options]
    assert len(labels) == 2
    assert len(labels) == len(set(labels))
    assert "dup-a" in labels[0] or "dup-a" in labels[1]
