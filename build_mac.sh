#!/bin/bash
set -e
cd "$(dirname "$0")"

PYTHON="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"

echo "▶ Installing build dependencies..."
"$PYTHON" -m pip install pyinstaller pillow tkinterdnd2 pycryptodome lxml keyring

echo "▶ Generating icon..."
"$PYTHON" -c "
import sys; sys.path.insert(0, 'src')
from app import _generate_icon
_generate_icon()
"

echo "▶ Building app bundle..."
"$PYTHON" -m PyInstaller --clean --noconfirm \
    --distpath releases/mac \
    --workpath build/mac \
    BibliothequeToKindle-mac.spec

echo "▶ Done!  App is at: releases/mac/Bibliothèque to Kindle.app"
