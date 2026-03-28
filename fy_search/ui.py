"""Qt user interface for the file search application."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from PySide6.QtCore import QAbstractTableModel, QDateTime, QLocale, QModelIndex, QSortFilterProxyModel, Qt, QThread, Signal
from PySide6.QtGui import QColor, QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .search import SearchOptions, iter_search_results
from .settings import load_settings, save_settings


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
    def display_type(self) -> str:
        return "Folder" if self.is_dir else "File"


class SearchResultModel(QAbstractTableModel):
    """Custom model to store and manage search results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: List[ResultRow] = []
        self._headers = ["Name", "Path", "Type", "Size", "Created On", "Modified On"]
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
                dir_path = os.path.dirname(row_data.full_path)
                if self.show_full_path:
                    return dir_path
                try:
                    return os.path.relpath(dir_path, self.root_path)
                except ValueError:
                    return dir_path
            if col == 2:
                return row_data.display_type
            if col == 3:
                return self._format_size(row_data)
            if col == 4:
                return self._format_datetime(row_data.created_on)
            if col == 5:
                return self._format_datetime(row_data.modified_on)

        if role == Qt.ItemDataRole.EditRole:
            if col == 0:
                return row_data.name.lower()
            if col == 1:
                return row_data.full_path.lower()
            if col == 2:
                return row_data.is_dir
            if col == 3:
                return row_data.size_bytes if not row_data.is_dir else -1
            if col == 4:
                return row_data.created_on
            if col == 5:
                return row_data.modified_on

        if role == Qt.ItemDataRole.ForegroundRole and row_data.is_dir:
            return QColor(34, 139, 34)

        if role == Qt.ItemDataRole.TextAlignmentRole and col == 3:
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

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

    def clear(self):
        self.beginResetModel()
        self._results = []
        self.endResetModel()

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
        super().sort(column, order)

    def append_sort_column(self, column, order):
        self._sort_columns = [(c, o) for c, o in self._sort_columns if c != column]
        self._sort_columns.append((column, order))
        if self._sort_columns:
            primary_column, primary_order = self._sort_columns[0]
            super().sort(primary_column, primary_order)
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

        self.model = SearchResultModel()
        self.proxy_model = MultiSortProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(Qt.ItemDataRole.EditRole)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Search Path:"))
        self.path_input = QLineEdit(os.path.expanduser("~"))
        path_layout.addWidget(self.path_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        main_layout.addLayout(path_layout)

        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("Search for:"))
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter file/folder name or regex...")
        self.pattern_input.returnPressed.connect(self.perform_search)
        pattern_layout.addWidget(self.pattern_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.perform_search)
        pattern_layout.addWidget(self.search_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_search)
        self.cancel_btn.setEnabled(False)
        pattern_layout.addWidget(self.cancel_btn)

        self.reset_sort_btn = QPushButton("Reset Sort")
        self.reset_sort_btn.clicked.connect(self.reset_sort)
        pattern_layout.addWidget(self.reset_sort_btn)
        main_layout.addLayout(pattern_layout)

        tools_group = QGroupBox("Search Options")
        tools_layout = QVBoxLayout(tools_group)

        row1 = QHBoxLayout()
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Files and Folders", "Files Only", "Folders Only"])
        row1.addWidget(QLabel("Type:"))
        row1.addWidget(self.search_type_combo)

        self.pattern_type_combo = QComboBox()
        self.pattern_type_combo.addItems(["Name Match", "Regular Expression"])
        row1.addWidget(QLabel("Pattern:"))
        row1.addWidget(self.pattern_type_combo)

        self.min_file_size = QLineEdit()
        self.min_file_size.setValidator(QIntValidator(0, 999999999, self))
        self.min_file_size.setFixedWidth(self.min_file_size.fontMetrics().horizontalAdvance("999") + 24)
        row1.addWidget(QLabel("Min File Size:"))
        row1.addWidget(self.min_file_size)
        self.min_size_unit = QComboBox()
        self.min_size_unit.addItems(["Bytes", "KB", "MB", "GB"])
        row1.addWidget(self.min_size_unit)

        self.max_file_size = QLineEdit()
        self.max_file_size.setValidator(QIntValidator(0, 999999999, self))
        self.max_file_size.setFixedWidth(self.max_file_size.fontMetrics().horizontalAdvance("999") + 24)
        row1.addWidget(QLabel("Max File Size:"))
        row1.addWidget(self.max_file_size)
        self.max_size_unit = QComboBox()
        self.max_size_unit.addItems(["Bytes", "KB", "MB", "GB"])
        row1.addWidget(self.max_size_unit)

        row1.addStretch()
        tools_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(0, 100)
        row2.addWidget(QLabel("Max Depth:"))
        row2.addWidget(self.depth_spin)

        self.days_spin = QSpinBox()
        self.days_spin.setRange(0, 9999)
        row2.addWidget(QLabel("Days:"))
        row2.addWidget(self.days_spin)

        self.full_path_check = QCheckBox("Show Full Path")
        row2.addWidget(self.full_path_check)

        self.size_format_combo = QComboBox()
        self.size_format_combo.addItems(["No Size", "Bytes", "Human Readable"])
        self.size_format_combo.setCurrentIndex(2)
        row2.addWidget(QLabel("Size Format:"))
        row2.addWidget(self.size_format_combo)
        row2.addStretch()
        tools_layout.addLayout(row2)
        main_layout.addWidget(tools_group)

        self.view = QTableView()
        self.view.setModel(self.proxy_model)
        self.view.setSortingEnabled(False)
        self.view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.view.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        header = self.view.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.view.setColumnWidth(0, 260)
        self.view.setColumnWidth(1, 520)
        header.setStyleSheet(
            "QHeaderView::section { background-color: #f5f5f5; padding: 4px; border: 1px solid #d0d0d0; font-weight: bold; }"
        )
        header.sectionClicked.connect(self.handle_header_sort)
        main_layout.addWidget(self.view)

        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.path_input.text())
        if directory:
            self.path_input.setText(directory)

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
        self.view.horizontalHeader().setSortIndicator(primary_column, primary_order)

    def perform_search(self):
        path = self.path_input.text().strip()
        pattern = self.pattern_input.text().strip()

        if not os.path.isdir(path) or not pattern:
            QMessageBox.warning(self, "Error", "Invalid path or pattern")
            return

        self.model.clear()
        self.model.root_path = path
        self.model.show_full_path = self.full_path_check.isChecked()
        self.model.size_format = self.size_format_combo.currentText()
        self._search_failed = False

        self.search_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("Searching...")

        unit_multiplier = {"Bytes": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
        min_file_size = None
        max_file_size = None

        if self.min_file_size.text():
            min_file_size = float(self.min_file_size.text()) * unit_multiplier[self.min_size_unit.currentText()]

        if self.max_file_size.text():
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
        settings = load_settings()
        self.path_input.setText(settings.get("path", self.path_input.text()))
        self.depth_spin.setValue(settings.get("depth", 0))
        self.full_path_check.setChecked(settings.get("full_path", False))

    def save_settings(self):
        save_settings(
            {
                "path": self.path_input.text(),
                "depth": self.depth_spin.value(),
                "full_path": self.full_path_check.isChecked(),
            }
        )
