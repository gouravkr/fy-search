"""Compatibility wrapper for older imports."""

from __future__ import annotations

from .app import main, run

__all__ = ["main", "run"]


if __name__ == "__main__":
    run()
