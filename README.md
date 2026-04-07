# Kindle Converter

A simple app that removes Adobe DRM from library ebooks (EPUB and PDF) and sends them to your Kindle. Works on macOS, Windows, and Linux.

## How it works

1. Drop an `.acsm`, `.epub`, or `.pdf` file onto the app
2. If it's an ACSM, the app opens Adobe Digital Editions to download the book and waits for it to appear
3. DRM is removed using [DeDRM_tools](https://github.com/noDRM/DeDRM_tools)
4. The DRM-free file is saved to your Desktop and your default email client opens with the Kindle address and file pre-filled — just click Send

If a borrowed book's loan has expired, the app will ask you to confirm you've deleted it from your Kindle library before letting you borrow another one.

## Requirements

- Python 3.8+
- [Adobe Digital Editions](https://www.adobe.com/solutions/ebook/digital-editions/download.html) — installed and authorized with your library account
- An email client configured with at least one account:
  - **macOS**: Mail.app
  - **Windows**: Outlook, Thunderbird, Windows Mail, or any MAPI-compatible client
  - **Linux**: any `xdg-email`-compatible client (Thunderbird, Evolution, etc.)

## Setup

```bash
git clone https://github.com/your-username/kindle-converter
cd kindle-converter
python3 app.py
```

The first time you run it, a setup window will automatically:
- Install dependencies (`pycryptodome`, `lxml`, `Pillow`)
- Download the DeDRM plugin files from [noDRM/DeDRM_tools](https://github.com/noDRM/DeDRM_tools)

After setup, click the ⚙ icon and enter your Kindle email address. Find it at:
**Amazon → Manage Your Content and Devices → Preferences → Personal Document Settings**

## Building a standalone app (no Python required)

**macOS** — produces `Kindle Converter.app` and optionally a `.dmg`:
```bash
./build_mac.sh
```

**Windows** — produces `KindleConverter.exe`:
```bat
build_windows.bat
```

## Legal notice

This tool is intended for removing DRM from ebooks you have legitimately borrowed or purchased, for personal use only. Circumventing DRM may be restricted in your jurisdiction. Use responsibly.

DRM removal is performed by [DeDRM_tools](https://github.com/noDRM/DeDRM_tools) (fetched at setup time), which is licensed separately under GPL v3.

## License

MIT — see [LICENSE](LICENSE).
