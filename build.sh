#!/bin/bash


BUILD=$(cat <<EOF
import PyInstaller.__main__
PyInstaller.__main__.run([
    'Comparator.py',
    '--onefile',
    '--noconsole',
    '--icon=a.ico',
    '--clean'
])
EOF
)

python3 -c "$BUILD"
wine python -m PyInstaller --onefile --noconsole --icon=a.ico --distpath ./windows --specpath ./windows Comparator.py

