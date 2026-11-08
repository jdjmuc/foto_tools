# Building the Executables

This project includes a PyInstaller build script that creates compact, single-file Linux executables. Each app lives in `apps/<name>/` with an entry script `apps/<name>/<name>.py` and an optional `apps/<name>/requirements.txt`.

## Prerequisites

- Python 3.15 with its shared library: `libpython3.15` and `libpython3.15-dev` (from the deadsnakes PPA on Ubuntu 24.04: `sudo apt install libpython3.15 libpython3.15-dev`)
- [uv](https://docs.astral.sh/uv/) (optional, used to install requirements; pip is used if uv is not on PATH)

## Setting up the virtual environment

Create the project venv with uv on Python 3.15:

```bash
uv venv --python 3.15 venv
VIRTUAL_ENV=$PWD/venv uv pip install -r apps/exif-date-rename/requirements.txt pyinstaller
```

## Building

From the project root, activate the virtual environment and run the build script:

```bash
source venv/bin/activate
python3 build_executable.py                     # build all apps
python3 build_executable.py exif-date-rename    # build only one app
python3 build_executable.py --list              # list available apps
python3 build_executable.py --install-deps      # install each app's requirements first
```

Executables are created in `dist/<name>`, for example `dist/exif-date-rename`.

## Output

- **Size**: ~14MB per app (compact single-file executable)
- **Location**: `./dist/<name>`
- **Features**:
  - Single standalone binary (no dependencies required)
  - Stripped of debug symbols for minimal size
  - Optimized for Linux x86_64

## Usage

After building, you can run the executable directly:

```bash
./dist/exif-date-rename --help
./dist/exif-date-rename /path/to/photos
```

Or add the dist directory to your PATH for global access.

## Cleanup

To remove build artifacts while keeping the executables:

```bash
rm -rf build
```

To completely clean everything including the executables:

```bash
rm -rf dist build
```
