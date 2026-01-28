#!/usr/bin/env python3
"""
PyInstaller build script for exif-date-rename.
Creates a compact, single-file executable for Linux.
"""

import PyInstaller.__main__
import sys
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
main_script = os.path.join(script_dir, 'exif-date-rename.py')

# PyInstaller arguments optimized for compact Linux executable
args = [
    main_script,
    '--onefile',              # Single executable file
    '--strip',                # Strip the executable (Linux only, removes debug symbols)
    '--noupx',                # Don't use UPX (can cause issues, not worth it for size)
    '-n', 'exif-date-rename', # Output name
    '--distpath', os.path.join(script_dir, 'dist'),
    '--workpath', os.path.join(script_dir, 'build'),
    '--specpath', os.path.join(script_dir, 'build'),
]

print("Building compact exif-date-rename executable for Linux...")
print(f"Using main script: {main_script}")

try:
    PyInstaller.__main__.run(args)
    exec_path = os.path.join(script_dir, 'dist', 'exif-date-rename')
    print("\n✓ Build successful!")
    print(f"✓ Executable created at: {exec_path}")
    print("\nUsage:")
    print(f"  {exec_path} --help")
except Exception as e:
    print(f"\n✗ Build failed: {e}")
    sys.exit(1)
