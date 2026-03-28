"""Application startup helpers."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from .ui import FileSearchGUI


def main(argv: Sequence[str] | None = None) -> int:
    app = QApplication(list(argv) if argv is not None else sys.argv)
    window = FileSearchGUI()
    window.show()
    return app.exec()


def run() -> None:
    raise SystemExit(main())
