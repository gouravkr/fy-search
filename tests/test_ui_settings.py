import unittest
from unittest.mock import patch
import os
import tempfile

from PySide6.QtCore import QDir, QEvent, QModelIndex, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from fy_search.settings import AppSettings, NO_QUICK_FILTER, QuickFilters
from fy_search.ui import DirectoryPathCompleter, FileSearchGUI, RenameDelegate, RenameLineEdit, ResultRow, SearchResultModel


class GuiSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_load_settings_populates_widgets(self):
        with patch(
            "fy_search.ui.load_settings",
            return_value=AppSettings(
                path="/tmp/demo",
                depth=7,
                full_path=True,
                search_type="Folders Only",
                pattern_match="Regular Expression",
                selected_quick_filter="Images",
                quick_filters=QuickFilters(filters={"Images": ("jpg", "png"), "Audio": ("mp3",)}),
                min_file_size_unit="MB",
                max_file_size_unit="GB",
                size_format="Bytes",
            ),
        ):
            window = FileSearchGUI()

        self.assertEqual(window.path_input.text(), "/tmp/demo")
        self.assertEqual(window.depth_spin.value(), 7)
        self.assertTrue(window.show_full_path_action.isChecked())
        self.assertEqual(window.search_type_combo.currentText(), "Folders Only")
        self.assertEqual(window.pattern_type_combo.currentText(), "Regular Expression")
        self.assertEqual(window.quick_filter_combo.currentText(), "Images")
        self.assertEqual(window.min_size_unit.currentText(), "MB")
        self.assertEqual(window.max_size_unit.currentText(), "GB")
        self.assertEqual(window.current_size_format(), "Bytes")
        self.assertEqual(window.quick_filter_combo.count(), 3)
        window.close()

    def test_save_settings_builds_app_settings_from_widgets(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        with patch("fy_search.ui.save_settings"):
            window.path_input.setText("/tmp/project")
            window.depth_spin.setValue(4)
            window.show_full_path_action.setChecked(True)
            window.search_type_combo.setCurrentText("Files Only")
            window.pattern_type_combo.setCurrentText("Regular Expression")
            window.quick_filter_combo.setCurrentText("Images")
            window.min_size_unit.setCurrentText("KB")
            window.max_size_unit.setCurrentText("GB")
            window.apply_size_format_setting("Bytes")

        with patch("fy_search.ui.save_settings") as save_mock:
            window.save_settings()

        save_mock.assert_called_once_with(
            AppSettings(
                path="/tmp/project",
                depth=4,
                full_path=True,
                search_type="Files Only",
                pattern_match="Regular Expression",
                selected_quick_filter="Images",
                quick_filters=QuickFilters.defaults(),
                min_file_size_unit="KB",
                max_file_size_unit="GB",
                size_format="Bytes",
            )
        )
        window.close()

    def test_quick_filter_dropdown_uses_settings_defined_filters(self):
        settings = AppSettings(
            quick_filters=QuickFilters(filters={"Pictures": ("jpg", "png"), "Music": ("mp3",)}),
            selected_quick_filter=NO_QUICK_FILTER,
        )
        with patch("fy_search.ui.load_settings", return_value=settings):
            window = FileSearchGUI()

        items = [window.quick_filter_combo.itemText(index) for index in range(window.quick_filter_combo.count())]
        self.assertEqual(items, [NO_QUICK_FILTER, "Pictures", "Music"])
        window.close()

    def test_show_full_path_updates_model_in_real_time(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        window.model.root_path = "/tmp"
        window.model._results = [
            ResultRow("demo.txt", "/tmp/sub/demo.txt", False, 10, 100.0, 100.0),
        ]

        index = window.model.index(0, 2)
        self.assertEqual(window.model.data(index, Qt.ItemDataRole.DisplayRole), "sub")

        with patch("fy_search.ui.save_settings"):
            window.show_full_path_action.setChecked(True)
        self.assertEqual(window.model.data(index, Qt.ItemDataRole.DisplayRole), "/tmp/sub")
        window.close()

    def test_size_format_updates_model_in_real_time(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        window.model._results = [
            ResultRow("demo.txt", "/tmp/demo.txt", False, 1536, 100.0, 100.0),
        ]

        index = window.model.index(0, 4)
        self.assertEqual(window.model.data(index, Qt.ItemDataRole.DisplayRole), "1.50 KB")

        with patch("fy_search.ui.save_settings"):
            window.apply_size_format_setting("Bytes")
        self.assertEqual(window.model.data(index, Qt.ItemDataRole.DisplayRole), "1,536 B")
        window.close()

    def test_menu_bar_has_file_options_and_help_menus(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        menu_titles = [action.text() for action in window.menuBar().actions()]
        self.assertEqual(menu_titles, ["File", "Options", "Help"])
        window.close()

    def test_options_menu_reflects_settings_state(self):
        with patch(
            "fy_search.ui.load_settings",
            return_value=AppSettings(full_path=True, size_format="Bytes"),
        ):
            window = FileSearchGUI()

        self.assertTrue(window.show_full_path_action.isChecked())
        self.assertEqual(window.current_size_format(), "Bytes")
        window.close()

    def test_context_menu_has_polished_stylesheet(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        menu = window._create_context_menu()
        stylesheet = menu.styleSheet()

        self.assertIn("border-radius:", stylesheet)
        self.assertIn("QMenu::item:selected", stylesheet)
        self.assertIn("QMenu::separator", stylesheet)
        window.close()

    def test_results_table_uses_alternating_row_colors(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        self.assertTrue(window.view.alternatingRowColors())
        self.assertFalse(window.view.showGrid())
        window.close()

    def test_search_path_input_has_directory_completer(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        completer = window.path_input.completer()
        self.assertIsNotNone(completer)
        self.assertIsInstance(completer, DirectoryPathCompleter)
        self.assertEqual(completer.completionMode(), completer.CompletionMode.PopupCompletion)
        self.assertTrue(completer.model().filter() & QDir.Filter.AllDirs)
        self.assertTrue(completer.model().filter() & QDir.Filter.Drives)
        window.close()

    def test_search_path_input_has_folder_icon_action(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        actions = window.path_input.actions()
        self.assertEqual(len(actions), 1)
        self.assertFalse(actions[0].icon().isNull())
        self.assertFalse(window.browse_btn.icon().isNull())
        window.close()

    def test_search_input_has_search_icon_action(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        actions = window.pattern_input.actions()
        self.assertEqual(len(actions), 1)
        self.assertFalse(actions[0].icon().isNull())
        window.close()

    def test_search_input_has_focus_when_window_shows(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        window.show()
        self.app.processEvents()

        self.assertIs(window.focusWidget(), window.pattern_input)
        window.close()

    def test_quick_filter_defaults_to_everything(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        self.assertEqual(window.quick_filter_combo.itemText(0), NO_QUICK_FILTER)
        self.assertEqual(window.quick_filter_combo.currentText(), NO_QUICK_FILTER)
        window.close()

    def test_directory_path_completer_returns_full_directory_path(self):
        completer = DirectoryPathCompleter()
        root_index = completer.model().setRootPath(QDir.rootPath())
        child_index = completer.model().index(QDir.rootPath())

        self.assertTrue(root_index.isValid())
        self.assertTrue(child_index.isValid())
        self.assertTrue(completer.pathFromIndex(child_index))

    def test_directory_path_completer_split_path_does_not_error(self):
        completer = DirectoryPathCompleter()
        parts = completer.splitPath(QDir.homePath())
        self.assertTrue(parts)

    def test_escape_shortcut_cancels_running_search(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        class DummyWorker:
            def __init__(self):
                self.cancel_requested = False

            def request_cancel(self):
                self.cancel_requested = True

        window.worker = DummyWorker()
        window.cancel_btn.setEnabled(True)
        window.cancel_search_shortcut.activated.emit()

        self.assertTrue(window.worker.cancel_requested)
        self.assertEqual(window.status_label.text(), "Cancelling search...")
        self.assertEqual(window.cancel_search_shortcut.context(), Qt.ShortcutContext.WindowShortcut)
        window.close()

    def test_enter_on_browse_button_triggers_browse(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        with patch.object(window, "browse_path") as browse_mock:
            window.browse_btn.clicked.disconnect()
            window.browse_btn.clicked.connect(window.browse_path)
            handled = window.eventFilter(window.browse_btn, key_event)

        self.assertTrue(handled)
        browse_mock.assert_called_once_with()
        window.close()

    def test_rename_is_only_available_for_name_column(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "demo.txt")
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write("data")

            window.model.add_result(file_path)
            name_index = window.proxy_model.index(0, 0)
            path_index = window.proxy_model.index(0, 2)

            self.assertTrue(window.can_rename_index(name_index))
            self.assertFalse(window.can_rename_index(path_index))
            self.assertFalse(window.can_rename_index(QModelIndex()))

        window.close()

    def test_model_set_data_renames_file(self):
        model = SearchResultModel()
        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = os.path.join(tmp_dir, "old.txt")
            renamed_path = os.path.join(tmp_dir, "new.txt")
            with open(original_path, "w", encoding="utf-8") as handle:
                handle.write("data")

            model.add_result(original_path)
            index = model.index(0, 0)

            self.assertTrue(model.setData(index, "new.txt"))
            self.assertTrue(os.path.exists(renamed_path))
            self.assertEqual(model.data(index, Qt.ItemDataRole.DisplayRole), "new.txt")
            self.assertEqual(model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole), "txt")

    def test_extension_column_uses_compact_header_and_value(self):
        model = SearchResultModel()
        model._results = [
            ResultRow("demo.txt", "/tmp/demo.txt", False, 100, 100.0, 100.0),
            ResultRow("projects", "/tmp/projects", True, 0, 100.0, 100.0),
        ]

        self.assertEqual(model.headerData(1, Qt.Orientation.Horizontal), "Ext.")
        self.assertEqual(model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole), "txt")
        self.assertEqual(model.data(model.index(1, 1), Qt.ItemDataRole.DisplayRole), "")

    def test_type_column_returns_icon_and_text(self):
        model = SearchResultModel()
        model._results = [
            ResultRow("demo.txt", "/tmp/demo.txt", False, 100, 100.0, 100.0),
            ResultRow("demo", "/tmp/demo", True, 0, 100.0, 100.0),
        ]

        file_index = model.index(0, 3)
        folder_index = model.index(1, 3)

        self.assertEqual(model.data(file_index, Qt.ItemDataRole.DisplayRole), "File")
        self.assertEqual(model.data(folder_index, Qt.ItemDataRole.DisplayRole), "Folder")
        self.assertFalse(model.data(file_index, Qt.ItemDataRole.DecorationRole).isNull())
        self.assertFalse(model.data(folder_index, Qt.ItemDataRole.DecorationRole).isNull())

    def test_name_column_returns_cached_icons_for_known_and_unknown_extensions(self):
        model = SearchResultModel()
        model._results = [
            ResultRow("photo.jpg", "/tmp/photo.jpg", False, 100, 100.0, 100.0),
            ResultRow("archive.unknownext", "/tmp/archive.unknownext", False, 100, 100.0, 100.0),
            ResultRow("projects", "/tmp/projects", True, 0, 100.0, 100.0),
        ]

        image_index = model.index(0, 0)
        unknown_index = model.index(1, 0)
        folder_index = model.index(2, 0)

        self.assertEqual(model.data(image_index, Qt.ItemDataRole.DisplayRole), "photo.jpg")
        self.assertEqual(model.data(unknown_index, Qt.ItemDataRole.DisplayRole), "archive.unknownext")
        self.assertEqual(model.data(folder_index, Qt.ItemDataRole.DisplayRole), "projects")
        self.assertFalse(model.data(image_index, Qt.ItemDataRole.DecorationRole).isNull())
        self.assertFalse(model.data(unknown_index, Qt.ItemDataRole.DecorationRole).isNull())
        self.assertFalse(model.data(folder_index, Qt.ItemDataRole.DecorationRole).isNull())

    def test_rename_delegate_does_not_commit_without_enter(self):
        model = SearchResultModel()
        delegate = RenameDelegate()
        editor = RenameLineEdit()
        editor.setText("new.txt")

        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = os.path.join(tmp_dir, "old.txt")
            with open(original_path, "w", encoding="utf-8") as handle:
                handle.write("data")

            model.add_result(original_path)
            index = model.index(0, 0)
            delegate.setModelData(editor, model, index)

            self.assertTrue(os.path.exists(original_path))
            self.assertFalse(os.path.exists(os.path.join(tmp_dir, "new.txt")))

    def test_rename_delegate_commits_after_enter(self):
        model = SearchResultModel()
        delegate = RenameDelegate()
        editor = RenameLineEdit()
        editor.setText("new.txt")
        editor.rename_committed = True

        with tempfile.TemporaryDirectory() as tmp_dir:
            original_path = os.path.join(tmp_dir, "old.txt")
            renamed_path = os.path.join(tmp_dir, "new.txt")
            with open(original_path, "w", encoding="utf-8") as handle:
                handle.write("data")

            model.add_result(original_path)
            index = model.index(0, 0)
            delegate.setModelData(editor, model, index)

            self.assertFalse(os.path.exists(original_path))
            self.assertTrue(os.path.exists(renamed_path))

    def test_enter_on_search_button_triggers_search(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        with patch.object(window, "perform_search") as search_mock:
            window.search_btn.clicked.disconnect()
            window.search_btn.clicked.connect(window.perform_search)
            handled = window.eventFilter(window.search_btn, key_event)

        self.assertTrue(handled)
        search_mock.assert_called_once_with()
        window.close()

    def test_enter_on_cancel_button_triggers_cancel(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        window.cancel_btn.setEnabled(True)
        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        with patch.object(window, "cancel_search") as cancel_mock:
            window.cancel_btn.clicked.disconnect()
            window.cancel_btn.clicked.connect(window.cancel_search)
            handled = window.eventFilter(window.cancel_btn, key_event)

        self.assertTrue(handled)
        cancel_mock.assert_called_once_with()
        window.close()

    def test_enter_on_reset_button_triggers_reset(self):
        with patch("fy_search.ui.load_settings", return_value=AppSettings()):
            window = FileSearchGUI()

        key_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        with patch.object(window, "reset_sort") as reset_mock:
            window.reset_sort_btn.clicked.disconnect()
            window.reset_sort_btn.clicked.connect(window.reset_sort)
            handled = window.eventFilter(window.reset_sort_btn, key_event)

        self.assertTrue(handled)
        reset_mock.assert_called_once_with()
        window.close()
