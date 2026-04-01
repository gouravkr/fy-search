"""Application startup helpers."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .ui import FileSearchGUI

ICON_PATH = Path(__file__).resolve().parent / "assets" / "fysearch.png"


def main(argv: Sequence[str] | None = None) -> int:
    app = QApplication(list(argv) if argv is not None else sys.argv)
    icon = QIcon(str(ICON_PATH))
    app.setWindowIcon(icon)
    window = FileSearchGUI()
    window.setWindowIcon(icon)
    window.show()
    return app.exec()


def run() -> None:
    raise SystemExit(main())
