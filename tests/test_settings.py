import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fy_search.settings import AppSettings, NO_QUICK_FILTER, QuickFilters, load_settings, save_settings


class AppSettingsTests(unittest.TestCase):
    def test_to_dict_preserves_json_keys(self):
        settings = AppSettings(
            path="/tmp/search",
            depth=3,
            full_path=True,
            search_type="Folders Only",
            pattern_match="Regular Expression",
            selected_quick_filter="Images",
            quick_filters=QuickFilters(filters={"Images": ("jpg", "png"), "Audio": ("mp3",)}),
            min_file_size_unit="MB",
            max_file_size_unit="GB",
            size_format="Bytes",
        )
        self.assertEqual(
            settings.to_dict(),
            {
                "path": "/tmp/search",
                "depth": 3,
                "full_path": True,
                "search_type": "Folders Only",
                "pattern_match": "Regular Expression",
                "selected_quick_filter": "Images",
                "quick_filters": {"Images": ["jpg", "png"], "Audio": ["mp3"]},
                "min_file_size_unit": "MB",
                "max_file_size_unit": "GB",
                "size_format": "Bytes",
            },
        )

    def test_missing_settings_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "settings.json"
            with patch("fy_search.settings.get_settings_path", return_value=settings_path):
                self.assertEqual(load_settings(), AppSettings())

    def test_partial_json_loads_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "settings.json"
            settings_path.write_text(json.dumps({"path": "/tmp/demo"}), encoding="utf-8")
            with patch("fy_search.settings.get_settings_path", return_value=settings_path):
                self.assertEqual(load_settings(), AppSettings(path="/tmp/demo"))

    def test_invalid_selected_quick_filter_falls_back_to_all(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "settings.json"
            settings_path.write_text(
                json.dumps(
                    {
                        "selected_quick_filter": "Missing",
                        "quick_filters": {"Images": ["jpg", "png"]},
                    }
                ),
                encoding="utf-8",
            )
            with patch("fy_search.settings.get_settings_path", return_value=settings_path):
                self.assertEqual(load_settings().selected_quick_filter, NO_QUICK_FILTER)

    def test_invalid_quick_filters_fall_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "settings.json"
            settings_path.write_text(json.dumps({"quick_filters": {"Images": "jpg"}}), encoding="utf-8")
            with patch("fy_search.settings.get_settings_path", return_value=settings_path):
                settings = load_settings()

            self.assertIn("Images", settings.quick_filters.filters)
            self.assertIn("Audio", settings.quick_filters.filters)

    def test_invalid_json_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "settings.json"
            settings_path.write_text("{invalid", encoding="utf-8")
            with patch("fy_search.settings.get_settings_path", return_value=settings_path):
                self.assertEqual(load_settings(), AppSettings())

    def test_save_settings_writes_compatible_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "settings.json"
            settings = AppSettings(
                path="/tmp/project",
                depth=5,
                full_path=True,
                search_type="Files Only",
                pattern_match="Regular Expression",
                selected_quick_filter="Images",
                quick_filters=QuickFilters(filters={"Images": ("jpg", "png"), "Code": ("py", "js")}),
                min_file_size_unit="KB",
                max_file_size_unit="GB",
                size_format="Bytes",
            )
            with patch("fy_search.settings.get_settings_path", return_value=settings_path):
                save_settings(settings)

            self.assertEqual(
                json.loads(settings_path.read_text(encoding="utf-8")),
                {
                    "path": "/tmp/project",
                    "depth": 5,
                    "full_path": True,
                    "search_type": "Files Only",
                    "pattern_match": "Regular Expression",
                    "selected_quick_filter": "Images",
                    "quick_filters": {"Images": ["jpg", "png"], "Code": ["py", "js"]},
                    "min_file_size_unit": "KB",
                    "max_file_size_unit": "GB",
                    "size_format": "Bytes",
                },
            )
