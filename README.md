# File Comparator

A small desktop app for checking whether two folders hold the same files. It lists files whose contents differ and files that exist in only one of the folders.

## Requirements

- Python 3.6 or later. Only the standard library is used, including Tkinter.
- PyInstaller, only if you want to build an executable.

## Running

```
python Comparator.py
```

## Using it

1. Click **Select** next to **Directory A** and **Directory B** to choose the two folders. You can also type or paste a path into either box.
2. Optionally tick **Full Directory** to include every subfolder. Without it, only the files directly inside each folder are compared.
3. Optionally pick a **File Type**. The list offers only extensions that appear in both folders. **All** compares every file.
4. Click **Compare Dirs**.

The log shows:

| Section | Meaning |
| --- | --- |
| NON MATCHING FILES | The file exists in both folders, but the contents differ. |
| MISSING FILES | The file exists in only one folder. The line says which folder it is missing from. |
| UNREADABLE FILES | The file exists in both folders, but one copy couldn't be read, for example because of permissions. |

If nothing differs, the log says `No File discrepancies`. Problems such as an invalid folder path are also reported in the log.

### How files are matched

With **Full Directory** ticked, files are paired by their path inside each folder. `A/reports/jan.csv` is compared with `B/reports/jan.csv`, never with a `jan.csv` in some other subfolder. Extension filtering ignores case, so `.TXT` and `.txt` count as the same type.

Comparison uses Python's [`filecmp`](https://docs.python.org/3/library/filecmp.html) in shallow mode. Two files with the same size and the same last-modified time are treated as identical without reading their contents. Otherwise, their contents are compared byte by byte.

## Running the tests

The tests in `test_comparator.py` use only the standard library. Run them from the repository folder:

```
python -m unittest -v
```

They open a hidden Tk window, so they need a desktop session. On a machine without a display, they are skipped.

## Building an executable

Install PyInstaller first:

```
python -m pip install pyinstaller
```

Then run the build script for your system:

| System | Command | Output |
| --- | --- | --- |
| Windows | `build.bat` | `dist\windows\Comparator.exe` |
| Linux | `./build.sh` | `dist/linux/Comparator` |
| macOS | `./build.sh` | `dist/macos/Comparator.app` |

Both scripts run the unit tests first and stop if any fail. Add `--skip-tests` to build without running them. To use a specific Python, such as one in a virtual environment, set the `PYTHON` environment variable:

```
set PYTHON=.venv\Scripts\python.exe        (Windows)
PYTHON=.venv/bin/python ./build.sh          (Linux/macOS)
```

The executable opens without a console window. On Windows it uses the `a.ico` icon.

On Linux or macOS, `build.sh` also builds a Windows `.exe` into `dist/windows/` if Wine is installed with Python and PyInstaller inside it. If Wine is found without them, the script skips this build and prints a notice.

PyInstaller's working files go in `build/`. Both `build/` and `dist/` are ignored by git.
