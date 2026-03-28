"""Cross-platform settings storage helpers."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

APP_NAME = "fy_search"
SETTINGS_FILENAME = "settings.json"


def get_settings_path() -> Path:
    if os.name == "nt":
        base_dir = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base_dir = str(Path.home() / "Library" / "Application Support")
    else:
        base_dir = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")

    return Path(base_dir) / APP_NAME / SETTINGS_FILENAME


def load_settings() -> dict[str, Any]:
    settings_path = get_settings_path()
    if not settings_path.exists():
        return {}

    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(data: dict[str, Any]) -> None:
    settings_path = get_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(data), encoding="utf-8")
