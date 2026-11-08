# foto_tools

Some practical tools for managing fotos.

## exif-date-rename 

Renames fotos to contain their EXIF create date. This is very useful for sorting the files on a cloud storage.

### Installation

You can either use the Python script directly or build a standalone executable.

#### Option 1: Python Script

Requires Python 3.7+ and dependencies:

```bash
pip install -r apps/exif-date-rename/requirements.txt
python3 apps/exif-date-rename/exif-date-rename.py /path/to/photos
```

#### Option 2: Standalone Executable

See [Building the Executable](#building-the-executable) section below.

### Usage

```bash
exif-date-rename /path/to/photos                          # Rename all photos
exif-date-rename ~/Pictures/vacation --dry-run            # Preview changes
exif-date-rename . --extensions jpg png heic              # Specific formats
exif-date-rename /photos --prefix "vacation" --dry-run    # Custom prefix
```

**Options:**
- `--dry-run` - Show what would be renamed without actually renaming files
- `--extensions` - File extensions to process (default: png jpg jpeg tiff tif heic)
- `--prefix` - Prefix for renamed files (default: photo)

## Building the Executable

This project includes a PyInstaller build script that creates compact, single-file Linux executables for the apps in `apps/`. See [BUILD.md](BUILD.md) for details.

### Building

```bash
source venv/bin/activate
python3 build_executable.py --install-deps exif-date-rename
```

The executable will be created at: `dist/exif-date-rename`

### Executable Output

- **Size**: ~14MB (compact single-file executable)
- **Location**: `./dist/exif-date-rename`
- **Features**:
  - Single standalone binary (no dependencies required)
  - Stripped of debug symbols for minimal size
  - Optimized for Linux x86_64

### Running the Executable

After building, you can run the executable directly:

```bash
./dist/exif-date-rename --help
./dist/exif-date-rename /path/to/photos
```

Or add the dist directory to your PATH for global access.

### Cleanup

To remove build artifacts while keeping the executable:

```bash
rm -rf build
```

To completely clean everything including the executable:

```bash
rm -rf dist build
```

