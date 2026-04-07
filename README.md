# Kindle Converter

A simple macOS app that removes Adobe DRM from library ebooks (EPUB and PDF) and sends them to your Kindle via email.

## How it works

1. Drop an `.acsm`, `.epub`, or `.pdf` file onto the app
2. If it's an ACSM, the app opens Adobe Digital Editions to download the book, then watches for the file to appear
3. DRM is removed using [DeDRM_tools](https://github.com/noDRM/DeDRM_tools)
4. The DRM-free file is saved to your Desktop and emailed to your Kindle address via Mail.app

## Requirements

- macOS 10.13+
- Python 3.8+
- [Adobe Digital Editions](https://www.adobe.com/solutions/ebook/digital-editions/download.html) — authorized with your library account
- Mail.app — configured with at least one email account

## Setup

```bash
git clone https://github.com/your-username/kindle-converter
cd kindle-converter
python3 app.py
```

The first time you run it, a setup window will automatically install dependencies (`pycryptodome`, `lxml`, `Pillow`) and download the DeDRM plugin files from [noDRM/DeDRM_tools](https://github.com/noDRM/DeDRM_tools).

After setup, enter your Kindle email address in Settings (the ⚙ icon). You can find it at:
**amazon.com → Manage Your Content and Devices → Preferences → Personal Document Settings**

You can also optionally add a second address for a Kids library.

## Running as a macOS app

Double-click `KindleConverter.app` to launch without a terminal window. On first run from a new machine, macOS may show a security warning — right-click the app and choose Open to bypass it.

## Legal notice

This tool is intended for removing DRM from ebooks you have legitimately borrowed or purchased, for personal use only. Circumventing DRM may be restricted in your jurisdiction. Use responsibly.

The DRM removal is performed by [DeDRM_tools](https://github.com/noDRM/DeDRM_tools) (fetched at setup time), which is licensed separately under GPL v3.

## License

MIT — see [LICENSE](LICENSE).
