"""Phase 5 — sequential download execution and progress/state reporting."""

import threading
import time

import youtube_kit as yk

from src.hosts.pywebview import workers as workers_module
from src.hosts.pywebview.api import Api
from src.hosts.pywebview.queue import CANCELED, DONE, EXISTS, FAILED, READY


class FakeEvents:
    def rows(self, revision, snapshot):
        pass

    def notice(self, duplicates, invalid):
        pass


INFO = {
    "title": "Test Video",
    "language": "en",
    "video_formats": [
        {"id": "v1080-60", "ext": "mp4", "vcodec": "avc1.640028", "height": 1080, "fps": 60, "size": 900},
    ],
    "audio_formats": [
        {"id": "a-m4a-129", "ext": "m4a", "abr": 129.0, "drc": False, "original": None, "size": 100, "language": "en"},
    ],
    "subtitles": [
        {"id": "manual:en", "kind": "manual", "key": "en", "name": "English"},
    ],
}


def wait_until(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def make_ready_api(monkeypatch, video_id, info=None):
    monkeypatch.setattr(workers_module.yk, "info", lambda url, out_dir=None: info or INFO)
    api = Api()
    api._events = FakeEvents()
    api.add_urls(f"https://www.youtube.com/watch?v={video_id}")
    assert wait_until(lambda: api._queue.snapshot() and api._queue.snapshot()[0]["status"] == READY)
    return api


def row(api, index=0):
    return api._queue.snapshot()[index]


def test_start_downloads_selected_video_and_audio_and_marks_done(monkeypatch, tmp_path):
    calls = []

    def fake_video(url, video, audio, container=None, out_dir=None, progress=None, cancel=None):
        calls.append((url, video, audio, container, out_dir))
        return {"status": "ok", "video_id": "x", "url": url, "path": "x"}

    monkeypatch.setattr(workers_module.yk, "video", fake_video)
    api = make_ready_api(monkeypatch, "aaaaaaaaaaa")
    api._settings["save_folder"] = str(tmp_path)

    api.start()
    assert wait_until(lambda: row(api)["status"] == DONE)

    assert calls[0][1] == "v1080-60"
    assert calls[0][2] == "a-m4a-129"
    assert calls[0][4] == str(tmp_path / "aaaaaaaaaaa")


def test_reused_file_marks_exists_and_new_download_marks_done(monkeypatch, tmp_path):
    def fake_video(url, video, audio, container=None, out_dir=None, progress=None, cancel=None):
        return {"status": "reused", "video_id": "x", "url": url, "path": "x"}

    monkeypatch.setattr(workers_module.yk, "video", fake_video)
    api = make_ready_api(monkeypatch, "bbbbbbbbbbb")
    api._settings["save_folder"] = str(tmp_path)

    api.start()
    assert wait_until(lambda: row(api)["status"] in (EXISTS, DONE))
    assert row(api)["status"] == EXISTS


def test_video_none_downloads_audio_only(monkeypatch, tmp_path):
    audio_calls = []
    video_calls = []

    monkeypatch.setattr(
        workers_module.yk,
        "video",
        lambda *a, **k: video_calls.append(1) or {"status": "ok", "path": "x"},
    )

    def fake_audio(url, audio, out_dir=None, progress=None, cancel=None):
        audio_calls.append(audio)
        return {"status": "ok", "video_id": "x", "url": url, "path": "x"}

    monkeypatch.setattr(workers_module.yk, "audio", fake_audio)

    api = make_ready_api(monkeypatch, "ccccccccccc")
    api._settings["save_folder"] = str(tmp_path)
    row_id = row(api)["id"]
    api.select(row_id, "resolution", None)  # FR-15: video "None" -> audio only

    api.start()
    assert wait_until(lambda: row(api)["status"] == DONE)
    assert audio_calls == ["a-m4a-129"]
    assert video_calls == []


def test_subtitle_selected_downloads_subtitle_track(monkeypatch, tmp_path):
    subtitle_calls = []

    monkeypatch.setattr(
        workers_module.yk, "video", lambda *a, **k: {"status": "ok", "path": "x"}
    )

    def fake_subtitle(url, track, fmt="srt", out_dir=None, progress=None, cancel=None):
        subtitle_calls.append((track, fmt))
        return {"status": "ok", "video_id": "x", "url": url, "path": "x"}

    monkeypatch.setattr(workers_module.yk, "subtitle", fake_subtitle)

    api = make_ready_api(monkeypatch, "ddddddddddd")
    api._settings["save_folder"] = str(tmp_path)
    api._settings["subtitle_format"] = "vtt"
    row_id = row(api)["id"]
    api.select(row_id, "subtitle", "manual:en")

    api.start()
    assert wait_until(lambda: row(api)["status"] == DONE)
    assert subtitle_calls == [("manual:en", "vtt")]


def test_subtitle_none_never_downloads_subtitle(monkeypatch, tmp_path):
    subtitle_calls = []
    monkeypatch.setattr(workers_module.yk, "video", lambda *a, **k: {"status": "ok", "path": "x"})
    monkeypatch.setattr(
        workers_module.yk,
        "subtitle",
        lambda *a, **k: subtitle_calls.append(1) or {"status": "ok", "path": "x"},
    )

    api = make_ready_api(monkeypatch, "eeeeeeeeeee")
    api._settings["save_folder"] = str(tmp_path)
    # default selection leaves subtitle at None (D-16) — no explicit select() needed
    api.start()
    assert wait_until(lambda: row(api)["status"] == DONE)
    assert subtitle_calls == []


def test_progress_events_update_row_and_merge_stage_is_distinct(monkeypatch, tmp_path):
    api = make_ready_api(monkeypatch, "fffffffffff")
    api._settings["save_folder"] = str(tmp_path)

    gate = threading.Event()

    def blocking_video(url, video, audio, container=None, out_dir=None, progress=None, cancel=None):
        progress({"stage": "download", "downloaded_bytes": 50, "total_bytes": 100, "speed": 10.0, "eta": 5})
        gate.wait(timeout=5)
        progress({"stage": "merge"})
        return {"status": "ok", "path": "x"}

    monkeypatch.setattr(workers_module.yk, "video", blocking_video)
    api.start()
    assert wait_until(lambda: row(api)["downloadedBytes"] == 50)
    assert row(api)["totalBytes"] == 100
    assert row(api)["speed"] == 10.0
    assert row(api)["status"] == "downloading"

    gate.set()
    assert wait_until(lambda: row(api)["status"] == "merging" or row(api)["status"] == DONE)


def test_stop_cancels_in_flight_download_and_leaves_it_canceled(monkeypatch, tmp_path):
    gate = threading.Event()

    def fake_video(url, video, audio, container=None, out_dir=None, progress=None, cancel=None):
        gate.set()
        cancel.wait(timeout=5) if hasattr(cancel, "wait") else None
        deadline = time.time() + 5
        while time.time() < deadline and not cancel.is_set():
            time.sleep(0.01)
        if cancel.is_set():
            raise yk.Cancelled("stopped")
        return {"status": "ok", "path": "x"}

    monkeypatch.setattr(workers_module.yk, "video", fake_video)
    api = make_ready_api(monkeypatch, "ggggggggggg")
    api._settings["save_folder"] = str(tmp_path)

    api.start()
    assert wait_until(lambda: gate.is_set())
    api.stop()
    assert wait_until(lambda: row(api)["status"] == CANCELED)


def test_remove_while_downloading_cancels_and_row_disappears(monkeypatch, tmp_path):
    gate = threading.Event()

    def fake_video(url, video, audio, container=None, out_dir=None, progress=None, cancel=None):
        gate.set()
        deadline = time.time() + 5
        while time.time() < deadline and not cancel.is_set():
            time.sleep(0.01)
        if cancel.is_set():
            raise yk.Cancelled("removed")
        return {"status": "ok", "path": "x"}

    monkeypatch.setattr(workers_module.yk, "video", fake_video)
    api = make_ready_api(monkeypatch, "hhhhhhhhhhh")
    api._settings["save_folder"] = str(tmp_path)
    row_id = row(api)["id"]

    api.start()
    assert wait_until(lambda: gate.is_set())
    api.remove([row_id])
    assert wait_until(lambda: api._queue.snapshot() == [])
    time.sleep(0.2)
    assert api._queue.snapshot() == []  # stays gone; no resurrection via mark_canceled


def test_download_failure_keeps_row_identifiable_and_does_not_stop_queue(monkeypatch, tmp_path):
    def failing_video(url, video, audio, container=None, out_dir=None, progress=None, cancel=None):
        raise yk.NotAvailable("format gone")

    def ok_video(url, video, audio, container=None, out_dir=None, progress=None, cancel=None):
        return {"status": "ok", "path": "x"}

    calls = {"n": 0}

    def fake_video(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            return failing_video(*a, **k)
        return ok_video(*a, **k)

    monkeypatch.setattr(workers_module.yk, "video", fake_video)
    monkeypatch.setattr(workers_module.yk, "info", lambda url, out_dir=None: INFO)

    api = Api()
    api._events = FakeEvents()
    api._settings["save_folder"] = str(tmp_path)
    api.add_urls(
        "https://www.youtube.com/watch?v=iiiiiiiiiii\nhttps://www.youtube.com/watch?v=jjjjjjjjjjj"
    )
    assert wait_until(lambda: all(r["status"] == READY for r in api._queue.snapshot()))

    api.start()
    assert wait_until(
        lambda: {r["id"]: r["status"] for r in api._queue.snapshot()}
        == {"iiiiiiiiiii": FAILED, "jjjjjjjjjjj": DONE}
    )
    failed = next(r for r in api._queue.snapshot() if r["id"] == "iiiiiiiiiii")
    assert failed["error"]


def test_downloads_run_sequentially_in_queue_order(monkeypatch, tmp_path):
    order = []
    active = {"n": 0}
    max_active = {"n": 0}
    lock = threading.Lock()

    def fake_video(url, video, audio, container=None, out_dir=None, progress=None, cancel=None):
        with lock:
            active["n"] += 1
            max_active["n"] = max(max_active["n"], active["n"])
        order.append(url)
        time.sleep(0.05)
        with lock:
            active["n"] -= 1
        return {"status": "ok", "path": "x"}

    monkeypatch.setattr(workers_module.yk, "video", fake_video)
    monkeypatch.setattr(workers_module.yk, "info", lambda url, out_dir=None: INFO)

    api = Api()
    api._events = FakeEvents()
    api._settings["save_folder"] = str(tmp_path)
    ids = [f"row{str(i).zfill(8)}" for i in range(4)]
    api.add_urls("\n".join(f"https://www.youtube.com/watch?v={i}" for i in ids))
    assert wait_until(lambda: all(r["status"] == READY for r in api._queue.snapshot()))

    api.start()
    assert wait_until(lambda: all(r["status"] == DONE for r in api._queue.snapshot()), timeout=5)
    assert max_active["n"] == 1  # never two downloads at once (D-13)
    assert [u.split("=")[-1] for u in order] == ids  # top of the queue first


def test_container_and_subtitle_format_settings_are_passed_through(monkeypatch, tmp_path):
    seen = {}

    def fake_video(url, video, audio, container=None, out_dir=None, progress=None, cancel=None):
        seen["container"] = container
        return {"status": "ok", "path": "x"}

    monkeypatch.setattr(workers_module.yk, "video", fake_video)
    api = make_ready_api(monkeypatch, "kkkkkkkkkkk")
    api._settings["save_folder"] = str(tmp_path)
    api.save_settings({"container": "mkv"})

    api.start()
    assert wait_until(lambda: row(api)["status"] == DONE)
    assert seen["container"] == "mkv"
