"""
File Search Application — Modern PySide6 UI
A clean, minimal file search tool with advanced filtering and display options.
"""

import sys
import os
import re
from datetime import datetime, date
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QCheckBox, QComboBox,
    QSpinBox, QDateEdit, QSizePolicy, QScrollArea, QGroupBox,
    QButtonGroup, QAbstractItemView, QProgressBar, QToolButton,
    QSplitter, QStackedWidget
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QDate, QSize, QPropertyAnimation,
    QEasingCurve, QTimer, QSortFilterProxyModel
)
from PySide6.QtGui import (
    QColor, QPalette, QFont, QIcon, QPixmap, QPainter,
    QLinearGradient, QBrush, QFontDatabase, QCursor
)

# ─── Color Palette ────────────────────────────────────────────────────────────
BG          = "#0E0F11"
SURFACE     = "#16181C"
SURFACE2    = "#1E2026"
BORDER      = "#2A2D35"
ACCENT      = "#5B8AF0"
ACCENT_DIM  = "#2A3D6E"
TEXT        = "#E8EAF0"
TEXT_MUTED  = "#6B7280"
TEXT_DIM    = "#4B5563"
SUCCESS     = "#34D399"
WARNING     = "#FBBF24"
DANGER      = "#F87171"
CHIP_BG     = "#1E2026"
CHIP_ACTIVE = "#5B8AF0"

QUICK_FILTERS = [
    ("All",       "*",                          "⬡"),
    ("Apps",      "*.exe;*.app;*.dmg;*.deb",    "◈"),
    ("Images",    "*.jpg;*.jpeg;*.png;*.gif;*.webp;*.svg;*.bmp;*.tiff", "◉"),
    ("Music",     "*.mp3;*.wav;*.flac;*.aac;*.ogg;*.m4a", "◎"),
    ("Video",     "*.mp4;*.mkv;*.mov;*.avi;*.webm", "▷"),
    ("Docs",      "*.pdf;*.doc;*.docx;*.txt;*.md;*.odt", "▤"),
    ("Code",      "*.py;*.js;*.ts;*.html;*.css;*.json;*.yaml;*.rs;*.go;*.cpp", "⌥"),
    ("Archives",  "*.zip;*.tar;*.gz;*.rar;*.7z", "◫"),
]

STYLESHEET = f"""
/* ── Base ─────────────────────────────────────── */
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: 'SF Pro Display', 'Segoe UI Variable', 'Helvetica Neue', 'Helvetica', sans-serif;
    font-size: 13px;
}}

QScrollBar:vertical {{
    background: {SURFACE};
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: {SURFACE};
    height: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Search Bar ───────────────────────────────── */
QLineEdit#searchBar {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 10px;
    padding: 10px 14px;
    color: {TEXT};
    font-size: 14px;
    selection-background-color: {ACCENT_DIM};
}}
QLineEdit#searchBar:focus {{
    border-color: {ACCENT};
    background: {SURFACE2};
}}
QLineEdit#searchBar::placeholder {{
    color: {TEXT_DIM};
}}

/* ── Path Input ───────────────────────────────── */
QLineEdit#pathInput {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TEXT};
    font-size: 12px;
    selection-background-color: {ACCENT_DIM};
}}
QLineEdit#pathInput:focus {{
    border-color: {ACCENT};
}}

/* ── Buttons ──────────────────────────────────── */
QPushButton#browseBtn {{
    background: {SURFACE2};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 8px 16px;
    color: {TEXT};
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#browseBtn:hover {{
    background: {BORDER};
    border-color: {TEXT_MUTED};
}}

QPushButton#searchBtn {{
    background: {ACCENT};
    border: none;
    border-radius: 10px;
    padding: 10px 28px;
    color: white;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
}}
QPushButton#searchBtn:hover {{
    background: #6B96F5;
}}
QPushButton#searchBtn:pressed {{
    background: #4A78E0;
}}

QPushButton#clearBtn {{
    background: transparent;
    border: 1.5px solid {BORDER};
    border-radius: 10px;
    padding: 10px 18px;
    color: {TEXT_MUTED};
    font-size: 13px;
}}
QPushButton#clearBtn:hover {{
    border-color: {TEXT_MUTED};
    color: {TEXT};
}}

/* ── Filter Chips ─────────────────────────────── */
QPushButton#filterChip {{
    background: {CHIP_BG};
    border: 1.5px solid {BORDER};
    border-radius: 20px;
    padding: 6px 14px;
    color: {TEXT_MUTED};
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#filterChip:hover {{
    border-color: {ACCENT};
    color: {TEXT};
}}
QPushButton#filterChip[active="true"] {{
    background: {ACCENT_DIM};
    border-color: {ACCENT};
    color: {ACCENT};
    font-weight: 600;
}}

/* ── Section Labels ───────────────────────────── */
QLabel#sectionLabel {{
    color: {TEXT_DIM};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}}

QLabel#statusLabel {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QLabel#countLabel {{
    color: {ACCENT};
    font-size: 12px;
    font-weight: 600;
}}

/* ── Checkboxes ───────────────────────────────── */
QCheckBox {{
    color: {TEXT_MUTED};
    font-size: 12px;
    spacing: 8px;
}}
QCheckBox:hover {{ color: {TEXT}; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border-radius: 5px;
    border: 1.5px solid {BORDER};
    background: {SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
    image: none;
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}

/* ── Combo Boxes ──────────────────────────────── */
QComboBox {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 7px;
    padding: 6px 10px;
    color: {TEXT};
    font-size: 12px;
    min-width: 120px;
}}
QComboBox:hover {{ border-color: {TEXT_MUTED}; }}
QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE2};
    border: 1.5px solid {BORDER};
    border-radius: 7px;
    color: {TEXT};
    selection-background-color: {ACCENT_DIM};
    selection-color: {TEXT};
    padding: 4px;
}}

/* ── Spin Boxes / Date Edits ──────────────────── */
QSpinBox, QDateEdit {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 7px;
    padding: 6px 10px;
    color: {TEXT};
    font-size: 12px;
}}
QSpinBox:focus, QDateEdit:focus {{ border-color: {ACCENT}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDateEdit::up-button, QDateEdit::down-button {{
    width: 0; height: 0;
}}
QDateEdit::drop-down {{ border: none; width: 0; }}

/* ── Advanced Panel ───────────────────────────── */
QFrame#advancedPanel {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
}}

QFrame#displayPanel {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
}}

/* ── Table ────────────────────────────────────── */
QTableWidget {{
    background: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
    gridline-color: {BORDER};
    color: {TEXT};
    font-size: 12px;
    alternate-background-color: {SURFACE2};
    selection-background-color: {ACCENT_DIM};
    selection-color: {TEXT};
    outline: none;
}}
QTableWidget::item {{
    padding: 0 12px;
    border: none;
}}
QTableWidget::item:selected {{
    background: {ACCENT_DIM};
    color: {TEXT};
}}
QTableWidget::item:hover {{
    background: {SURFACE2};
}}
QHeaderView::section {{
    background: {SURFACE2};
    color: {TEXT_DIM};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    padding: 10px 12px;
    border: none;
    border-bottom: 1.5px solid {BORDER};
    border-right: 1px solid {BORDER};
    text-transform: uppercase;
}}
QHeaderView::section:first {{ border-left: none; }}
QHeaderView::section:last {{ border-right: none; }}
QHeaderView::section:hover {{
    background: {BORDER};
    color: {TEXT};
}}

/* ── Progress Bar ─────────────────────────────── */
QProgressBar {{
    background: {SURFACE2};
    border: none;
    border-radius: 3px;
    height: 3px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 3px;
}}

/* ── Toggle Button ────────────────────────────── */
QPushButton#toggleAdvanced {{
    background: transparent;
    border: none;
    color: {TEXT_MUTED};
    font-size: 12px;
    text-align: left;
    padding: 4px 0;
}}
QPushButton#toggleAdvanced:hover {{
    color: {ACCENT};
}}

QFrame#divider {{
    background: {BORDER};
    max-height: 1px;
    border: none;
}}
"""


# ─── Worker Thread ─────────────────────────────────────────────────────────────
class SearchWorker(QThread):
    result_found  = Signal(str, str, int, float, float)  # name, path, size, created, modified
    search_done   = Signal(int)
    progress      = Signal(int)

    def __init__(self, base_path, pattern, quick_filter_exts,
                 use_regex, min_size, max_size, date_from, date_to):
        super().__init__()
        self.base_path         = base_path
        self.pattern           = pattern
        self.quick_filter_exts = quick_filter_exts
        self.use_regex         = use_regex
        self.min_size          = min_size
        self.max_size          = max_size
        self.date_from         = date_from
        self.date_to           = date_to
        self._stop             = False

    def stop(self):
        self._stop = True

    def run(self):
        count = 0
        try:
            all_files = list(Path(self.base_path).rglob("*"))
        except Exception:
            self.search_done.emit(0)
            return

        total = max(len(all_files), 1)

        # Compile extension set
        if self.quick_filter_exts and self.quick_filter_exts != "*":
            allowed_exts = {e.strip().lower() for e in self.quick_filter_exts.split(";")}
        else:
            allowed_exts = None

        for i, path in enumerate(all_files):
            if self._stop:
                break

            self.progress.emit(int(i / total * 100))

            if not path.is_file():
                continue

            # Extension filter
            if allowed_exts:
                suffix = path.suffix.lower()
                if not any(suffix == ext.lstrip("*") for ext in allowed_exts):
                    continue

            # Name pattern filter
            if self.pattern:
                try:
                    if self.use_regex:
                        if not re.search(self.pattern, path.name, re.IGNORECASE):
                            continue
                    else:
                        if self.pattern.lower() not in path.name.lower():
                            continue
                except re.error:
                    continue

            # Size filter
            try:
                size = path.stat().st_size
            except Exception:
                continue

            if self.min_size >= 0 and size < self.min_size:
                continue
            if self.max_size >= 0 and size > self.max_size:
                continue

            # Date filter
            try:
                mtime = path.stat().st_mtime
                mod_date = date.fromtimestamp(mtime)
            except Exception:
                mtime = 0
                mod_date = date.min

            if self.date_from and mod_date < self.date_from:
                continue
            if self.date_to and mod_date > self.date_to:
                continue

            try:
                ctime = path.stat().st_ctime
            except Exception:
                ctime = 0

            self.result_found.emit(path.name, str(path), size, ctime, mtime)
            count += 1

        self.progress.emit(100)
        self.search_done.emit(count)


# ─── Separator ─────────────────────────────────────────────────────────────────
def make_divider():
    d = QFrame()
    d.setObjectName("divider")
    d.setFixedHeight(1)
    d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return d


# ─── Section Label ─────────────────────────────────────────────────────────────
def make_section_label(text):
    lbl = QLabel(text)
    lbl.setObjectName("sectionLabel")
    return lbl


# ─── Main Window ───────────────────────────────────────────────────────────────
class FileSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileSearch")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)
        self.worker = None

        self.active_filter_idx = 0  # "All"
        self.filter_buttons     = []

        self._build_ui()
        self.setStyleSheet(STYLESHEET)

    # ── Build UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top panel (controls) ──────────────────────────────────────────────
        top_panel = QWidget()
        top_panel.setFixedWidth(360)
        top_panel.setStyleSheet(f"background: {SURFACE}; border-right: 1.5px solid {BORDER};")
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(24, 24, 24, 24)
        top_layout.setSpacing(20)

        # App title
        title_lbl = QLabel("FileSearch")
        title_lbl.setStyleSheet(f"color: {TEXT}; font-size: 20px; font-weight: 700; letter-spacing: -0.5px;")
        subtitle_lbl = QLabel("Find anything, anywhere")
        subtitle_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; margin-top: -6px;")
        top_layout.addWidget(title_lbl)
        top_layout.addWidget(subtitle_lbl)

        top_layout.addWidget(make_divider())

        # ── Base path ─────────────────────────────────────────────────────────
        top_layout.addWidget(make_section_label("BASE PATH"))
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_input = QLineEdit()
        self.path_input.setObjectName("pathInput")
        self.path_input.setPlaceholderText(str(Path.home()))
        self.path_input.setText(str(Path.home()))
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setFixedWidth(72)
        browse_btn.setCursor(QCursor(Qt.PointingHandCursor))
        browse_btn.clicked.connect(self._browse_path)
        path_row.addWidget(self.path_input)
        path_row.addWidget(browse_btn)
        top_layout.addLayout(path_row)

        # ── Quick filters ──────────────────────────────────────────────────────
        top_layout.addWidget(make_section_label("QUICK FILTERS"))
        chips_widget = QWidget()
        chips_layout = QVBoxLayout(chips_widget)
        chips_layout.setSpacing(8)
        chips_layout.setContentsMargins(0, 0, 0, 0)

        row1 = QHBoxLayout(); row1.setSpacing(6)
        row2 = QHBoxLayout(); row2.setSpacing(6)

        for idx, (label, exts, icon) in enumerate(QUICK_FILTERS):
            btn = QPushButton(f"{icon}  {label}")
            btn.setObjectName("filterChip")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setCheckable(False)
            btn.setProperty("active", idx == 0)
            btn.clicked.connect(lambda checked, i=idx: self._set_filter(i))
            self.filter_buttons.append(btn)
            (row1 if idx < 4 else row2).addWidget(btn)

        row1.addStretch(); row2.addStretch()
        chips_layout.addLayout(row1)
        chips_layout.addLayout(row2)
        top_layout.addWidget(chips_widget)

        # ── Search input ───────────────────────────────────────────────────────
        top_layout.addWidget(make_divider())
        top_layout.addWidget(make_section_label("SEARCH"))
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchBar")
        self.search_input.setPlaceholderText("Type a filename or pattern…")
        self.search_input.returnPressed.connect(self._start_search)
        top_layout.addWidget(self.search_input)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("searchBtn")
        self.search_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.search_btn.clicked.connect(self._start_search)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_btn.clicked.connect(self._clear_results)
        btn_row.addWidget(self.search_btn)
        btn_row.addWidget(self.clear_btn)
        top_layout.addLayout(btn_row)

        # ── Advanced options ───────────────────────────────────────────────────
        top_layout.addWidget(make_divider())
        toggle_adv = QPushButton("▸  Advanced Options")
        toggle_adv.setObjectName("toggleAdvanced")
        toggle_adv.setCursor(QCursor(Qt.PointingHandCursor))
        top_layout.addWidget(toggle_adv)

        self.adv_panel = QFrame()
        self.adv_panel.setObjectName("advancedPanel")
        adv_layout = QVBoxLayout(self.adv_panel)
        adv_layout.setContentsMargins(16, 14, 16, 14)
        adv_layout.setSpacing(12)

        # Regex
        self.regex_check = QCheckBox("Use Regular Expressions")
        adv_layout.addWidget(self.regex_check)
        adv_layout.addWidget(make_divider())

        # Size
        size_label = make_section_label("FILE SIZE (BYTES)")
        adv_layout.addWidget(size_label)
        size_row = QHBoxLayout(); size_row.setSpacing(8)
        self.size_min = QSpinBox()
        self.size_min.setRange(0, 999_999_999)
        self.size_min.setSpecialValueText("No min")
        self.size_min.setPrefix("Min  ")
        self.size_max = QSpinBox()
        self.size_max.setRange(-1, 999_999_999)
        self.size_max.setValue(-1)
        self.size_max.setSpecialValueText("No max")
        self.size_max.setPrefix("Max  ")
        size_row.addWidget(self.size_min)
        size_row.addWidget(self.size_max)
        adv_layout.addLayout(size_row)
        adv_layout.addWidget(make_divider())

        # Date
        date_label = make_section_label("MODIFIED DATE RANGE")
        adv_layout.addWidget(date_label)
        date_row = QHBoxLayout(); date_row.setSpacing(8)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate(2000, 1, 1))
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.use_date_filter = QCheckBox("Enable date filter")
        date_row.addWidget(self.date_from)
        date_row.addWidget(self.date_to)
        adv_layout.addLayout(date_row)
        adv_layout.addWidget(self.use_date_filter)

        self.adv_panel.setVisible(False)
        top_layout.addWidget(self.adv_panel)

        def _toggle_adv():
            vis = not self.adv_panel.isVisible()
            self.adv_panel.setVisible(vis)
            toggle_adv.setText(("▾" if vis else "▸") + "  Advanced Options")

        toggle_adv.clicked.connect(_toggle_adv)

        # ── Display options ────────────────────────────────────────────────────
        top_layout.addWidget(make_divider())
        top_layout.addWidget(make_section_label("DISPLAY OPTIONS"))

        disp_panel = QFrame()
        disp_panel.setObjectName("displayPanel")
        disp_layout = QVBoxLayout(disp_panel)
        disp_layout.setContentsMargins(16, 14, 16, 14)
        disp_layout.setSpacing(12)

        path_row2 = QHBoxLayout(); path_row2.setSpacing(12)
        path_lbl2 = QLabel("Path display")
        path_lbl2.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        self.path_combo = QComboBox()
        self.path_combo.addItems(["Relative path", "Full path"])
        path_row2.addWidget(path_lbl2)
        path_row2.addStretch()
        path_row2.addWidget(self.path_combo)
        disp_layout.addLayout(path_row2)

        size_row2 = QHBoxLayout(); size_row2.setSpacing(12)
        size_lbl2 = QLabel("Size unit")
        size_lbl2.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["Auto (KB/MB)", "Bytes"])
        size_row2.addWidget(size_lbl2)
        size_row2.addStretch()
        size_row2.addWidget(self.size_combo)
        disp_layout.addLayout(size_row2)

        top_layout.addWidget(disp_panel)
        top_layout.addStretch()

        # ── Right panel (results) ──────────────────────────────────────────────
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(14)

        # Status bar row
        status_row = QHBoxLayout()
        self.status_lbl = QLabel("Ready to search")
        self.status_lbl.setObjectName("statusLabel")
        self.count_lbl = QLabel("")
        self.count_lbl.setObjectName("countLabel")
        status_row.addWidget(self.status_lbl)
        status_row.addStretch()
        status_row.addWidget(self.count_lbl)
        right_layout.addLayout(status_row)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Path", "Size", "Created", "Modified"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setSortingEnabled(True)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        right_layout.addWidget(self.table)

        # ── Splitter ───────────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {BORDER}; }}")
        splitter.addWidget(top_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 900])

        root_layout.addWidget(splitter)

    # ── Filter chips ────────────────────────────────────────────────────────────
    def _set_filter(self, idx):
        self.active_filter_idx = idx
        for i, btn in enumerate(self.filter_buttons):
            btn.setProperty("active", i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ── Browse ──────────────────────────────────────────────────────────────────
    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Base Directory",
                                                self.path_input.text() or str(Path.home()))
        if path:
            self.path_input.setText(path)

    # ── Format helpers ──────────────────────────────────────────────────────────
    def _format_size(self, size_bytes):
        if self.size_combo.currentIndex() == 1:
            return f"{size_bytes:,} B"
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / 1024**2:.1f} MB"
        else:
            return f"{size_bytes / 1024**3:.2f} GB"

    def _format_path(self, path_str):
        base = self.path_input.text() or str(Path.home())
        if self.path_combo.currentIndex() == 0:
            try:
                return str(Path(path_str).relative_to(base))
            except ValueError:
                return path_str
        return path_str

    def _format_date(self, ts):
        try:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d  %H:%M")
        except Exception:
            return "—"

    # ── Search ──────────────────────────────────────────────────────────────────
    def _start_search(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        base = self.path_input.text().strip() or str(Path.home())
        if not os.path.isdir(base):
            self.status_lbl.setText("⚠  Invalid base path")
            return

        pattern   = self.search_input.text().strip()
        exts      = QUICK_FILTERS[self.active_filter_idx][1]
        use_regex = self.regex_check.isChecked()
        min_size  = self.size_min.value()
        max_size  = self.size_max.value()
        date_from = None
        date_to   = None

        if self.use_date_filter.isChecked():
            qdf = self.date_from.date()
            qdt = self.date_to.date()
            date_from = date(qdf.year(), qdf.month(), qdf.day())
            date_to   = date(qdt.year(), qdt.month(), qdt.day())

        self.table.setRowCount(0)
        self.count_lbl.setText("")
        self.status_lbl.setText("Searching…")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.search_btn.setEnabled(False)

        self.worker = SearchWorker(base, pattern, exts, use_regex,
                                   min_size, max_size, date_from, date_to)
        self.worker.result_found.connect(self._add_row)
        self.worker.search_done.connect(self._search_done)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.start()

    def _add_row(self, name, path, size, ctime, mtime):
        self.table.setSortingEnabled(False)
        row = self.table.rowCount()
        self.table.insertRow(row)

        items = [
            QTableWidgetItem(name),
            QTableWidgetItem(self._format_path(path)),
            QTableWidgetItem(self._format_size(size)),
            QTableWidgetItem(self._format_date(ctime)),
            QTableWidgetItem(self._format_date(mtime)),
        ]
        for col, item in enumerate(items):
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if col == 0:
                item.setForeground(QColor(TEXT))
            else:
                item.setForeground(QColor(TEXT_MUTED))
            self.table.setItem(row, col, item)

        self.count_lbl.setText(f"{row + 1} result{'s' if row else ''}")

    def _search_done(self, count):
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.table.setSortingEnabled(True)
        n = self.table.rowCount()
        self.status_lbl.setText(f"Search complete — {n} file{'s' if n != 1 else ''} found")
        self.count_lbl.setText(f"{n} result{'s' if n != 1 else ''}")

    def _clear_results(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.table.setRowCount(0)
        self.search_input.clear()
        self.status_lbl.setText("Ready to search")
        self.count_lbl.setText("")
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)


# ─── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette baseline
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(BG))
    palette.setColor(QPalette.WindowText,      QColor(TEXT))
    palette.setColor(QPalette.Base,            QColor(SURFACE))
    palette.setColor(QPalette.AlternateBase,   QColor(SURFACE2))
    palette.setColor(QPalette.ToolTipBase,     QColor(SURFACE2))
    palette.setColor(QPalette.ToolTipText,     QColor(TEXT))
    palette.setColor(QPalette.Text,            QColor(TEXT))
    palette.setColor(QPalette.Button,          QColor(SURFACE2))
    palette.setColor(QPalette.ButtonText,      QColor(TEXT))
    palette.setColor(QPalette.BrightText,      Qt.red)
    palette.setColor(QPalette.Highlight,       QColor(ACCENT_DIM))
    palette.setColor(QPalette.HighlightedText, QColor(TEXT))
    app.setPalette(palette)

    window = FileSearchApp()
    window.show()
    sys.exit(app.exec())
