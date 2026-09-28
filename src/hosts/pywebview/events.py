"""Python -> JS notifications, pushed through evaluate_js.

pywebview has no callback channel from Python into JS other than evaluating
a script string, so every push here calls a global hook the frontend
installs on window (src/bridge.ts).
"""

import json


class Events:
    def __init__(self, window) -> None:
        self._window = window

    def rows(self, revision: int, snapshot: list[dict]) -> None:
        # `revision` lets the frontend drop a push that was computed before
        # a later mutation but arrives after it (evaluate_js() can be slow
        # enough for concurrent pushes to reorder in flight — the fetch
        # thread and the UI thread both call into QueueManager). See
        # docs/reviews/A4.md finding #4.
        payload = json.dumps({"revision": revision, "rows": snapshot})
        self._window.evaluate_js(f"window.__ytdlOnRows && window.__ytdlOnRows({payload})")

    def notice(self, duplicates: int, invalid: int) -> None:
        payload = json.dumps({"duplicates": duplicates, "invalid": invalid})
        self._window.evaluate_js(f"window.__ytdlOnNotice && window.__ytdlOnNotice({payload})")
