#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
BUNDLE_PATH="${PROJECT_ROOT}/dist/fy-search"
BUILD_ROOT="${PROJECT_ROOT}/dist/deb"
PACKAGE_ROOT="${BUILD_ROOT}/fy-search"
cd "${PROJECT_ROOT}"

VERSION="$(python3 - <<'PY'
import tomllib
from pathlib import Path

data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
print(data["project"]["version"])
PY
)"
ARCHITECTURE="$(dpkg --print-architecture)"

if [[ ! -e "${BUNDLE_PATH}" ]]; then
  echo "PyInstaller bundle not found at ${BUNDLE_PATH}" >&2
  echo "Run ./packaging/linux/build-pyinstaller.sh first." >&2
  exit 1
fi

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb is required to build the Debian package." >&2
  exit 1
fi

rm -rf "${PACKAGE_ROOT}"
mkdir -p \
  "${PACKAGE_ROOT}/DEBIAN" \
  "${PACKAGE_ROOT}/opt/fy-search" \
  "${PACKAGE_ROOT}/usr/bin" \
  "${PACKAGE_ROOT}/usr/share/applications" \
  "${PACKAGE_ROOT}/usr/share/icons/hicolor/scalable/apps"

if [[ -d "${BUNDLE_PATH}" ]]; then
  cp -R "${BUNDLE_PATH}/." "${PACKAGE_ROOT}/opt/fy-search/"
else
  cp "${BUNDLE_PATH}" "${PACKAGE_ROOT}/opt/fy-search/fy-search"
fi
ln -s /opt/fy-search/fy-search "${PACKAGE_ROOT}/usr/bin/fy-search"
cp "${PROJECT_ROOT}/packaging/linux/fy-search.desktop" "${PACKAGE_ROOT}/usr/share/applications/fy-search.desktop"
cp "${PROJECT_ROOT}/fy_search/assets/fysearch.svg" "${PACKAGE_ROOT}/usr/share/icons/hicolor/scalable/apps/fysearch.svg"

cat > "${PACKAGE_ROOT}/DEBIAN/control" <<EOF
Package: fy-search
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCHITECTURE}
Maintainer: fy_search contributors
Description: Cross-platform desktop file search application
EOF

mkdir -p "${BUILD_ROOT}"
dpkg-deb --build "${PACKAGE_ROOT}" "${BUILD_ROOT}/fy-search_${VERSION}_${ARCHITECTURE}.deb"

echo "Built Debian package at ${BUILD_ROOT}/fy-search_${VERSION}_${ARCHITECTURE}.deb"
