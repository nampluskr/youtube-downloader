"""Phase 4 — per-row format selection and queue reordering."""

import time

from src.hosts.pywebview import workers as workers_module
from src.hosts.pywebview.api import Api
from src.hosts.pywebview.queue import READY


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
        {"id": "v1080-30", "ext": "mp4", "vcodec": "avc1.640028", "height": 1080, "fps": 30, "size": 500},
        {"id": "v1080-vp9", "ext": "webm", "vcodec": "vp09.00", "height": 1080, "fps": 60, "size": 700},
        {"id": "v720-60", "ext": "mp4", "vcodec": "avc1.4d4015", "height": 720, "fps": 60, "size": 400},
        {"id": "v1080-dup-mp4", "ext": "mp4", "vcodec": "avc1.4d4015", "height": 1080, "fps": 24, "size": 300},
        {"id": "v1080-dup-webm", "ext": "webm", "vcodec": "avc1.4d4015", "height": 1080, "fps": 24, "size": None},
    ],
    "audio_formats": [
        {"id": "a-m4a-129", "ext": "m4a", "abr": 129.0, "drc": False, "original": None, "size": 100, "language": "en"},
        {"id": "a-m4a-drc", "ext": "m4a", "abr": 129.0, "drc": True, "original": None, "size": 100, "language": "en"},
        {"id": "a-webm", "ext": "webm", "abr": 160.0, "drc": False, "original": None, "size": 120, "language": "en"},
    ],
    "subtitles": [
        {"id": "manual:en", "kind": "manual", "key": "en", "name": "English"},
        {"id": "auto:en", "kind": "auto", "key": "en", "name": "English"},
        {"id": "auto:ko", "kind": "auto", "key": "ko", "name": "Korean"},
        {"id": "auto:fr", "kind": "auto", "key": "fr", "name": "French"},
    ],
}


def make_ready_api(monkeypatch, video_id, info=None):
    monkeypatch.setattr(workers_module.yk, "info", lambda url, out_dir=None: info or INFO)
    api = Api()
    api._events = FakeEvents()
    api.add_urls(f"https://www.youtube.com/watch?v={video_id}")
    deadline = time.time() + 5
    while time.time() < deadline:
        row = api._queue.snapshot()[0]
        if row["status"] == READY:
            return api
        time.sleep(0.02)
    raise AssertionError("row never became ready")


def row(api):
    return api._queue.snapshot()[0]


def test_default_selection_on_fetch_matches_d16(monkeypatch):
    api = make_ready_api(monkeypatch, "aaaaaaaaaaa")
    r = row(api)
    assert r["resolution"] == "1080p60"
    assert r["codec"] == "avc1"
    assert r["selectedVideoFormatId"] == "v1080-60"
    assert r["audio"] == "m4a 129k"
    assert r["subtitle"] == "None"
    assert r["size"] == "0 MB"  # 900 + 100 bytes, rounds to 0 MB — still a real total, not "-"


def test_ambiguous_same_res_fps_codec_shown_as_separate_resolution_options(monkeypatch):
    api = make_ready_api(monkeypatch, "bbbbbbbbbbb")
    r = row(api)
    labels = {o["label"] for o in r["videoOptions"]}
    assert "1080p24 · mp4" in labels
    assert "1080p24 · webm" in labels
    assert "1080p24" not in labels  # never collapsed into one unlabeled tie


def test_changing_resolution_updates_codec_and_size(monkeypatch):
    api = make_ready_api(monkeypatch, "ccccccccccc")
    row_id = row(api)["id"]
    api.select(row_id, "resolution", "720-60")
    r = row(api)
    assert r["resolution"] == "720p60"
    assert r["codec"] == "avc1"
    assert r["selectedVideoFormatId"] == "v720-60"
    assert r["size"] == "0 MB"


def test_codec_change_restricted_to_current_resolution(monkeypatch):
    api = make_ready_api(monkeypatch, "ddddddddddd")
    row_id = row(api)["id"]
    api.select(row_id, "resolution", "1080-60")
    # v720-60 is not a codec option at 1080p60 — must be ignored (NFR-6)
    api.select(row_id, "codec", "v720-60")
    assert row(api)["selectedVideoFormatId"] == "v1080-60"

    api.select(row_id, "codec", "v1080-vp9")
    r = row(api)
    assert r["selectedVideoFormatId"] == "v1080-vp9"
    assert r["codec"] == "vp09"


def test_audio_none_forbidden_while_video_selected(monkeypatch):
    api = make_ready_api(monkeypatch, "eeeeeeeeeee")
    row_id = row(api)["id"]
    api.select(row_id, "audio", None)
    assert row(api)["selectedAudioFormatId"] == "a-m4a-129"  # ignored, D-17


def test_video_none_then_audio_none_allows_subtitle_only(monkeypatch):
    api = make_ready_api(monkeypatch, "fffffffffff")
    row_id = row(api)["id"]
    api.select(row_id, "resolution", None)
    assert row(api)["selectedVideoFormatId"] is None
    api.select(row_id, "audio", None)
    r = row(api)
    assert r["selectedAudioFormatId"] is None
    assert r["audio"] == ""


def test_reselecting_video_restores_a_real_audio_default(monkeypatch):
    api = make_ready_api(monkeypatch, "ggggggggggg")
    row_id = row(api)["id"]
    api.select(row_id, "resolution", None)
    api.select(row_id, "audio", None)
    api.select(row_id, "resolution", "1080-60")
    r = row(api)
    assert r["selectedVideoFormatId"] == "v1080-60"
    assert r["selectedAudioFormatId"] == "a-m4a-129"  # D-17 invariant restored


def test_subtitle_selection_and_none(monkeypatch):
    api = make_ready_api(monkeypatch, "hhhhhhhhhhh")
    row_id = row(api)["id"]
    ids = {o["id"] for o in row(api)["subtitleOptions"]}
    assert ids == {"manual:en", "auto:en", "auto:ko"}

    api.select(row_id, "subtitle", "auto:ko")
    assert row(api)["subtitle"] == "ko (auto)"
    api.select(row_id, "subtitle", None)
    assert row(api)["subtitle"] == "None"

    api.select(row_id, "subtitle", "auto:fr")  # not offered — ignored
    assert row(api)["subtitle"] == "None"


def test_rows_keep_independent_selections(monkeypatch):
    monkeypatch.setattr(workers_module.yk, "info", lambda url, out_dir=None: INFO)
    api = Api()
    api._events = FakeEvents()
    api.add_urls("https://www.youtube.com/watch?v=iiiiiiiiiii\nhttps://www.youtube.com/watch?v=jjjjjjjjjjj")

    deadline = time.time() + 5
    while time.time() < deadline:
        rows = api._queue.snapshot()
        if all(r["status"] == READY for r in rows):
            break
        time.sleep(0.02)

    ids = [r["id"] for r in api._queue.snapshot()]
    api.select(ids[0], "resolution", "720-60")
    api.select(ids[1], "codec", "v1080-vp9")

    rows = {r["id"]: r for r in api._queue.snapshot()}
    assert rows[ids[0]]["resolution"] == "720p60"
    assert rows[ids[1]]["resolution"] == "1080p60"
    assert rows[ids[1]]["codec"] == "vp09"


def test_move_up_and_down_changes_queue_order(monkeypatch):
    monkeypatch.setattr(workers_module.yk, "info", lambda url, out_dir=None: {"title": "T"})
    api = Api()
    api._events = FakeEvents()
    api.add_urls(
        "\n".join(
            f"https://www.youtube.com/watch?v=row{str(i).zfill(8)}" for i in range(4)
        )
    )
    ids = [r["id"] for r in api._queue.snapshot()]
    assert ids == ["row00000000", "row00000001", "row00000002", "row00000003"]

    api.move(ids[2], -1)  # move index 2 up
    ids_after_up = [r["id"] for r in api._queue.snapshot()]
    assert ids_after_up == ["row00000000", "row00000002", "row00000001", "row00000003"]

    api.move(ids[0], -1)  # already at top — no-op
    assert [r["id"] for r in api._queue.snapshot()] == ids_after_up

    api.move(ids[3], 1)  # already at bottom — no-op
    assert [r["id"] for r in api._queue.snapshot()] == ids_after_up

    api.move("row00000002", 1)
    assert [r["id"] for r in api._queue.snapshot()] == [
        "row00000000",
        "row00000001",
        "row00000002",
        "row00000003",
    ]
