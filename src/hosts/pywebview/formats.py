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


def _resolution_label(height, fps, precise: bool = False) -> str:
    if fps is None:
        fps_part = ""
    elif precise:
        fps_part = f"{fps:g}"
    else:
        fps_part = f"{round(fps)}"
    return f"{height}p{fps_part}"


def video_options(info: dict) -> list[dict]:
    """Selectable resolution rows (FR-7). Grouped by (height, fps); a group
    that collides on (codec, ext) at the same height/fps (D-18's "포맷이
    여러 개" case) is exploded into one row per format instead, each row's
    label carrying the extension, so the tie is never picked silently
    (FR-9's "앱이 그중 하나를 자동으로 고르지 않는다")."""
    groups: dict[tuple, list[dict]] = {}
    for f in info.get("video_formats", []):
        if f.get("height") is None:
            continue
        groups.setdefault((f["height"], f.get("fps")), []).append(f)

    rows = []
    for (height, fps), group in groups.items():
        by_codec: dict[str, list[dict]] = {}
        for f in group:
            by_codec.setdefault(codec_label(f), []).append(f)

        # Only the codec(s) that actually collide (same height/fps/codec,
        # different ext) get exploded into their own ext-suffixed rows.
        # Codecs that are unambiguous at this height/fps stay merged into one
        # "{h}p{fps}" row, letting the Codec dropdown pick among them as
        # usual — real data has (height,fps) groups spanning 3+ unrelated
        # codecs (avc1/vp9/av01) where only one of them happens to collide.
        merged = [f for f in group if len(by_codec[codec_label(f)]) == 1]
        if merged:
            rows.append(
                {
                    "key": f"{height}-{fps}",
                    "label": _resolution_label(height, fps),
                    "ext_suffix": None,
                    "height": height,
                    "fps": fps,
                    "formats": merged,
                }
            )
        for codec, fmts in by_codec.items():
            if len(fmts) == 1:
                continue
            for f in fmts:
                ext = f.get("ext", "")
                rows.append(
                    {
                        "key": f"{height}-{fps}-{ext}-{f['id']}",
                        "label": f"{_resolution_label(height, fps)} · {ext}",
                        "ext_suffix": ext,
                        "height": height,
                        "fps": fps,
                        "formats": [f],
                    }
                )

    # Two DIFFERENT (height, fps) groups can round to the same displayed fps
    # (29.97 and 30 both show "30") and end up with identical-looking labels
    # for otherwise distinct rows. Switch just the colliding ones to the
    # precise fps value so every option stays visually distinguishable
    # (docs/reviews/A4.md finding #5).
    label_counts: dict[str, int] = {}
    for r in rows:
        label_counts[r["label"]] = label_counts.get(r["label"], 0) + 1
    for r in rows:
        if label_counts[r["label"]] > 1:
            precise = _resolution_label(r["height"], r["fps"], precise=True)
            r["label"] = f"{precise} · {r['ext_suffix']}" if r["ext_suffix"] else precise

    # Last resort: two formats can still look identical after the precise-fps
    # pass (truly equal height/fps/codec/ext, or fps values so close that
    # :g rounds them the same, e.g. 29.970001 vs 29.970002 — flagged in the
    # second A4 verification pass). Nothing left in the source data can tell
    # them apart, so fall back to the one thing that always differs: the
    # format id, appended only to the still-colliding rows.
    final_counts: dict[str, int] = {}
    for r in rows:
        final_counts[r["label"]] = final_counts.get(r["label"], 0) + 1
    for r in rows:
        if final_counts[r["label"]] > 1:
            r["label"] = f"{r['label']} ({r['formats'][0]['id']})"

    for r in rows:
        del r["ext_suffix"]
    rows.sort(key=lambda r: (-(r["height"] or 0), -(r["fps"] or 0)))
    return rows


def audio_options(info: dict) -> list[dict]:
    """Selectable audio tracks (FR-10), language suffixed only when >1 language exists."""
    fmts = info.get("audio_formats", [])
    languages = {f.get("language") for f in fmts if f.get("language")}
    multi_lang = len(languages) > 1
    options = []
    for f in fmts:
        label = audio_label(f)
        if multi_lang and f.get("language"):
            label = f"{label} {f['language']}"
        options.append({"id": f["id"], "label": label, "format": f})
    return options


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


def select_fallback_audio(info: dict) -> Optional[dict]:
    """Best-by-bitrate audio track, ignoring the m4a/non-drc preference.

    Used only to repair D-17's invariant (a selected video forbids "None"
    audio) when the ideal rule (select_default_audio) finds nothing but a
    real audio track does exist — never invents one out of thin air.
    """
    candidates = info.get("audio_formats", [])
    if not candidates:
        return None
    return max(candidates, key=lambda f: f.get("abr") or 0)


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
    return [{"id": t["id"], "label": subtitle_label(t), "kind": t.get("kind"), "key": t.get("key")} for t in result]


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


def serialize_video_options(rows: list[dict]) -> list[dict]:
    return [
        {
            "key": r["key"],
            "label": r["label"],
            "codecs": [{"id": f["id"], "label": codec_label(f)} for f in r["formats"]],
        }
        for r in rows
    ]


def serialize_audio_options(options: list[dict]) -> list[dict]:
    return [{"id": o["id"], "label": o["label"]} for o in options]


def formats_for_resolution_key(rows: list[dict], key: Optional[str]) -> list[dict]:
    row = next((r for r in rows if r["key"] == key), None)
    return row["formats"] if row else []


def resolution_key_for_format_id(rows: list[dict], format_id: Optional[str]) -> Optional[str]:
    if format_id is None:
        return None
    for row in rows:
        if any(f["id"] == format_id for f in row["formats"]):
            return row["key"]
    return None


def format_by_id(fmts: list[dict], format_id: Optional[str]) -> Optional[dict]:
    if format_id is None:
        return None
    return next((f for f in fmts if f["id"] == format_id), None)


def apply_defaults(info: dict, preferred_language: str = PREFERRED_SUBTITLE_LANGUAGE) -> dict:
    """Everything a row needs right after fetch: option lists, the D-16
    default selection, and the labels/size derived from it. Phase 4's
    select_* functions (below) mutate the selection ids this returns; the
    row re-derives labels/size from them the same way each time.

    `preferred_language` is read once, at fetch time, from the settings
    current when THIS row was added — later settings changes apply only to
    rows added after them (FR-32's "새로 추가되는 행에만 적용").
    """
    v_options = video_options(info)
    a_options = audio_options(info)
    s_options = subtitle_options(info, preferred_language=preferred_language)

    video_fmt = select_default_video(info)
    audio_fmt = select_default_audio(info)
    if video_fmt is not None and audio_fmt is None:
        # D-17: a selected video forbids "None" audio. The ideal rule found
        # no m4a/non-drc track — fall back to any real track rather than
        # leaving the invariant violated (docs/reviews/A4.md finding #3).
        audio_fmt = select_fallback_audio(info)

    video_format_id = video_fmt["id"] if video_fmt else None
    audio_format_id = audio_fmt["id"] if audio_fmt else None
    resolution_key = resolution_key_for_format_id(v_options, video_format_id)
    size = total_size(video_fmt, audio_fmt)

    return {
        "video_options": v_options,
        "audio_options": a_options,
        "subtitle_options": s_options,
        "resolution_key": resolution_key,
        "video_format_id": video_format_id,
        "audio_format_id": audio_format_id,
        "subtitle_track_id": None,
        "resolution_label": video_label(video_fmt),
        "codec_label": codec_label(video_fmt),
        "audio_label": audio_label(audio_fmt),
        "subtitle_label": subtitle_label(None),
        "size_bytes": size,
        "size_label": size_label(size),
    }


def relabel(info: dict, video_format_id, audio_format_id, subtitle_track_id) -> dict:
    """Recomputes the display labels/size for a (possibly user-changed) selection."""
    video_fmt = format_by_id(info.get("video_formats", []), video_format_id)
    audio_fmt = format_by_id(info.get("audio_formats", []), audio_format_id)
    tracks = info.get("subtitles", [])
    subtitle_track = next((t for t in tracks if t["id"] == subtitle_track_id), None) if subtitle_track_id else None
    size = total_size(video_fmt, audio_fmt)
    return {
        "resolution_label": video_label(video_fmt),
        "codec_label": codec_label(video_fmt),
        "audio_label": audio_label(audio_fmt),
        "subtitle_label": subtitle_label(subtitle_track),
        "size_bytes": size,
        "size_label": size_label(size),
    }
