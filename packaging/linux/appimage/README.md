# AppImage packaging

AppImage is the recommended first Linux deliverable for `fy_search`.

## Build

```bash
./packaging/linux/build-pyinstaller.sh
./packaging/linux/appimage/build.sh
```

The script:

- uses the PyInstaller output from `dist/fy-search`
- creates an `AppDir` layout under `dist/appimage/AppDir`
- installs the shared desktop file and icon
- creates an `AppRun` launcher
- runs `appimagetool`

It supports both a one-file PyInstaller executable and a directory-style bundle.

The resulting artifact is written to `dist/appimage/`.
