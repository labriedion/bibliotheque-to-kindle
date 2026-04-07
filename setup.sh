#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEDRM_DIR="$SCRIPT_DIR/dedrm"
GITHUB_BASE="https://raw.githubusercontent.com/noDRM/DeDRM_tools/master/DeDRM_plugin"

echo "=== Kindle Converter - First-Time Setup ==="
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found."
    echo "Install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

echo "Python 3 found: $(python3 --version)"
echo ""

# Install pip dependencies
echo "Installing required Python packages..."
pip3 install pycryptodome lxml
echo ""

echo "Installing optional drag-and-drop support..."
pip3 install tkinterdnd2 || echo "  (tkinterdnd2 not installed - drag-and-drop unavailable, but app will still work)"
echo ""

# Create dedrm/ package directory
mkdir -p "$DEDRM_DIR"
touch "$DEDRM_DIR/__init__.py"

# Download DeDRM source files from noDRM/DeDRM_tools
echo "Downloading DeDRM tools from GitHub..."
FILES="adobekey.py ineptepub.py ineptpdf.py utilities.py argv_utils.py zeroedzipinfo.py"
for f in $FILES; do
    echo "  Downloading $f ..."
    curl -fsSL "$GITHUB_BASE/$f" -o "$DEDRM_DIR/$f"
done

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To run the app:  ./run.sh"
echo ""
echo "IMPORTANT: Make sure Adobe Digital Editions is installed and your"
echo "computer is authorized before running the app."
echo "(Open ADE → Help → Authorize Computer)"
