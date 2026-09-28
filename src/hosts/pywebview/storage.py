"""Save-folder default (D-14). Persistence across restarts is FR-32 (Phase 5)."""

import os


def default_save_folder() -> str:
    return os.path.join(os.path.expanduser("~"), "Downloads")
