"""Search logic that can be tested independently of the GUI."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from stat import ST_MTIME
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
    quick_filter_extensions: tuple[str, ...] = ()


@dataclass(frozen=True)
class SearchResult:
    path: str
    name: str
    is_dir: bool
    stat_result: os.stat_result


ProgressCallback = Callable[[int, int], None]
CancelCallback = Callable[[], bool]


def _no_cancel() -> bool:
    return False


def path_matches_filters(
    *,
    entry: os.DirEntry[str],
    pattern: str,
    use_regex: bool,
    search_type: Literal["both", "files", "folders"],
    cutoff_time: float | None,
    min_file_size: float | None,
    max_file_size: float | None,
    quick_filter_extensions: tuple[str, ...],
    compiled_regex: re.Pattern[str] | None = None,
    is_dir: bool | None = None,
    stat_result: os.stat_result | None = None,
) -> bool:
    # full_path = entry.path
    name = entry.name

    if is_dir is None:
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError:
            return False

    if use_regex:
        regex = compiled_regex if compiled_regex is not None else re.compile(pattern, re.IGNORECASE)
        match = regex.search(name) is not None
    else:
        match = pattern.lower() in name.lower()

    if (search_type == "files" and is_dir) or (search_type == "folders" and not is_dir):
        return False

    if not match:
        return False

    if quick_filter_extensions and not is_dir:
        _, extension = os.path.splitext(name)
        normalized_extension = extension.lower().lstrip(".")
        if normalized_extension not in quick_filter_extensions:
            return False

    if cutoff_time is not None:
        try:
            stat_result = stat_result or entry.stat(follow_symlinks=False)
            if stat_result[ST_MTIME] < cutoff_time:
                return False
        except OSError:
            return False

    if not is_dir and (min_file_size is not None or max_file_size is not None):
        try:
            stat_result = stat_result or entry.stat(follow_symlinks=False)
            file_size = stat_result.st_size
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
    cancel_callback = cancel_callback or _no_cancel
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

        if cancel_callback():
            return

        if options.max_depth is not None and current_depth > options.max_depth:
            return

        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if cancel_callback():
                        return

                    try:
                        is_dir = entry.is_dir(follow_symlinks=False)
                    except OSError:
                        continue

                    files_checked += 1

                    if files_checked % 100 == 0 and progress_callback is not None:
                        progress_callback(files_checked, matches_found)

                    stat_result = None
                    if cutoff_time is not None or (
                        not is_dir and (options.min_file_size is not None or options.max_file_size is not None)
                    ):
                        try:
                            stat_result = entry.stat(follow_symlinks=False)
                        except OSError:
                            stat_result = None

                    if path_matches_filters(
                        entry=entry,
                        pattern=options.pattern,
                        use_regex=options.use_regex,
                        search_type=options.search_type,
                        cutoff_time=cutoff_time,
                        min_file_size=options.min_file_size,
                        max_file_size=options.max_file_size,
                        quick_filter_extensions=options.quick_filter_extensions,
                        compiled_regex=compiled_regex,
                        is_dir=is_dir,
                        stat_result=stat_result,
                    ):
                        if stat_result is None:
                            try:
                                stat_result = entry.stat(follow_symlinks=False)
                            except OSError:
                                continue

                        matches_found += 1
                        yield SearchResult(
                            path=entry.path,
                            name=entry.name,
                            is_dir=is_dir,
                            stat_result=stat_result,
                        )

                    if is_dir:
                        yield from search_directory(entry.path, current_depth + 1)
        except OSError:
            return

    yield from search_directory(options.root_path, 0)

    if progress_callback is not None:
        progress_callback(files_checked, matches_found)
