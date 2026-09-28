"""Turns a youtube-kit info() result into what a queue row shows.

Phase 3 only needs the DEFAULT selection (D-16) and the values it derives
(labels, total size, D-19). Phase 4 adds the per-row dropdowns that let the
user change these same selections; it reuses this module rather than
duplicating the rule.

Never invents a value info() did not provide (NFR-6): a slot with no match
stays None/blank rather than falling back to some other format.
"""

from typing import Optional

PREFERRED_SUBTITLE_LANGUAGE = "ko"
MAX_DEFAULT_HEIGHT = 1080


def select_default_video(info: dict) -> Optional[dict]:
    candidates = [
        f
        for f in info.get("video_formats", [])
        if (f.get("vcodec") or "").startswith("avc1")
        and f.get("height")
        and f["height"] <= MAX_DEFAULT_HEIGHT
    ]
    if not candidates:
        return None
    max_height = max(f["height"] for f in candidates)
    at_height = [f for f in candidates if f["height"] == max_height]
    max_fps = max((f.get("fps") or 0) for f in at_height)
    at_fps = [f for f in at_height if (f.get("fps") or 0) == max_fps]
    at_fps.sort(key=lambda f: f["id"])
    return at_fps[0]


def select_default_audio(info: dict) -> Optional[dict]:
    candidates = [f for f in info.get("audio_formats", []) if not f.get("drc") and f.get("ext") == "m4a"]
    if not candidates:
        return None
    flagged_original = [f for f in candidates if f.get("original")]
    pool = flagged_original if flagged_original else candidates
    return max(pool, key=lambda f: f.get("abr") or 0)


def select_default_subtitle(_info: dict) -> Optional[dict]:
    return None  # D-16: default subtitle selection is None.


def subtitle_options(info: dict, preferred_language: str = PREFERRED_SUBTITLE_LANGUAGE) -> list[dict]:
    """Manual tracks + native-language auto tracks + preferred-language auto-translated (D-20)."""
    tracks = info.get("subtitles", [])
    manual = [t for t in tracks if t.get("kind") == "manual"]
    native_lang = (info.get("language") or "").lower()
    result = list(manual)
    for t in tracks:
        if t.get("kind") != "auto":
            continue
        key = (t.get("key") or "").lower()
        if native_lang and key == native_lang:
            result.append(t)
        elif key == preferred_language.lower():
            result.append(t)
    return result


def video_label(fmt: Optional[dict]) -> str:
    if not fmt:
        return ""
    fps = fmt.get("fps")
    fps_label = f"{round(fps)}" if fps else ""
    return f"{fmt['height']}p{fps_label}"


def codec_label(fmt: Optional[dict]) -> str:
    if not fmt:
        return ""
    vcodec = fmt.get("vcodec") or ""
    return vcodec.split(".")[0]


def audio_label(fmt: Optional[dict]) -> str:
    if not fmt:
        return ""
    abr = fmt.get("abr")
    abr_label = f" {round(abr)}k" if abr else ""
    return f"{fmt.get('ext', '')}{abr_label}"


def subtitle_label(track: Optional[dict]) -> str:
    if not track:
        return "None"
    if track.get("kind") == "manual":
        return track.get("key", "")
    return f"{track.get('key', '')} (auto)"


def total_size(video_fmt: Optional[dict], audio_fmt: Optional[dict]) -> Optional[int]:
    parts = []
    for fmt in (video_fmt, audio_fmt):
        if fmt is None:
            continue
        size = fmt.get("size")
        if size is None:
            return None
        parts.append(size)
    if not parts:
        return None
    return sum(parts)


def size_label(size_bytes: Optional[int]) -> str:
    if size_bytes is None:
        return "-"
    mb = size_bytes / (1024 * 1024)
    return f"{mb:.0f} MB"


def apply_defaults(info: dict) -> dict:
    """Everything a row needs to show, derived once right after fetch (D-16)."""
    video_fmt = select_default_video(info)
    audio_fmt = select_default_audio(info)
    subtitle_track = select_default_subtitle(info)
    size = total_size(video_fmt, audio_fmt)
    return {
        "video_format_id": video_fmt["id"] if video_fmt else None,
        "audio_format_id": audio_fmt["id"] if audio_fmt else None,
        "subtitle_track_id": subtitle_track["id"] if subtitle_track else None,
        "resolution_label": video_label(video_fmt),
        "codec_label": codec_label(video_fmt),
        "audio_label": audio_label(audio_fmt),
        "subtitle_label": subtitle_label(subtitle_track),
        "size_bytes": size,
        "size_label": size_label(size),
    }
