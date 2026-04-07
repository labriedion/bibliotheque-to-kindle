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
        "keyring", "keyring.backends.Windows",
        "win32api", "win32con", "win32cred",
        "smtplib", "email", "email.mime.multipart",
        "email.mime.base", "email.mime.text", "email.encoders",
    ] + hiddenimports_dnd,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="KindleConverter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no terminal window
    icon="icon.ico",        # convert icon.png to .ico before building
)
