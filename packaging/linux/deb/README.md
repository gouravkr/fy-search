# Debian packaging

The Debian package installs `fy_search` with this layout:

- application bundle under `/opt/fy-search`
- launcher symlink at `/usr/bin/fy-search`
- desktop entry under `/usr/share/applications`
- icon under `/usr/share/icons/hicolor/scalable/apps`

## Build

```bash
./packaging/linux/build-pyinstaller.sh
./packaging/linux/deb/build.sh
```

The resulting `.deb` is written to `dist/deb/`.

The build script supports both a one-file PyInstaller executable and a directory-style bundle.
