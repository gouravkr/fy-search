from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fy_search import __version__

OUTPUT_NAME = f"fysearch-{__version__}"
ROOT_DIR = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT_DIR / "packaging" / "run_fy_search.py"

cmd = [
    sys.executable,
    "-m",
    "nuitka",
    "--standalone",
    "--onefile",
    "--jobs=10",
    "--enable-plugin=pyside6",
    "--include-package=fy_search",
    "--include-data-dir=fy_search/assets=fy_search/assets",
    f"--linux-icon={ROOT_DIR / 'fy_search' / 'assets' / 'fysearch.png'}",
    f"--windows-icon-from-ico={ROOT_DIR / 'fy_search' / 'assets' / 'fysearch.ico'}",
    f"--output-filename={OUTPUT_NAME}",
    f"--output-dir={ROOT_DIR / 'dist' / 'nuitka'}",
    str(ENTRYPOINT),
]

result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT_DIR)

print("STDOUT:\n", result.stdout)
print("STDERR:\n", result.stderr)

result.check_returncode()
