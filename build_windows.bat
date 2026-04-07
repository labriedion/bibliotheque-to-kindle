@echo off
cd /d "%~dp0"

echo Installing build dependencies...
pip install pyinstaller pillow tkinterdnd2 pycryptodome lxml keyring pywin32

echo Converting icon to .ico...
python -c "from PIL import Image; Image.open('icon.png').save('icon.ico')"

echo Building executable...
pyinstaller --clean --noconfirm KindleConverter-windows.spec

echo.
echo Done! Executable is at: dist\KindleConverter.exe
