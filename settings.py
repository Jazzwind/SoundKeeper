"""Validated, per-user SoundKeeper preferences (no audio or UI dependencies)."""

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

WAIT_OPTIONS = (30, 55, 295, 595, 895)
DURATION_OPTIONS = (0.01, 0.1, 1.0)
LANGUAGE_NAMES = {
    "en": "English",
    "zh-Hans": "简体中文",
    "fr": "Français",
    "ru": "Русский",
    "es": "Español",
    "ar": "العربية",
}


@dataclass(frozen=True)
class Settings:
    version: int = 1
    wait_seconds: int = 55
    duration_seconds: float = 1.0
    language: str = "auto"


def config_path():
    """Keep preferences independent of the executable's location."""
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base / "SoundKeeper" / "config.json"


def load_settings(path):
    """Use defaults for missing, damaged, unsupported, or invalid settings."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    if not isinstance(data, dict) or type(data.get("version", 1)) is not int:
        return Settings()
    if data.get("version", 1) != 1:
        return Settings()

    defaults = Settings()
    wait = data.get("wait_seconds")
    duration = data.get("duration_seconds")
    language = data.get("language")
    return Settings(
        wait_seconds=wait
        if type(wait) is int and wait in WAIT_OPTIONS
        else defaults.wait_seconds,
        duration_seconds=(
            float(duration)
            if type(duration) in (int, float) and duration in DURATION_OPTIONS
            else defaults.duration_seconds
        ),
        language=(
            language
            if isinstance(language, str) and language in ("auto", *LANGUAGE_NAMES)
            else defaults.language
        ),
    )


def save_settings(path, settings):
    """Replace the file atomically; never leave a partially written JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(asdict(settings), stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
