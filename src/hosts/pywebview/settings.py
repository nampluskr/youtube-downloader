"""Persisted app settings (FR-32). Applies only to new rows / next launch —
never retroactively rewrites a row already fetched (LAYOUT.md 3절)."""

import json
import os

from src.hosts.pywebview.storage import default_save_folder

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".youtube-downloader")
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "settings.json")

CONTAINER_AUTO = "auto"


def defaults() -> dict:
    return {
        "theme": "dark",
        "save_folder": default_save_folder(),
        "container": CONTAINER_AUTO,  # "auto" | "mp4" | "mkv" (D-23)
        "subtitle_format": "srt",
        "preferred_language": "ko",
        "window_width": 1100,
        "window_height": 650,
    }


def load() -> dict:
    merged = defaults()
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return merged
    for key in merged:
        if key in data:
            merged[key] = data[key]
    return merged


def save(settings: dict) -> None:
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    tmp_path = SETTINGS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, SETTINGS_PATH)
