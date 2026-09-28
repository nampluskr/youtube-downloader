"""Python -> JS notifications, pushed through evaluate_js.

pywebview has no callback channel from Python into JS other than evaluating
a script string, so every push here calls a global hook the frontend
installs on window (src/bridge.ts).
"""

import json


class Events:
    def __init__(self, window) -> None:
        self._window = window

    def rows(self, snapshot: list[dict]) -> None:
        payload = json.dumps(snapshot)
        self._window.evaluate_js(f"window.__ytdlOnRows && window.__ytdlOnRows({payload})")

    def notice(self, duplicates: int, invalid: int) -> None:
        payload = json.dumps({"duplicates": duplicates, "invalid": invalid})
        self._window.evaluate_js(f"window.__ytdlOnNotice && window.__ytdlOnNotice({payload})")
