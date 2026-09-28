import os
import sys

import webview

from src.hosts.pywebview.api import Api

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

    api = Api()
    webview.create_window(
        "YouTube Downloader",
        entry_url(),
        js_api=api,
        width=1100,
        height=650,
        min_size=(760, 420),
    )
    webview.start()


if __name__ == "__main__":
    main()
