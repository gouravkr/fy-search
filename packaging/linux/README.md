# Linux packaging

`FySearch` is packaged for Linux in two stages:

1. Build the self-contained Linux application bundle with `PyInstaller`
2. Wrap that bundle as either an `AppImage` or a `.deb`

This directory contains the shared Linux desktop assets and helper scripts for that flow.

## Files

- `build-pyinstaller.sh`: builds the production Linux bundle with the repo's PyInstaller spec
- `fy-search.desktop`: desktop entry used by both AppImage and `.deb` packaging
- `appimage/build.sh`: assembles an `AppDir` and builds an AppImage with `appimagetool`
- `deb/build.sh`: creates a Debian package using `dpkg-deb`

## Prerequisites

- Build on a Linux machine
- Python 3.13 available
- `uv` installed
- For AppImage builds: `appimagetool` available on `PATH`
- For Debian builds: `dpkg-deb` available on `PATH`

## Recommended Flow

Build the bundled application first:

```bash
./packaging/linux/build-pyinstaller.sh
```

Then build one of the Linux-native formats:

```bash
./packaging/linux/appimage/build.sh
./packaging/linux/deb/build.sh
```

The default Linux icon used by both formats lives at
`fy_search/assets/fysearch.svg`.

The wrapper scripts support either PyInstaller output shape:

- a single executable at `dist/fy-search`
- a directory bundle at `dist/fy-search/`
