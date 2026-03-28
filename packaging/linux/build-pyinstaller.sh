#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${PROJECT_ROOT}"

uv sync --group dev
uv run pyinstaller packaging/pyinstaller/fy_search.spec --clean

echo "Built PyInstaller bundle at ${PROJECT_ROOT}/dist/fy-search"
