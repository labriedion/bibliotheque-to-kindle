# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas_dnd, binaries_dnd, hiddenimports_dnd = collect_all("tkinterdnd2")

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries_dnd,
    datas=[("dedrm/__init__.py", "dedrm")] + datas_dnd,
    hiddenimports=[
        "tkinter", "tkinter.ttk", "tkinter.filedialog",
        "tkinter.scrolledtext", "tkinter.messagebox",
        "Crypto", "Crypto.Cipher", "Crypto.Util",
        "lxml", "lxml.etree",
        "keyring", "keyring.backends.macOS",
        "PIL", "PIL.Image", "PIL.ImageDraw",
    ] + hiddenimports_dnd,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="KindleConverter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=True,
    name="KindleConverter",
)

app = BUNDLE(
    coll,
    name="Kindle Converter.app",
    icon="icon.icns",
    bundle_identifier="com.kindleconverter.app",
    info_plist={
        "CFBundleName":             "Kindle Converter",
        "CFBundleDisplayName":      "Kindle Converter",
        "CFBundleShortVersionString": "1.0",
        "CFBundleVersion":          "1.0",
        "NSHighResolutionCapable":  True,
        "LSMinimumSystemVersion":   "10.13",
    },
)
