#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
BUNDLE_PATH="${PROJECT_ROOT}/dist/fy-search"
APPIMAGE_ROOT="${PROJECT_ROOT}/dist/appimage"
APPDIR="${APPIMAGE_ROOT}/AppDir"
cd "${PROJECT_ROOT}"

VERSION="$(python3 - <<'PY'
import tomllib
from pathlib import Path

data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
print(data["project"]["version"])
PY
)"

if [[ ! -e "${BUNDLE_PATH}" ]]; then
  echo "PyInstaller bundle not found at ${BUNDLE_PATH}" >&2
  echo "Run ./packaging/linux/build-pyinstaller.sh first." >&2
  exit 1
fi

if ! command -v appimagetool >/dev/null 2>&1; then
  echo "appimagetool is required to build the AppImage." >&2
  exit 1
fi

rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin" "${APPDIR}/usr/share/applications" "${APPDIR}/usr/share/icons/hicolor/scalable/apps"

if [[ -d "${BUNDLE_PATH}" ]]; then
  cp -R "${BUNDLE_PATH}/." "${APPDIR}/usr/bin/"
else
  cp "${BUNDLE_PATH}" "${APPDIR}/usr/bin/fy-search"
fi
cp "${PROJECT_ROOT}/packaging/linux/fy-search.desktop" "${APPDIR}/usr/share/applications/fy-search.desktop"
cp "${PROJECT_ROOT}/fy_search/assets/fy-search.svg" "${APPDIR}/usr/share/icons/hicolor/scalable/apps/fy-search.svg"
cp "${PROJECT_ROOT}/fy_search/assets/fy-search.svg" "${APPDIR}/fy-search.svg"

cat > "${APPDIR}/AppRun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${HERE}/usr/bin/fy-search" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

cp "${PROJECT_ROOT}/packaging/linux/fy-search.desktop" "${APPDIR}/fy-search.desktop"

mkdir -p "${APPIMAGE_ROOT}"
appimagetool "${APPDIR}" "${APPIMAGE_ROOT}/fy-search-${VERSION}-x86_64.AppImage"

echo "Built AppImage at ${APPIMAGE_ROOT}/fy-search-${VERSION}-x86_64.AppImage"
