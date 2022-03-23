#!/bin/bash


BUILD=$(cat <<EOF
import PyInstaller.__main__
PyInstaller.__main__.run([
    'Comparator.py',
    '--onefile',
    '--noconsole',
    '--icon=a.ico'
])
EOF
)

python3 -c "$BUILD"

