# Building the Executable

This project includes a PyInstaller build script to create a compact, single-file Linux executable.

## Prerequisites

The build script uses your virtual environment. Ensure you have:
- Python 3.14 development libraries: `libpython3.14-dev` (installed via apt if needed)
- PyInstaller installed in your venv (already in requirements if you've set up the project)

## Building

From the project root, activate the virtual environment and run the build script:

```bash
source venv/bin/activate
python3 build_executable.py
```

The executable will be created at: `dist/exif-date-rename`

## Output

- **Size**: ~14MB (compact single-file executable)
- **Location**: `./dist/exif-date-rename`
- **Features**:
  - Single standalone binary (no dependencies required)
  - Stripped of debug symbols for minimal size
  - Optimized for Linux x86_64

## Usage

After building, you can run the executable directly:

```bash
./dist/exif-date-rename --help
./dist/exif-rename /path/to/photos
```

Or add the dist directory to your PATH for global access.

## Cleanup

To remove build artifacts while keeping the executable:

```bash
rm -rf build
```

To completely clean everything including the executable:

```bash
rm -rf dist build
```
