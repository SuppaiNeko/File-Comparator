#!/usr/bin/env bash
# Build File Comparator as a windowless executable with PyInstaller.
#
# Usage: ./build.sh [--skip-tests]
#
# Runs the unit tests, then builds for the current platform into dist/<platform>/
# (linux, macos or windows). On Linux or macOS, if Wine is installed with Python
# and PyInstaller inside it, a Windows .exe is also built into dist/windows/.
#
# Set PYTHON to choose the interpreter, e.g.  PYTHON=.venv/bin/python ./build.sh
# On Windows, build.bat does the same without needing Bash.

set -euo pipefail
cd "$(dirname "$0")"

run_tests=1
for arg in "$@"; do
    case "$arg" in
        --skip-tests) run_tests=0 ;;
        *) echo "Unknown option: $arg (usage: ./build.sh [--skip-tests])" >&2; exit 1 ;;
    esac
done

# Use the first interpreter that actually runs; on Windows "python3" can be a Microsoft Store stub
if [ -z "${PYTHON:-}" ]; then
    for candidate in python3 python; do
        if "$candidate" -c 'import sys' >/dev/null 2>&1; then
            PYTHON=$candidate
            break
        fi
    done
fi
if [ -z "${PYTHON:-}" ]; then
    echo "Python was not found. Install Python 3 or set PYTHON." >&2
    exit 1
fi
if ! "$PYTHON" -m PyInstaller --version >/dev/null 2>&1; then
    echo "PyInstaller is not installed for $PYTHON. Install it with: $PYTHON -m pip install pyinstaller" >&2
    exit 1
fi

case "$(uname -s)" in
    Linux*) platform=linux ;;
    Darwin*) platform=macos ;;
    MINGW*|MSYS*|CYGWIN*) platform=windows ;;
    *) platform=$(uname -s | tr '[:upper:]' '[:lower:]') ;;
esac

# build <platform> <python command...>
build() {
    local target=$1
    shift
    local options=(--onefile)
    if [ "$target" = windows ]; then
        # PyInstaller resolves a relative icon path against the .spec folder, so pass an absolute one.
        # Python works it out so the path is in its own format (also under Wine and Git Bash).
        local icon
        icon=$("$@" -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' a.ico | tr -d '\r')
        options+=(--icon "$icon")
    elif [ "$target" = macos ]; then
        # Windowless macOS builds are .app bundles, and one-file .app bundles are deprecated
        options=(--onedir)
    fi
    "$@" -m PyInstaller Comparator.py \
        "${options[@]}" \
        --noconsole \
        --clean \
        --noconfirm \
        --name Comparator \
        --distpath "dist/$target" \
        --workpath "build/$target" \
        --specpath "build/$target"
    echo "Built dist/$target/"
}

if [ "$run_tests" = 1 ]; then
    echo "Running tests..."
    "$PYTHON" -m unittest || { echo "Tests failed, not building." >&2; exit 1; }
fi

echo "Building $platform executable..."
build "$platform" "$PYTHON"

if [ "$platform" != windows ] && command -v wine >/dev/null 2>&1; then
    if wine python -m PyInstaller --version >/dev/null 2>&1; then
        echo "Building Windows executable with Wine..."
        build windows wine python
    else
        echo "Wine was found without Python and PyInstaller inside it, so the Windows build was skipped." >&2
    fi
fi
