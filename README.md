# FySearch

`FySearch` is a cross-platform desktop file search which works seamlessly on Linux and Windows. There's no setup or indexing needed, just launch and start searching.

It is built with Python and packaged for distribution with `PyInstaller`.

## Features

- Quickly search for files and folders anywhere on your PC
- No need for indexing or building a database
- Plain-text and regular-expression matching
- Optional folder depth, age, and size filters
- Sortable results table
- Clean and modern UI with no distraction, only essential features

## Development

This application uses uv for dependency management.

Install dependencies:

```bash
uv sync --group dev
```

Run the development hot-reload entrypoint:

```bash
uv run --group dev python dev_run.py
```

Run the production entrypoint:

```bash
uv run python -m fy_search
```

## Development Guidelines

* This application uses uv for dependency management. It is recommended to use the same to avoid any conflicts.
* This application uses ruff for linting and formatting

## Packaging

Create a standalone executable with `PyInstaller`:

```bash
uv sync --group dev
uv run pyinstaller packaging/pyinstaller/fy_search.spec --clean
```

This will generate Linux executable on Linux and .exe file on Windows.

Linux-native formats such as `.deb` and AppImage should be created as a second packaging step on top
of the built application bundle.

Linux packaging helpers are included in `packaging/linux/`:

- `packaging/linux/build-pyinstaller.sh` builds the Linux app bundle
- `packaging/linux/appimage/build.sh` wraps the bundle as an AppImage
- `packaging/linux/deb/build.sh` wraps the bundle as a `.deb`

Build Linux artifacts on Linux. Do not cross-build them from Windows.