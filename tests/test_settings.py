"""Phase 5 — persisted settings survive a save/reload round trip (FR-32)."""

from src.hosts.pywebview import settings as settings_module


def test_save_then_load_round_trips_changed_values(tmp_path, monkeypatch):
    settings_dir = tmp_path / ".youtube-downloader"
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", str(settings_dir))
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", str(settings_dir / "settings.json"))

    original = settings_module.load()
    assert original["container"] == settings_module.CONTAINER_AUTO  # defaults, nothing saved yet

    changed = dict(original)
    changed["container"] = "mkv"
    changed["subtitle_format"] = "vtt"
    changed["preferred_language"] = "en"
    changed["window_width"] = 1234
    changed["window_height"] = 789
    changed["theme"] = "light"
    settings_module.save(changed)

    reloaded = settings_module.load()
    assert reloaded["container"] == "mkv"
    assert reloaded["subtitle_format"] == "vtt"
    assert reloaded["preferred_language"] == "en"
    assert reloaded["window_width"] == 1234
    assert reloaded["window_height"] == 789
    assert reloaded["theme"] == "light"
    assert reloaded["save_folder"] == original["save_folder"]  # untouched key preserved


def test_load_with_missing_file_returns_defaults(tmp_path, monkeypatch):
    settings_dir = tmp_path / ".youtube-downloader-missing"
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", str(settings_dir))
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", str(settings_dir / "settings.json"))

    loaded = settings_module.load()
    assert loaded == settings_module.defaults()


def test_load_with_corrupt_file_falls_back_to_defaults(tmp_path, monkeypatch):
    settings_dir = tmp_path / ".youtube-downloader-corrupt"
    settings_dir.mkdir()
    settings_path = settings_dir / "settings.json"
    settings_path.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", str(settings_dir))
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", str(settings_path))

    loaded = settings_module.load()
    assert loaded == settings_module.defaults()


def test_api_save_settings_persists_across_new_api_instance(tmp_path, monkeypatch):
    """FR-32 end to end: Api.save_settings() -> new Api() picks up the change,
    simulating the app being closed and reopened."""
    from src.hosts.pywebview.api import Api

    settings_dir = tmp_path / ".youtube-downloader-e2e"
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", str(settings_dir))
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", str(settings_dir / "settings.json"))

    api1 = Api()
    api1.save_settings({"container": "mkv", "subtitle_format": "vtt", "preferred_language": "fr"})

    api2 = Api()  # a fresh process/window would call settings_module.load() again on start
    assert api2.get_settings()["container"] == "mkv"
    assert api2.get_settings()["subtitle_format"] == "vtt"
    assert api2.get_settings()["preferred_language"] == "fr"
