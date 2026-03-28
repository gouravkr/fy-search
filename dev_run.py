"""Development runner with hot reload support."""

from __future__ import annotations

try:
    from watchfiles import run_process
except ImportError as exc:  # pragma: no cover - dev-only dependency
    raise SystemExit("watchfiles is required for dev_run.py. Install dev dependencies with `uv sync --group dev`.") from exc


def start() -> None:
    from fy_search.app import main

    raise SystemExit(main())


if __name__ == "__main__":
    run_process(".", target=start)
