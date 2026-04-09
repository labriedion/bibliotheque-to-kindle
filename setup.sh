#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Kindle Converter — Setup ==="
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found."
    echo "Install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

echo "Python: $(python3 --version)"
echo ""

echo "Installing Python packages…"
pip3 install -r "$SCRIPT_DIR/requirements.txt"
echo ""

echo "=== Setup complete! ==="
echo ""
echo "Run the app:  python3 app.py   or   ./run.sh"
echo ""
echo "IMPORTANT: Make sure Adobe Digital Editions is installed and authorised"
echo "before running the app.  (Open ADE → Help → Authorize Computer)"
