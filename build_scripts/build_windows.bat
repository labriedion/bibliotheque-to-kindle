@echo off
cd /d "%~dp0.."

echo Installing build dependencies...
pip install pyinstaller pillow tkinterdnd2 pycryptodome lxml

echo Converting icon to .ico...
python -c "from PIL import Image; Image.open('src/icon.png').save('src/icon.ico')"

echo Building executable...
pyinstaller --clean --noconfirm --distpath releases\windows --workpath build\windows build_scripts\BibliothequeToKindle-windows.spec

echo.
echo Done! Executable is at: releases\windows\BibliothequeToKindle.exe
