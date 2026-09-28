"""Phase 3 — default selection rule and display labels (formats.py, D-16)."""

import json
import os

from src.hosts.pywebview import formats

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


def test_default_video_picks_highest_height_then_highest_fps_avc1_at_or_under_1080p():
    info = {
        "video_formats": [
            {"id": "v2160", "vcodec": "avc1.high", "height": 2160, "fps": 30},
            {"id": "v1080-30", "vcodec": "avc1.4d4015", "height": 1080, "fps": 30},
            {"id": "v1080-60", "vcodec": "avc1.4d4015", "height": 1080, "fps": 60},
            {"id": "v720", "vcodec": "avc1.4d4015", "height": 720, "fps": 60},
            {"id": "v1080-vp9", "vcodec": "vp09.00", "height": 1080, "fps": 60},
        ]
    }
    picked = formats.select_default_video(info)
    assert picked["id"] == "v1080-60"  # <=1080p, highest height, then highest fps
    assert formats.video_label(picked) == "1080p60"
    assert formats.codec_label(picked) == "avc1"


def test_default_video_is_none_when_no_avc1_under_1080p():
    info = {
        "video_formats": [
            {"id": "v1080-vp9", "vcodec": "vp09.00", "height": 1080, "fps": 60},
            {"id": "v4k-avc1", "vcodec": "avc1.high", "height": 2160, "fps": 30},
        ]
    }
    assert formats.select_default_video(info) is None  # NFR-6: blank, not substituted


def test_same_resolution_fps_codec_multiple_ext_is_resolved_deterministically():
    info = {
        "video_formats": [
            {"id": "137", "ext": "mp4", "vcodec": "avc1.640028", "height": 1080, "fps": 30},
            {"id": "299", "ext": "mp4", "vcodec": "avc1.640028", "height": 1080, "fps": 30},
        ]
    }
    picked = formats.select_default_video(info)
    assert picked["id"] == "137"  # lowest id wins the tie, not a random pick


def test_default_audio_prefers_non_drc_m4a_highest_bitrate():
    info = {
        "audio_formats": [
            {"id": "139-drc", "ext": "m4a", "abr": 48.9, "drc": True, "original": None},
            {"id": "139", "ext": "m4a", "abr": 48.9, "drc": False, "original": None},
            {"id": "140", "ext": "m4a", "abr": 129.3, "drc": False, "original": None},
            {"id": "251", "ext": "webm", "abr": 160.0, "drc": False, "original": None},
        ]
    }
    picked = formats.select_default_audio(info)
    assert picked["id"] == "140"
    assert formats.audio_label(picked) == "m4a 129k"


def test_default_audio_prefers_flagged_original_track_when_present():
    info = {
        "audio_formats": [
            {"id": "dub", "ext": "m4a", "abr": 200.0, "drc": False, "original": None},
            {"id": "orig", "ext": "m4a", "abr": 129.3, "drc": False, "original": True},
        ]
    }
    picked = formats.select_default_audio(info)
    assert picked["id"] == "orig"


def test_default_subtitle_is_always_none():
    assert formats.select_default_subtitle({"subtitles": [{"id": "manual:en"}]}) is None


def test_subtitle_options_keep_manual_native_auto_and_preferred_language_auto():
    info = {
        "language": "en",
        "subtitles": [
            {"id": "manual:en", "kind": "manual", "key": "en"},
            {"id": "auto:en", "kind": "auto", "key": "en"},  # native auto
            {"id": "auto:ko", "kind": "auto", "key": "ko"},  # preferred-language translation
            {"id": "auto:fr", "kind": "auto", "key": "fr"},  # should be filtered out
        ],
    }
    ids = {t["id"] for t in formats.subtitle_options(info, preferred_language="ko")}
    assert ids == {"manual:en", "auto:en", "auto:ko"}


def test_total_size_is_none_if_either_selected_format_size_is_unknown():
    known = {"size": 1000}
    unknown = {"size": None}
    assert formats.total_size(known, known) == 2000
    assert formats.total_size(known, unknown) is None
    assert formats.total_size(None, known) == 1000
    assert formats.total_size(None, None) is None


def test_size_label_formats_or_dashes():
    assert formats.size_label(None) == "-"
    assert formats.size_label(5 * 1024 * 1024) == "5 MB"


def test_apply_defaults_on_real_fixture_never_fabricates_unknown_size():
    info = load_fixture("JyEsEcsCqzM.meta.json")
    result = formats.apply_defaults(info)
    # This fixture's avc1 formats at height 144/240 have size=None in several
    # entries; whichever one wins the default rule, an unknown size must
    # surface as "-", never a guessed number.
    if result["size_bytes"] is None:
        assert result["size_label"] == "-"
    else:
        assert result["size_bytes"] > 0
