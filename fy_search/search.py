"""Search logic that can be tested independently of the GUI."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Callable, Literal


@dataclass(frozen=True)
class SearchOptions:
    root_path: str
    pattern: str
    use_regex: bool
    max_depth: int | None
    days: int | None
    search_type: Literal["both", "files", "folders"]
    min_file_size: float | None
    max_file_size: float | None


ProgressCallback = Callable[[int, int], None]
CancelCallback = Callable[[], bool]


def path_matches_filters(
    *,
    full_path: str,
    name: str,
    pattern: str,
    use_regex: bool,
    search_type: Literal["both", "files", "folders"],
    cutoff_time: float | None,
    min_file_size: float | None,
    max_file_size: float | None,
    compiled_regex: re.Pattern[str] | None = None,
) -> bool:
    is_dir = os.path.isdir(full_path)

    if use_regex:
        regex = compiled_regex if compiled_regex is not None else re.compile(pattern, re.IGNORECASE)
        match = regex.search(name) is not None
    else:
        match = pattern.lower() in name.lower()

    if (search_type == "files" and is_dir) or (search_type == "folders" and not is_dir):
        return False

    if not match:
        return False

    if cutoff_time is not None:
        try:
            if os.path.getmtime(full_path) < cutoff_time:
                return False
        except OSError:
            return False

    if not is_dir and (min_file_size is not None or max_file_size is not None):
        try:
            file_size = os.stat(full_path).st_size
        except OSError:
            return False

        if min_file_size is not None and file_size < min_file_size:
            return False

        if max_file_size is not None and file_size > max_file_size:
            return False

    return True


def iter_search_results(
    options: SearchOptions,
    *,
    progress_callback: ProgressCallback | None = None,
    cancel_callback: CancelCallback | None = None,
):
    compiled_regex = None
    if options.use_regex:
        try:
            compiled_regex = re.compile(options.pattern, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"Invalid regex: {exc}") from exc

    cutoff_time = time.time() - (options.days * 86400) if options.days else None
    files_checked = 0
    matches_found = 0

    def search_directory(path: str, current_depth: int):
        nonlocal files_checked, matches_found

        if cancel_callback is not None and cancel_callback():
            return

        if options.max_depth is not None and current_depth > options.max_depth:
            return

        try:
            entries = os.listdir(path)
        except OSError:
            return

        for name in entries:
            if cancel_callback is not None and cancel_callback():
                return

            full_path = os.path.join(path, name)
            files_checked += 1

            if files_checked % 100 == 0 and progress_callback is not None:
                progress_callback(files_checked, matches_found)

            if path_matches_filters(
                full_path=full_path,
                name=name,
                pattern=options.pattern,
                use_regex=options.use_regex,
                search_type=options.search_type,
                cutoff_time=cutoff_time,
                min_file_size=options.min_file_size,
                max_file_size=options.max_file_size,
                compiled_regex=compiled_regex,
            ):
                matches_found += 1
                yield full_path

            if os.path.isdir(full_path):
                yield from search_directory(full_path, current_depth + 1)

    yield from search_directory(options.root_path, 0)

    if progress_callback is not None:
        progress_callback(files_checked, matches_found)
