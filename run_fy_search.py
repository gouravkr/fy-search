"""PyInstaller launcher for fy_search.

This wrapper imports the packaged application through the `fy_search`
package so package-relative imports continue to work in frozen builds.
"""

from __future__ import annotations

from fy_search.app import main


if __name__ == "__main__":
    raise SystemExit(main())
