#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$SCRIPT_DIR/KindleConverter.app"
MACOS="$APP/Contents/MacOS"

echo "Building KindleConverter.app …"

mkdir -p "$MACOS"
mkdir -p "$APP/Contents/Resources"

# ── Info.plist ────────────────────────────────────────────────────────────────
cat > "$APP/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>KindleConverter</string>
    <key>CFBundleIdentifier</key>
    <string>com.family.kindleconverter</string>
    <key>CFBundleName</key>
    <string>Kindle Converter</string>
    <key>CFBundleDisplayName</key>
    <string>Kindle Converter</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
</dict>
</plist>
PLIST

# ── Launcher script ───────────────────────────────────────────────────────────
cat > "$MACOS/KindleConverter" << 'LAUNCHER'
#!/bin/bash
APP_BUNDLE="$(cd "$(dirname "$0")/../.." && pwd)"
PROJECT_DIR="$(dirname "$APP_BUNDLE")"
LOG="$PROJECT_DIR/error.log"

PYTHON=""
for candidate in \
    /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 \
    /usr/local/bin/python3 \
    /opt/homebrew/bin/python3 \
    "$HOME/.pyenv/shims/python3" \
    /usr/bin/python3
do
    for py in $candidate; do
        if "$py" -c "import sys; assert sys.version_info >= (3,8)" 2>/dev/null; then
            PYTHON="$py"
            break 2
        fi
    done
done

if [ -z "$PYTHON" ]; then
    osascript -e 'display dialog "Python 3.8 or later is required but was not found.\n\nInstall it from:\npython.org/downloads\n\nThen re-open Kindle Converter." with title "Kindle Converter" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

"$PYTHON" "$PROJECT_DIR/app.py" 2>"$LOG"
STATUS=$?
if [ $STATUS -ne 0 ]; then
    ERROR=$(tail -20 "$LOG" 2>/dev/null | tr '"' "'" | tr '\n' ' ')
    osascript -e "display dialog \"Kindle Converter crashed.\n\n$ERROR\n\nFull log: $LOG\" with title \"Kindle Converter\" buttons {\"OK\"} default button \"OK\" with icon stop"
fi
LAUNCHER

chmod +x "$MACOS/KindleConverter"

echo ""
echo "Done!  KindleConverter.app is ready."
echo ""
echo "Your mom can double-click it from Finder."
echo "On first launch it will install everything automatically."
echo "(She may need to right-click → Open the very first time if macOS warns about the developer.)"
