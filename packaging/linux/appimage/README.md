# AppImage packaging

AppImage is a standalone executable for Linux systems. The `appimage/build.sh` helps create an AppImage of `FySearch` which can be run on Linux distro without installation.

Building using this script requires Appimagetool, which can be downloaded from https://github.com/AppImage/appimagetool/releases

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
