#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$SCRIPT_DIR/Bibliothèque to Kindle.app"
MACOS="$APP/Contents/MacOS"

echo "Building Bibliothèque to Kindle.app …"

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
    <string>BibliothequeToKindle</string>
    <key>CFBundleIdentifier</key>
    <string>com.bibliothequetokindleapp</string>
    <key>CFBundleName</key>
    <string>Bibliothèque to Kindle</string>
    <key>CFBundleDisplayName</key>
    <string>Bibliothèque to Kindle</string>
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
cat > "$MACOS/BibliothequeToKindle" << 'LAUNCHER'
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
    osascript -e 'display dialog "Python 3.8 or later is required but was not found.\n\nInstall it from:\npython.org/downloads\n\nThen re-open Bibliothèque to Kindle." with title "Bibliothèque to Kindle" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

"$PYTHON" "$PROJECT_DIR/app.py" 2>"$LOG"
STATUS=$?
if [ $STATUS -ne 0 ]; then
    ERROR=$(tail -20 "$LOG" 2>/dev/null | tr '"' "'" | tr '\n' ' ')
    osascript -e "display dialog \"Bibliothèque to Kindle crashed.\n\n$ERROR\n\nFull log: $LOG\" with title \"Bibliothèque to Kindle\" buttons {\"OK\"} default button \"OK\" with icon stop"
fi
LAUNCHER

chmod +x "$MACOS/BibliothequeToKindle"

echo ""
echo "Done!  Bibliothèque to Kindle.app is ready."
echo ""
echo "This is a lightweight launcher that requires Python to be installed."
echo "For a fully standalone bundle with no Python dependency, use build_mac.sh instead."
echo ""
echo "On first launch macOS may show a security warning — right-click the app and choose Open to bypass it."
echo "Run ./setup.sh first if you haven't already."
