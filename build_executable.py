#!/usr/bin/env python3
"""
PyInstaller build script for the apps in the apps/ folder.

Each app lives in apps/<name>/ with an entry script apps/<name>/<name>.py and
an optional apps/<name>/requirements.txt.

Each app gets its own virtual environment at apps/<name>/.venv (Python 3.15,
created and synced with uv), so each app's requirements stay separate. To work
on one app, activate its environment:

    source apps/<name>/.venv/bin/activate

Examples:
    python3 build_executable.py                    # build all apps
    python3 build_executable.py exif-date-rename   # build one app
    python3 build_executable.py --list             # list available apps
    python3 build_executable.py --setup-env        # only create/sync app environments

Requires uv (https://docs.astral.sh/uv/) on PATH.
"""

import argparse
import os
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(SCRIPT_DIR, 'apps')
DIST_DIR = os.path.join(SCRIPT_DIR, 'dist')
BUILD_DIR = os.path.join(SCRIPT_DIR, 'build')
PYTHON_VERSION = '3.15'


def discover_apps():
    """Return {name: info} for every apps/<name>/<name>.py entry script."""
    apps = {}
    if not os.path.isdir(APPS_DIR):
        return apps
    for name in sorted(os.listdir(APPS_DIR)):
        app_dir = os.path.join(APPS_DIR, name)
        entry = os.path.join(app_dir, f'{name}.py')
        if os.path.isfile(entry):
            requirements = os.path.join(app_dir, 'requirements.txt')
            apps[name] = {
                'entry': entry,
                'requirements': requirements if os.path.isfile(requirements) else None,
            }
    return apps


def require_uv():
    """Return the path to uv, or exit if it is not on PATH."""
    uv = shutil.which('uv')
    if not uv:
        print("uv is required but was not found on PATH. Install it from https://docs.astral.sh/uv/")
        sys.exit(1)
    return uv


def app_env_python(name):
    """Path to the Python executable of an app's environment apps/<name>/.venv."""
    env_dir = os.path.join(APPS_DIR, name, '.venv')
    if sys.platform == 'win32':
        return os.path.join(env_dir, 'Scripts', 'python.exe')
    return os.path.join(env_dir, 'bin', 'python')


def setup_env(uv, name, info):
    """Create (if needed) and sync apps/<name>/.venv. Returns its Python path, or None on failure."""
    env_python = app_env_python(name)
    env_dir = os.path.dirname(os.path.dirname(env_python))
    if not os.path.isfile(env_python):
        print(f"Creating environment for {name} with Python {PYTHON_VERSION}: {env_dir}")
        if subprocess.run([uv, 'venv', '--python', PYTHON_VERSION, env_dir]).returncode != 0:
            return None

    cmd = [uv, 'pip', 'install', '--python', env_python, 'pyinstaller']
    if info['requirements']:
        cmd += ['-r', info['requirements']]
    print(f"Syncing requirements for {name}")
    if subprocess.run(cmd).returncode != 0:
        return None
    return env_python


def build_app(name, info, env_python):
    """Build a single-file executable for one app with its environment. Returns True on success."""
    print(f"\n=== Building {name} ===")
    print(f"Using entry script: {info['entry']}")

    cmd = [
        env_python, '-m', 'PyInstaller',
        info['entry'],
        '--onefile',              # Single executable file
        '--noupx',                # Don't use UPX (can cause issues, not worth it for size)
        '--name', name,           # Output name
        '--distpath', DIST_DIR,
        '--workpath', os.path.join(BUILD_DIR, name),
        '--specpath', BUILD_DIR,
        '--noconfirm',            # Overwrite previous build output without asking
    ]
    if sys.platform.startswith('linux'):
        cmd.append('--strip')     # Strip debug symbols (Linux only)

    try:
        result = subprocess.run(cmd)
    except OSError as e:
        print(f"✗ Could not run PyInstaller: {e}")
        return False
    if result.returncode != 0:
        print(f"✗ Build failed for {name}")
        return False

    print(f"✓ Executable created at: {os.path.join(DIST_DIR, name)}")
    return True


def main():
    apps = discover_apps()

    parser = argparse.ArgumentParser(description='Build executables for the apps in apps/.')
    parser.add_argument('names', nargs='*', metavar='APP',
                        help='app(s) to build (default: all apps)')
    parser.add_argument('--list', action='store_true', help='list available apps and exit')
    parser.add_argument('--setup-env', action='store_true',
                        help="only create/sync each selected app's environment, without building")
    args = parser.parse_args()

    if args.list:
        for name in apps:
            print(name)
        return

    if not apps:
        print(f"No apps found in {APPS_DIR} (expected apps/<name>/<name>.py)")
        sys.exit(1)

    unknown = [n for n in args.names if n not in apps]
    if unknown:
        parser.error(f"unknown app(s): {', '.join(unknown)} (available: {', '.join(apps)})")

    selected = args.names or list(apps)
    uv = require_uv()

    failed = []
    for name in selected:
        info = apps[name]
        env_python = setup_env(uv, name, info)
        if env_python is None:
            print(f"✗ Could not set up the environment for {name}")
            failed.append(name)
            continue
        if args.setup_env:
            env_dir = os.path.dirname(os.path.dirname(env_python))
            print(f"✓ Environment ready. Activate it with: source {env_dir}/bin/activate")
            continue
        if not build_app(name, info, env_python):
            failed.append(name)

    print("\n=== Summary ===")
    for name in selected:
        print(f"  {'FAILED' if name in failed else 'OK':6} {name}")
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
