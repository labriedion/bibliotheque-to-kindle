#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "▶ Installing build dependencies..."
pip3 install pyinstaller pillow tkinterdnd2 pycryptodome lxml keyring

echo "▶ Generating icon..."
python3 -c "
import sys; sys.path.insert(0, '.')
from app import _generate_icon
_generate_icon()
"

echo "▶ Building app bundle..."
pyinstaller --clean --noconfirm KindleConverter-mac.spec

echo "▶ Done!  App is at: dist/Kindle\ Converter.app"
echo "   To create a DMG for distribution:"
echo "   hdiutil create -volname 'Kindle Converter' -srcfolder dist/'Kindle Converter.app' -ov -format UDZO dist/KindleConverter.dmg"
