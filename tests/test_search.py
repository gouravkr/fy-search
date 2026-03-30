import os
import tempfile
import time
import unittest
from pathlib import Path

from fy_search.search import SearchOptions, iter_search_results, path_matches_filters


class SearchTests(unittest.TestCase):
    def test_path_matches_filters_for_plain_name_match(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "report.txt"
            file_path.write_text("data", encoding="utf-8")
            with os.scandir(tmp_dir) as entries:
                entry = next(iter(entries))

            self.assertTrue(
                path_matches_filters(
                    entry=entry,
                    pattern="report",
                    use_regex=False,
                    search_type="files",
                    cutoff_time=None,
                    min_file_size=None,
                    max_file_size=None,
                    quick_filter_extensions=(),
                )
            )

    def test_path_matches_filters_respects_max_file_size(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "large.log"
            file_path.write_text("x" * 20, encoding="utf-8")
            with os.scandir(tmp_dir) as entries:
                entry = next(iter(entries))

            self.assertFalse(
                path_matches_filters(
                    entry=entry,
                    pattern="large",
                    use_regex=False,
                    search_type="files",
                    cutoff_time=None,
                    min_file_size=None,
                    max_file_size=5,
                    quick_filter_extensions=(),
                )
            )

    def test_iter_search_results_returns_matching_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")
            (tmp_path / "image.png").write_text("png", encoding="utf-8")

            options = SearchOptions(
                root_path=os.fspath(tmp_path),
                pattern=r".*\.txt$",
                use_regex=True,
                max_depth=None,
                days=None,
                search_type="files",
                min_file_size=None,
                max_file_size=None,
                quick_filter_extensions=(),
            )

            results = list(iter_search_results(options))

            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].path.endswith("notes.txt"))
            self.assertFalse(results[0].is_dir)

    def test_iter_search_results_respects_days_filter(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "old.txt"
            file_path.write_text("data", encoding="utf-8")
            old_timestamp = time.time() - (3 * 86400)
            os.utime(file_path, (old_timestamp, old_timestamp))

            options = SearchOptions(
                root_path=tmp_dir,
                pattern="old",
                use_regex=False,
                max_depth=None,
                days=1,
                search_type="files",
                min_file_size=None,
                max_file_size=None,
                quick_filter_extensions=(),
            )

            self.assertEqual(list(iter_search_results(options)), [])

    def test_iter_search_results_respects_quick_filter_extensions(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "photo.JPG").write_text("jpg", encoding="utf-8")
            (tmp_path / "notes.txt").write_text("txt", encoding="utf-8")

            options = SearchOptions(
                root_path=os.fspath(tmp_path),
                pattern="",
                use_regex=False,
                max_depth=None,
                days=None,
                search_type="files",
                min_file_size=None,
                max_file_size=None,
                quick_filter_extensions=("jpg", "png"),
            )

            results = list(iter_search_results(options))

            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].path.endswith("photo.JPG"))

    def test_iter_search_results_includes_stat_metadata_for_matches(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "notes.txt"
            file_path.write_text("notes", encoding="utf-8")

            options = SearchOptions(
                root_path=os.fspath(tmp_dir),
                pattern="notes",
                use_regex=False,
                max_depth=None,
                days=None,
                search_type="files",
                min_file_size=None,
                max_file_size=None,
                quick_filter_extensions=(),
            )

            result = next(iter(iter_search_results(options)))

            self.assertEqual(result.name, "notes.txt")
            self.assertEqual(result.stat_result.st_size, 5)
