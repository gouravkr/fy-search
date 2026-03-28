# fy_search

`fy_search` is a cross-platform desktop file search application built with Python and `PySide6`.
It is intended to run on Linux and Windows during development with `uv`, and to be packaged for
distribution with `PyInstaller`.

## Features

- Search for files, folders, or both
- Plain-text and regular-expression matching
- Optional depth, age, and size filters
- Sortable results table with multi-column sorting
- Cross-platform settings storage

## Development

Install dependencies:

```bash
uv sync --group dev
```

Run the production entrypoint:

```bash
uv run python -m fy_search
```

Run the development hot-reload entrypoint:

```bash
uv run --group dev python dev_run.py
```

## Packaging

Create a standalone executable with `PyInstaller`:

```bash
uv run --group dev pyinstaller packaging/pyinstaller/fy_search.spec
```

Linux-native formats such as `.deb` and AppImage should be created as a second packaging step on top
of the built application bundle. See the files in `packaging/linux/` for the related assets.
