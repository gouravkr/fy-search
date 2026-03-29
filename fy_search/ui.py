"""Qt user interface for the file search application."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

import qtawesome as qta
from PySide6.QtCore import QAbstractTableModel, QDateTime, QDir, QEvent, QLocale, QModelIndex, QSortFilterProxyModel, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor, QDesktopServices, QKeyEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QApplication,
    QComboBox,
    QCompleter,
    QFileDialog,
    QFileSystemModel,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .file_icons import DEFAULT_FILE_ICON, FILE_ICON_MAP, FOLDER_ICON, TYPE_FILE_ICON, normalized_extension
from .search import SearchOptions, iter_search_results
from .settings import NO_QUICK_FILTER, AppSettings, QuickFilters, load_settings, save_settings


@dataclass
class ResultRow:
    """Data container for a single search result."""

    name: str
    full_path: str
    is_dir: bool
    size_bytes: float
    created_on: float
    modified_on: float

    @property
    def extension(self) -> str:
        if self.is_dir:
            return ""
        return normalized_extension(self.name)

    @property
    def display_type(self) -> str:
        return "Folder" if self.is_dir else "File"


class RenameLineEdit(QLineEdit):
    """Inline editor that only commits renames on Enter."""

    commit_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rename_committed = False

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.rename_committed = True
            self.commit_requested.emit()
            return

        if event.key() == Qt.Key.Key_Escape:
            self.rename_committed = False
            self.cancel_requested.emit()
            return

        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        if not self.rename_committed:
            self.cancel_requested.emit()
        super().focusOutEvent(event)


class RenameDelegate(QStyledItemDelegate):
    """Delegate for controlled rename commits in the name column."""

    def createEditor(self, parent, option, index):
        editor = RenameLineEdit(parent)
        editor.commit_requested.connect(lambda: self._commit_and_close(editor))
        editor.cancel_requested.connect(lambda: self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.RevertModelCache))
        return editor

    def setEditorData(self, editor, index):
        if isinstance(editor, RenameLineEdit):
            editor.setText(index.data(Qt.ItemDataRole.EditRole) or "")
            editor.selectAll()
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, RenameLineEdit) and not editor.rename_committed:
            return
        super().setModelData(editor, model, index)

    def _commit_and_close(self, editor: RenameLineEdit) -> None:
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)


class SearchResultModel(QAbstractTableModel):
    """Custom model to store and manage search results."""

    SORT_ROLE = Qt.ItemDataRole.UserRole
    _icon_cache: dict[tuple[str, str], object] = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: List[ResultRow] = []
        self._headers = ["Name", "Ext.", "Path", "Type", "Size", "Created On", "Modified On"]
        self.show_full_path = False
        self.root_path = ""
        self.size_format = "Human Readable"
        self._locale = QLocale.system()

    def rowCount(self, parent=QModelIndex()):
        return len(self._results)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._results)):
            return None

        row_data = self._results[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return row_data.name
            if col == 1:
                return row_data.extension
            if col == 2:
                dir_path = os.path.dirname(row_data.full_path)
                if self.show_full_path:
                    return dir_path
                try:
                    return os.path.relpath(dir_path, self.root_path)
                except ValueError:
                    return dir_path
            if col == 3:
                return row_data.display_type
            if col == 4:
                return self._format_size(row_data)
            if col == 5:
                return self._format_datetime(row_data.created_on)
            if col == 6:
                return self._format_datetime(row_data.modified_on)

        if role == Qt.ItemDataRole.EditRole:
            if col == 0:
                return row_data.name
            if col == 1:
                return row_data.extension
            if col == 2:
                return row_data.full_path
            if col == 3:
                return row_data.display_type
            if col == 4:
                return self._format_size(row_data)
            if col == 5:
                return self._format_datetime(row_data.created_on)
            if col == 6:
                return self._format_datetime(row_data.modified_on)

        if role == Qt.ItemDataRole.DecorationRole:
            if col == 0:
                return self._name_icon(row_data)
            if col == 3:
                return self._type_icon(row_data.is_dir)

        if role == self.SORT_ROLE:
            if col == 0:
                return row_data.name.lower()
            if col == 1:
                return row_data.extension
            if col == 2:
                return row_data.full_path.lower()
            if col == 3:
                return row_data.is_dir
            if col == 4:
                return row_data.size_bytes if not row_data.is_dir else -1
            if col == 5:
                return row_data.created_on
            if col == 6:
                return row_data.modified_on

        if role == Qt.ItemDataRole.ForegroundRole and row_data.is_dir:
            return QColor(34, 139, 34)

        if role == Qt.ItemDataRole.TextAlignmentRole and col in (1, 4):
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = super().flags(index)
        if index.column() == 0:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def _format_size(self, row: ResultRow):
        if self.size_format == "No Size" or row.is_dir:
            return "-" if row.is_dir else ""

        size = row.size_bytes
        if self.size_format == "Bytes":
            return f"{int(size):,} B"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 930:
                return f"{int(size)} {unit}" if unit == "B" else f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def _format_datetime(self, timestamp: float) -> str:
        dt = QDateTime.fromMSecsSinceEpoch(int(timestamp * 1000))
        return self._locale.toString(dt, QLocale.FormatType.ShortFormat)

    def _type_icon(self, is_dir: bool):
        icon_name, color = FOLDER_ICON if is_dir else TYPE_FILE_ICON
        return self._cached_icon(icon_name, color)

    def _name_icon(self, row: ResultRow):
        if row.is_dir:
            icon_name, color = FOLDER_ICON
            return self._cached_icon(icon_name, color)

        extension = normalized_extension(row.name)
        icon_name, color = FILE_ICON_MAP.get(extension, DEFAULT_FILE_ICON)
        return self._cached_icon(icon_name, color)

    @classmethod
    def _cached_icon(cls, icon_name: str, color: str):
        cache_key = (icon_name, color)
        if cache_key not in cls._icon_cache:
            cls._icon_cache[cache_key] = qta.icon(icon_name, color=color)
        return cls._icon_cache[cache_key]

    def clear(self):
        self.beginResetModel()
        self._results = []
        self.endResetModel()

    def set_show_full_path(self, show_full_path: bool):
        if self.show_full_path == show_full_path:
            return

        self.show_full_path = show_full_path
        self._emit_column_changed(2)

    def set_size_format(self, size_format: str):
        if self.size_format == size_format:
            return

        self.size_format = size_format
        self._emit_column_changed(4)

    def _emit_column_changed(self, column: int):
        if not self._results:
            return

        top_left = self.index(0, column)
        bottom_right = self.index(len(self._results) - 1, column)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])

    def add_result(self, result_path: str):
        try:
            is_dir = os.path.isdir(result_path)
            stat = os.stat(result_path)
            new_row = ResultRow(
                name=os.path.basename(result_path),
                full_path=result_path,
                is_dir=is_dir,
                size_bytes=stat.st_size if not is_dir else 0,
                created_on=os.path.getctime(result_path),
                modified_on=stat.st_mtime,
            )

            self.beginInsertRows(QModelIndex(), len(self._results), len(self._results))
            self._results.append(new_row)
            self.endInsertRows()
        except OSError:
            pass

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or not index.isValid() or index.column() != 0:
            return False

        row_data = self._results[index.row()]
        new_name = str(value).strip()
        if not new_name or new_name == row_data.name:
            return False

        if os.sep in new_name or (os.altsep and os.altsep in new_name):
            return False

        source_dir = os.path.dirname(row_data.full_path)
        new_full_path = os.path.join(source_dir, new_name)
        if os.path.exists(new_full_path):
            return False

        try:
            os.rename(row_data.full_path, new_full_path)
        except OSError:
            return False

        row_data.name = new_name
        row_data.full_path = new_full_path
        self.dataChanged.emit(
            self.index(index.row(), 0),
            self.index(index.row(), 2),
            [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole, self.SORT_ROLE],
        )
        return True


class MultiSortProxyModel(QSortFilterProxyModel):
    """Proxy model that supports ordered multi-column sorting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sort_columns: list[tuple[int, Qt.SortOrder]] = []

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        if column < 0:
            self._sort_columns = []
            self.invalidate()
            return

        self._sort_columns = [(column, order)]
        self.invalidate()
        super().sort(column, Qt.SortOrder.AscendingOrder)

    def append_sort_column(self, column, order):
        self._sort_columns = [(c, o) for c, o in self._sort_columns if c != column]
        self._sort_columns.append((column, order))
        if self._sort_columns:
            primary_column, primary_order = self._sort_columns[0]
            self.invalidate()
            super().sort(primary_column, Qt.SortOrder.AscendingOrder)
        else:
            self.invalidate()

    def toggle_sort_column(self, column, add_to_existing=False):
        current_order = next((order for c, order in self._sort_columns if c == column), None)
        next_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder

        if add_to_existing:
            self.append_sort_column(column, next_order)
        else:
            self.sort(column, next_order)

    def lessThan(self, left, right):
        if not self._sort_columns:
            return left.row() < right.row()

        source = self.sourceModel()
        sort_role = self.sortRole()

        for column, order in self._sort_columns:
            left_value = source.data(left.siblingAtColumn(column), sort_role)
            right_value = source.data(right.siblingAtColumn(column), sort_role)

            if left_value == right_value:
                continue

            if order == Qt.SortOrder.AscendingOrder:
                return left_value < right_value
            return left_value > right_value

        return left.row() < right.row()


class DirectoryPathCompleter(QCompleter):
    """Filesystem completer that suggests directories and inserts full paths."""

    def __init__(self, parent=None):
        super().__init__(parent)

        model = QFileSystemModel(parent)
        model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Drives)
        model.setRootPath(QDir.rootPath())
        self.setModel(model)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

    def pathFromIndex(self, index):
        model = self.model()
        if isinstance(model, QFileSystemModel):
            return QDir.toNativeSeparators(model.filePath(index))
        return super().pathFromIndex(index)

    def splitPath(self, path):
        expanded_path = os.path.expanduser(path)
        normalized_path = QDir.fromNativeSeparators(expanded_path)
        return super().splitPath(normalized_path)


class SearchWorker(QThread):
    finished = Signal()
    result_found = Signal(str)
    progress = Signal(int, int)
    error = Signal(str)

    def __init__(self, options: SearchOptions):
        super().__init__()
        self.options = options
        self.cancel_requested = False

    def request_cancel(self):
        self.cancel_requested = True

    def run(self):
        try:
            for result_path in iter_search_results(
                self.options,
                progress_callback=self.progress.emit,
                cancel_callback=lambda: self.cancel_requested,
            ):
                if self.cancel_requested:
                    return
                self.result_found.emit(result_path)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()


class FileSearchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("fy_search")
        self.setGeometry(100, 100, 1200, 700)
        self._search_failed = False
        self._loading_settings = False

        self.model = SearchResultModel()
        self.proxy_model = MultiSortProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(SearchResultModel.SORT_ROLE)
        self.cancel_search_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.cancel_search_shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        self.cancel_search_shortcut.activated.connect(self.cancel_search)
        self._enter_activates_buttons: set[QPushButton] = set()
        self.quick_filters = QuickFilters.defaults()

        self.init_ui()
        self.load_settings()
        QTimer.singleShot(0, self.focus_search_input)

    def show_context_menu(self, pos):
        index = self.view.indexAt(pos)
        if not index.isValid():
            return

        source_index = self.proxy_model.mapToSource(index)
        result_row = self.model._results[source_index.row()]

        menu = self._create_context_menu()

        open_action = menu.addAction("Open")
        open_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(result_row.full_path)))
        show_in_folder_action = menu.addAction("Show in Folder")
        show_in_folder_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(result_row.full_path))))
        if self.can_rename_index(index):
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(lambda: self.begin_rename(index))
        menu.exec(self.view.viewport().mapToGlobal(pos))

    def _create_context_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                padding: 2px;
            }
            QMenu::item {
                padding: 4px 6px;
                margin: 2px 0;
                border-radius: 2px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #EFF6FF;
                color: #0F172A;
            }
            QMenu::separator {
                height: 1px;
                margin: 2px 4px;
                background: #E5E7EB;
            }
            """
        )
        return menu

    def on_double_click(self, index):
        if not index.isValid():
            return

        NAME_COLUMN = 0
        PATH_COLUMN = 2

        if index.column() not in (NAME_COLUMN, PATH_COLUMN):
            return

        source_index = self.proxy_model.mapToSource(index)

        if source_index.column() == NAME_COLUMN:
            result_row = self.model._results[source_index.row()]
            QDesktopServices.openUrl(QUrl.fromLocalFile(result_row.full_path))
        elif source_index.column() == PATH_COLUMN:
            result_row = self.model._results[source_index.row()]
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(result_row.full_path)))

    def can_rename_index(self, index: QModelIndex) -> bool:
        return index.isValid() and index.column() == 0

    def begin_rename(self, index: QModelIndex) -> None:
        if not self.can_rename_index(index):
            return

        self.view.setCurrentIndex(index)
        self.view.edit(index)

    def init_ui(self):
        self._create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)

        ## Path and Search box
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setSpacing(0)
        top_controls_layout.addWidget(QLabel("Path:"))
        top_controls_layout.addSpacing(8)
        self.path_input = QLineEdit(os.path.expanduser("~"))
        self.path_input.addAction(qta.icon("fa5s.folder", color="#64748B"), QLineEdit.ActionPosition.LeadingPosition)

        self.path_completer = DirectoryPathCompleter(self)
        self.path_input.setCompleter(self.path_completer)
        top_controls_layout.addWidget(self.path_input, 5)
        self.browse_btn = QPushButton("")
        self.browse_btn.setIcon(qta.icon("fa5s.folder-open", color="#475569"))
        self.browse_btn.clicked.connect(self.browse_path)
        self._register_enter_activated_button(self.browse_btn)
        top_controls_layout.addWidget(self.browse_btn)
        top_controls_layout.addSpacing(16)

        # Search input
        self.pattern_input = QLineEdit()
        self.pattern_input.addAction(qta.icon("fa5s.search", color="#64748B"), QLineEdit.ActionPosition.LeadingPosition)
        self.pattern_input.setPlaceholderText("Enter file/folder name or regex...")
        self.pattern_input.returnPressed.connect(self.perform_search)
        top_controls_layout.addWidget(self.pattern_input, 3)

        self.quick_filter_combo = QComboBox()
        top_controls_layout.addWidget(self.quick_filter_combo)

        top_controls_layout.addSpacing(16)
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.perform_search)
        self._register_enter_activated_button(self.search_btn)
        top_controls_layout.addWidget(self.search_btn)
        main_layout.addLayout(top_controls_layout)

        tools_group = QGroupBox("Search Options")
        tools_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        tools_layout = QVBoxLayout(tools_group)

        row1 = QHBoxLayout()
        row1.setAlignment(Qt.AlignJustify)

        type_layout = QVBoxLayout()
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Files and Folders", "Files Only", "Folders Only"])
        type_layout.addWidget(QLabel("Type:"))
        type_layout.addWidget(self.search_type_combo)
        row1.addLayout(type_layout)
        row1.addStretch()

        match_type_layout = QVBoxLayout()
        self.pattern_type_combo = QComboBox()
        self.pattern_type_combo.addItems(["Name Match", "Regular Expression"])
        match_type_layout.addWidget(QLabel("Pattern:"))
        match_type_layout.addWidget(self.pattern_type_combo)
        row1.addLayout(match_type_layout)
        row1.addStretch()

        min_file_size_layout = QVBoxLayout()
        self.min_file_size = QSpinBox(minimum=0, maximum=1023, singleStep=10)
        self.min_file_size.setFixedWidth(self.min_file_size.fontMetrics().horizontalAdvance("9999") + 24)
        min_file_size_layout.addWidget(QLabel("Min File Size:"))

        min_input_layout = QHBoxLayout()
        min_input_layout.setSpacing(0)
        min_input_layout.setContentsMargins(0, 0, 0, 0)
        min_input_layout.addWidget(self.min_file_size)
        self.min_size_unit = QComboBox()
        self.min_size_unit.addItems(["Bytes", "KB", "MB", "GB"])
        min_input_layout.addWidget(self.min_size_unit)
        min_file_size_layout.addLayout(min_input_layout)
        row1.addLayout(min_file_size_layout)
        row1.addStretch()

        max_file_size_layout = QVBoxLayout()
        self.max_file_size = QSpinBox(minimum=0, maximum=1023, singleStep=10)
        self.max_file_size.setFixedWidth(self.max_file_size.fontMetrics().horizontalAdvance("9999") + 24)
        max_file_size_layout.addWidget(QLabel("Max File Size:"))

        max_input_layout = QHBoxLayout()
        max_input_layout.setSpacing(0)
        max_input_layout.setContentsMargins(0, 0, 0, 0)
        max_input_layout.addWidget(self.max_file_size)
        self.max_size_unit = QComboBox()
        self.max_size_unit.addItems(["Bytes", "KB", "MB", "GB"])
        max_input_layout.addWidget(self.max_size_unit)
        max_file_size_layout.addLayout(max_input_layout)
        row1.addLayout(max_file_size_layout)
        row1.addStretch()

        max_depth_layout = QVBoxLayout()
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(0, 100)
        max_depth_layout.addWidget(QLabel("Max Depth:"))
        max_depth_layout.addWidget(self.depth_spin)
        row1.addLayout(max_depth_layout)
        row1.addStretch()

        modified_days_layout = QVBoxLayout()
        self.days_spin = QSpinBox(suffix=" days")
        self.days_spin.setRange(0, 9999)
        modified_days_layout.addWidget(QLabel("Last Modified Within:"))
        modified_days_layout.addWidget(self.days_spin)
        row1.addLayout(modified_days_layout)
        row1.addStretch()

        tools_layout.addLayout(row1)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_search)
        self.cancel_btn.setEnabled(False)
        self._register_enter_activated_button(self.cancel_btn)

        self.reset_sort_btn = QPushButton("Reset Sort")
        self.reset_sort_btn.clicked.connect(self.reset_sort)
        self._register_enter_activated_button(self.reset_sort_btn)

        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(12)
        options_layout.addWidget(tools_group, 1)
        side_actions_widget = QWidget()
        side_actions_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        side_actions_layout = QVBoxLayout(side_actions_widget)
        side_actions_layout.setContentsMargins(0, 0, 0, 0)
        side_actions_layout.setSpacing(8)
        side_actions_layout.addWidget(self.cancel_btn)
        side_actions_layout.addWidget(self.reset_sort_btn)
        options_layout.addWidget(side_actions_widget, 0, Qt.AlignmentFlag.AlignBottom)

        options_widget = QWidget()
        options_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        options_widget.setLayout(options_layout)
        main_layout.addWidget(options_widget)

        self.view = QTableView()
        self.view.setModel(self.proxy_model)
        self.view.setSortingEnabled(False)
        self.view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.view.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.view.setShowGrid(False)
        self.view.setAlternatingRowColors(True)
        self.view.verticalHeader().setVisible(False)
        self.view.setStyleSheet(
            """
            QTableView {
                background-color: #FFFFFF;
                alternate-background-color: #F8FAFC;
                border: 1px solid #E5E7EB;
                gridline-color: #EEF2F7;
                selection-background-color: #E8F1FF;
                selection-color: #0F172A;
            }
            QTableView::item {
                border-right: 1px solid rgba(148, 163, 184, 0.08);
                padding: 4px 6px;
            }
            QTableView::item:selected {
                border-right: 1px solid rgba(59, 130, 246, 0.10);
            }
            """
        )
        self.rename_delegate = RenameDelegate(self.view)
        self.view.setItemDelegateForColumn(0, self.rename_delegate)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)
        self.view.doubleClicked.connect(self.on_double_click)
        header = self.view.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.view.setColumnWidth(0, 260)
        self.view.setColumnWidth(1, 56)
        self.view.setColumnWidth(2, 520)
        header.setStyleSheet(
            """
            QHeaderView::section {
                background-color: #F8FAFC;
                padding: 4px 6px;
                border: 0;
                border-bottom: 1px solid #E5E7EB;
                border-right: 1px solid rgba(148, 163, 184, 0.10);
                font-weight: bold;
            }
            QHeaderView::section:first {
                border-left: 0;
            }
            QHeaderView::section:last {
                border-right: 0;
            }
            """
        )
        header.sectionClicked.connect(self.handle_header_sort)
        main_layout.addWidget(self.view)

        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

    def _create_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        self.quit_action = QAction("Quit", self)
        self.quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.quit_action.triggered.connect(self.close)
        file_menu.addAction(self.quit_action)

        options_menu = menu_bar.addMenu("Options")
        self.show_full_path_action = QAction("Show Full Path", self)
        self.show_full_path_action.setCheckable(True)
        self.show_full_path_action.toggled.connect(self.apply_show_full_path_setting)
        options_menu.addAction(self.show_full_path_action)

        size_format_menu = options_menu.addMenu("Size Format")
        self.size_format_action_group = QActionGroup(self)
        self.size_format_action_group.setExclusive(True)
        self.size_format_actions: dict[str, QAction] = {}
        for label in ["No Size", "Bytes", "Human Readable"]:
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, value=label: self.apply_size_format_setting(value))
            self.size_format_action_group.addAction(action)
            size_format_menu.addAction(action)
            self.size_format_actions[label] = action

        help_menu = menu_bar.addMenu("Help")
        self.instructions_action = QAction("Instructions", self)
        self.instructions_action.triggered.connect(self.show_instructions)
        help_menu.addAction(self.instructions_action)

        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.path_input.text())
        if directory:
            self.path_input.setText(directory)

    def focus_search_input(self) -> None:
        self.pattern_input.setFocus(Qt.FocusReason.OtherFocusReason)
        self.pattern_input.selectAll()

    def _register_enter_activated_button(self, button: QPushButton) -> None:
        self._enter_activates_buttons.add(button)
        button.installEventFilter(self)

    def eventFilter(self, watched, event):
        if (
            watched in self._enter_activates_buttons
            and event.type() == QEvent.Type.KeyPress
            and isinstance(event, QKeyEvent)
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        ):
            watched.click()
            return True

        return super().eventFilter(watched, event)

    def reset_sort(self):
        header = self.view.horizontalHeader()
        self.proxy_model.sort(-1)
        header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.status_label.setText("Sort reset to default order")

    def handle_header_sort(self, column):
        modifiers = QApplication.keyboardModifiers()
        add_to_existing = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        self.proxy_model.toggle_sort_column(column, add_to_existing=add_to_existing)

        sort_columns = self.proxy_model._sort_columns
        if not sort_columns:
            self.view.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
            return

        primary_column, primary_order = sort_columns[0]
        indicator_order = Qt.SortOrder.DescendingOrder if primary_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        self.view.horizontalHeader().setSortIndicator(primary_column, indicator_order)

    def perform_search(self):
        path = self.path_input.text().strip()
        pattern = self.pattern_input.text().strip()

        if not os.path.isdir(path) or not pattern:
            QMessageBox.warning(self, "Error", "Invalid path or pattern")
            return

        self.model.clear()
        self.model.root_path = path
        self.model.set_show_full_path(self.show_full_path_action.isChecked())
        self.model.set_size_format(self.current_size_format())
        self._search_failed = False

        self.search_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("Searching...")

        unit_multiplier = {"Bytes": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
        min_file_size = None
        max_file_size = None

        if self.min_file_size.value() > 0:
            min_file_size = float(self.min_file_size.text()) * unit_multiplier[self.min_size_unit.currentText()]

        if self.max_file_size.value() > 0:
            max_file_size = float(self.max_file_size.text()) * unit_multiplier[self.max_size_unit.currentText()]

        search_type = ["both", "files", "folders"][self.search_type_combo.currentIndex()]
        options = SearchOptions(
            root_path=path,
            pattern=pattern,
            use_regex=self.pattern_type_combo.currentIndex() == 1,
            max_depth=self.depth_spin.value() or None,
            days=self.days_spin.value() or None,
            search_type=search_type,
            min_file_size=min_file_size,
            max_file_size=max_file_size,
            quick_filter_extensions=self.quick_filters.extensions_for(self.quick_filter_combo.currentText()),
        )

        self.worker = SearchWorker(options)
        self.worker.result_found.connect(self.model.add_result)
        self.worker.progress.connect(self.update_progress)
        self.worker.error.connect(self.handle_search_error)
        self.worker.finished.connect(self.search_finished)
        self.worker.start()

    def update_progress(self, checked, found):
        self.status_label.setText(f"Checked: {checked:,} | Matches: {found}")

    def cancel_search(self):
        if hasattr(self, "worker"):
            self.worker.request_cancel()
            self.status_label.setText("Cancelling search...")

    def handle_search_error(self, message: str):
        self._search_failed = True
        QMessageBox.warning(self, "Search Error", message)

    def search_finished(self):
        self.search_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        if getattr(self, "worker", None) is not None and self.worker.cancel_requested:
            self.status_label.setText(f"Search cancelled. Matches found: {self.model.rowCount()}")
            return

        if self._search_failed:
            self.status_label.setText("Search failed")
            return

        self.status_label.setText(f"Search complete. Total matches: {self.model.rowCount()}")
        self.save_settings()

    def load_settings(self):
        self._loading_settings = True
        settings = load_settings()
        self.quick_filters = settings.quick_filters
        self.quick_filter_combo.clear()
        self.quick_filter_combo.addItems(self.quick_filters.names())
        if settings.path:
            self.path_input.setText(settings.path)
        self.depth_spin.setValue(settings.depth)
        self.show_full_path_action.setChecked(settings.full_path)
        self._set_combo_text(self.search_type_combo, settings.search_type)
        self._set_combo_text(self.pattern_type_combo, settings.pattern_match)
        self._set_combo_text(self.quick_filter_combo, settings.selected_quick_filter)
        self._set_combo_text(self.min_size_unit, settings.min_file_size_unit)
        self._set_combo_text(self.max_size_unit, settings.max_file_size_unit)
        self.apply_show_full_path_setting(self.show_full_path_action.isChecked())
        self.apply_size_format_setting(settings.size_format)
        self._loading_settings = False

    def save_settings(self):
        save_settings(
            AppSettings(
                path=self.path_input.text(),
                depth=self.depth_spin.value(),
                full_path=self.show_full_path_action.isChecked(),
                search_type=self.search_type_combo.currentText(),
                pattern_match=self.pattern_type_combo.currentText(),
                selected_quick_filter=self.quick_filter_combo.currentText() or NO_QUICK_FILTER,
                quick_filters=self.quick_filters,
                min_file_size_unit=self.min_size_unit.currentText(),
                max_file_size_unit=self.max_size_unit.currentText(),
                size_format=self.current_size_format(),
            )
        )

    def apply_show_full_path_setting(self, checked: bool):
        self.model.set_show_full_path(checked)
        if not self._loading_settings:
            self.save_settings()

    def apply_size_format_setting(self, size_format: str):
        self._set_size_format_action(size_format)
        self.model.set_size_format(size_format)
        if not self._loading_settings:
            self.save_settings()

    def current_size_format(self) -> str:
        checked_action = self.size_format_action_group.checkedAction()
        return checked_action.text() if checked_action is not None else "Human Readable"

    def _set_size_format_action(self, size_format: str) -> None:
        action = self.size_format_actions.get(size_format)
        if action is not None:
            action.setChecked(True)

    def show_instructions(self) -> None:
        QMessageBox.information(
            self,
            "Instructions",
            "1. Choose a search path.\n"
            "2. Enter text or a regular expression to search for.\n"
            "3. Optionally adjust filters in Search Options.\n"
            "4. Press Search to begin.\n"
            "5. Use the context menu on results to open, reveal, or rename items.\n"
            "6. You can also double click on file or path columns to open them.",
        )

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About Fy Search",
            "Fy Search\nA cross-platform desktop file search application built with Python and PySide6.",
        )

    @staticmethod
    def _set_combo_text(combo: QComboBox, value: str) -> None:
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
