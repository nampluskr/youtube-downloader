import os
import sys

import webview

from src.hosts.pywebview.api import Api
from src.hosts.pywebview import settings as settings_module

DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "dist")


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
