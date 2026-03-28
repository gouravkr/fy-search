"""Cross-platform settings storage helpers."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APP_NAME = "fy_search"
SETTINGS_FILENAME = "settings.json"
NO_QUICK_FILTER = "All"


@dataclass(frozen=True)
class QuickFilters:
    filters: dict[str, tuple[str, ...]]

    @classmethod
    def defaults(cls) -> QuickFilters:
        return cls(
            filters={
                "Images": ("jpg", "jpeg", "png", "gif", "bmp", "tiff", "svg"),
                "Audio": ("mp3", "wav", "aac", "flac", "ogg", "m4a", "opus"),
                "Videos": ("mp4", "mkv", "avi", "mov", "wmv", "flv", "webm"),
                "Documents": ("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "md", "odt"),
                "Executables": ("exe", "msi", "bat", "sh", "app", "deb", "rpm", "ps1"),
                "Archives": ("zip", "rar", "7z", "tar", "gz", "bz2", "xz"),
            }
        )

    @classmethod
    def from_dict(cls, data: Any) -> QuickFilters:
        if not isinstance(data, dict):
            return cls.defaults()

        normalized: dict[str, tuple[str, ...]] = {}
        for name, extensions in data.items():
            if not isinstance(name, str) or not name.strip():
                continue
            if not isinstance(extensions, list):
                continue

            values: list[str] = []
            for extension in extensions:
                if not isinstance(extension, str):
                    continue
                normalized_extension = extension.strip().lower().lstrip(".")
                if normalized_extension:
                    values.append(normalized_extension)

            if values:
                normalized[name.strip()] = tuple(dict.fromkeys(values))

        return cls(filters=normalized or cls.defaults().filters)

    def to_dict(self) -> dict[str, list[str]]:
        return {name: list(extensions) for name, extensions in self.filters.items()}

    def names(self) -> list[str]:
        return [NO_QUICK_FILTER, *self.filters.keys()]

    def extensions_for(self, filter_name: str) -> tuple[str, ...]:
        if filter_name == NO_QUICK_FILTER:
            return ()
        return self.filters.get(filter_name, ())


@dataclass(frozen=True)
class AppSettings:
    path: str = ""
    depth: int = 0
    full_path: bool = False
    search_type: str = "Files and Folders"
    pattern_match: str = "Name Match"
    min_file_size_unit: str = "Bytes"
    max_file_size_unit: str = "Bytes"
    size_format: str = "Human Readable"
    selected_quick_filter: str = NO_QUICK_FILTER
    quick_filters: QuickFilters = QuickFilters.defaults()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppSettings:
        path = data.get("path", "")
        depth = data.get("depth", 0)
        full_path = data.get("full_path", False)
        search_type = data.get("search_type", "Files and Folders")
        pattern_match = data.get("pattern_match", "Name Match")
        min_file_size_unit = data.get("min_file_size_unit", "Bytes")
        max_file_size_unit = data.get("max_file_size_unit", "Bytes")
        size_format = data.get("size_format", "Human Readable")
        selected_quick_filter = data.get("selected_quick_filter", NO_QUICK_FILTER)
        quick_filters = QuickFilters.from_dict(data.get("quick_filters", QuickFilters.defaults().to_dict()))

        selected_quick_filter = selected_quick_filter if isinstance(selected_quick_filter, str) else NO_QUICK_FILTER
        if selected_quick_filter != NO_QUICK_FILTER and selected_quick_filter not in quick_filters.filters:
            selected_quick_filter = NO_QUICK_FILTER

        return cls(
            path=path if isinstance(path, str) else "",
            depth=depth if isinstance(depth, int) else 0,
            full_path=full_path if isinstance(full_path, bool) else False,
            search_type=search_type if isinstance(search_type, str) else "Files and Folders",
            pattern_match=pattern_match if isinstance(pattern_match, str) else "Name Match",
            min_file_size_unit=min_file_size_unit if isinstance(min_file_size_unit, str) else "Bytes",
            max_file_size_unit=max_file_size_unit if isinstance(max_file_size_unit, str) else "Bytes",
            size_format=size_format if isinstance(size_format, str) else "Human Readable",
            selected_quick_filter=selected_quick_filter,
            quick_filters=quick_filters,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "depth": self.depth,
            "full_path": self.full_path,
            "search_type": self.search_type,
            "pattern_match": self.pattern_match,
            "min_file_size_unit": self.min_file_size_unit,
            "max_file_size_unit": self.max_file_size_unit,
            "size_format": self.size_format,
            "selected_quick_filter": self.selected_quick_filter,
            "quick_filters": self.quick_filters.to_dict(),
        }


def get_settings_path() -> Path:
    if os.name == "nt":
        base_dir = (
            os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Roaming")
        )
    elif sys.platform == "darwin":
        base_dir = str(Path.home() / "Library" / "Application Support")
    else:
        base_dir = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")

    return Path(base_dir) / APP_NAME / SETTINGS_FILENAME


def load_settings() -> AppSettings:
    settings_path = get_settings_path()
    if not settings_path.exists():
        return AppSettings()

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppSettings()

    if not isinstance(data, dict):
        return AppSettings()

    return AppSettings.from_dict(data)


def save_settings(settings: AppSettings) -> None:
    settings_path = get_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings.to_dict()), encoding="utf-8")
