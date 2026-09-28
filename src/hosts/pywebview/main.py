import os
import sys

import webview

from src.hosts.pywebview.api import Api
from src.hosts.pywebview import settings as settings_module

def _dist_dir() -> str:
    # A PyInstaller-frozen executable has no real src/hosts/pywebview/main.py
    # on disk — __file__ resolves inside the temp extraction dir, four levels
    # up from which is meaningless. sys._MEIPASS is that extraction dir
    # itself, and youtube-downloader.spec lays dist/ directly under it to
    # match (workbench-kit's pywebview branch does the same, D-27).
    # Source-tree execution (`python -m src.hosts.pywebview.main`) is
    # untouched: sys.frozen is only ever set inside a PyInstaller bundle.
    if getattr(sys, "frozen", False):
        root_dir = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.path.join(root_dir, "dist")


DIST_DIR = _dist_dir()


def entry_url() -> str:
    index_path = os.path.join(DIST_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise FileNotFoundError(
            f"{index_path} not found. Run `npm run build` before `start:pywebview`."
        )
    return index_path


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    initial_settings = settings_module.load()

    api = Api()
    window = webview.create_window(
        "YouTube Downloader",
        entry_url(),
        js_api=api,
        width=initial_settings["window_width"],
        height=initial_settings["window_height"],
        min_size=(760, 420),
    )
    api.bind(window)

    def on_closing() -> bool:
        # FR-33: confirm before closing while a download is in progress.
        # The dialog itself is shown by the frontend; this only decides
        # whether to let the OS-level close proceed right now.
        if api.should_force_close():
            return True  # user already confirmed via the dialog
        if api.is_downloading():
            window.evaluate_js("window.__ytdlOnCloseRequest && window.__ytdlOnCloseRequest()")
            return False
        return True

    window.events.closing += on_closing
    webview.start()


if __name__ == "__main__":
    main()
