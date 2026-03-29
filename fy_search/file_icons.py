"""File-type icon metadata for the results table."""

from __future__ import annotations

import os

FILE_ICON_MAP = {
    # Images
    "jpg": ("fa5s.file-image", "#0EA5E9"),
    "jpeg": ("fa5s.file-image", "#0EA5E9"),
    "png": ("fa5s.file-image", "#0EA5E9"),
    "gif": ("fa5s.file-image", "#0EA5E9"),
    "bmp": ("fa5s.file-image", "#0EA5E9"),
    "svg": ("fa5s.file-image", "#0EA5E9"),
    "tiff": ("fa5s.file-image", "#0EA5E9"),
    "tif": ("fa5s.file-image", "#0EA5E9"),
    "webp": ("fa5s.file-image", "#0EA5E9"),
    # Audio
    "mp3": ("fa5s.file-audio", "#10B981"),
    "aac": ("fa5s.file-audio", "#10B981"),
    "wav": ("fa5s.file-audio", "#10B981"),
    "flac": ("fa5s.file-audio", "#10B981"),
    "ogg": ("fa5s.file-audio", "#10B981"),
    "m4a": ("fa5s.file-audio", "#10B981"),
    # Video
    "mp4": ("fa5s.file-video", "#8B5CF6"),
    "mkv": ("fa5s.file-video", "#8B5CF6"),
    "avi": ("fa5s.file-video", "#8B5CF6"),
    "mov": ("fa5s.file-video", "#8B5CF6"),
    "m4v": ("fa5s.file-video", "#8B5CF6"),
    "webm": ("fa5s.file-video", "#8B5CF6"),
    # Documents
    "pdf": ("fa5s.file-pdf", "#DC2626"),
    "doc": ("fa5s.file-word", "#2563EB"),
    "docx": ("fa5s.file-word", "#2563EB"),
    "xls": ("fa5s.file-excel", "#059669"),
    "xlsx": ("fa5s.file-excel", "#059669"),
    "csv": ("fa5s.file-csv", "#059669"),
    "ppt": ("fa5s.file-powerpoint", "#EA580C"),
    "pptx": ("fa5s.file-powerpoint", "#EA580C"),
    "txt": ("fa5s.file-alt", "#64748B"),
    "md": ("msc.markdown", "#64748B"),
    # Programming
    "py": ("fa5b.python", "#356e9e"),
    "pyc": ("fa5b.python", "#356e9e"),
    "js": ("fa5b.js-square", "#efd81c"),
    "jsx": ("fa5b.js-square", "#efd81c"),
    "ts": ("fa5s.file-code", "#0076c6"),
    "json": ("fa5s.file-code", "#F59E0B"),
    "html": ("fa5s.code", "#F59E0B"),
    "css": ("fa5s.file-code", "#F59E0B"),
    "db": ("fa5s.database", "#F59E0B"),
    "java": ("msc.coffee", "#f38f1c"),
    "jar": ("msc.coffee", "#f38f1c"),
    "vue": ("fa5b.vuejs", "#3eb17e"),
    "ipynb": ("msc.notebook", "#e8712a"),
    "rs": ("fa5b.rust", "#7e3408"),
    "sqlite": ("fa5s.database", "#F59E0B"),
    "sql": ("fa5s.database", "#0075cf"),
    # Archives
    "zip": ("fa5s.file-archive", "#7C3AED"),
    "rar": ("fa5s.file-archive", "#7C3AED"),
    "7z": ("fa5s.file-archive", "#7C3AED"),
    "tar": ("fa5s.file-archive", "#7C3AED"),
    "gz": ("fa5s.file-archive", "#7C3AED"),
    "xz": ("fa5s.file-archive", "#7C3AED"),
    # Executables
    "ps1": ("msc.terminal-powershell", "#1720ca"),
    "apk": ("fa5b.android", "#25A732"),
    "bat": ("msc.terminal", "#333333"),
    "cmd": ("msc.terminal", "#333333"),
    "exe": ("mdi6.view-grid", "#B45309"),
    "msi": ("fa5s.file-medical-alt", "#B45309"),
    "sh": ("fa5s.terminal", "#334155"),
    "deb": ("fa5s.box-open", "#B45309"),
}

DEFAULT_FILE_ICON = ("fa5s.file-alt", "#64748B")
FOLDER_ICON = ("fa5s.folder", "#D97706")
TYPE_FILE_ICON = ("fa5s.file-alt", "#64748B")


def normalized_extension(name: str) -> str:
    """Return a lowercase extension without the leading dot."""

    _, extension = os.path.splitext(name)
    return extension.lower().lstrip(".")
