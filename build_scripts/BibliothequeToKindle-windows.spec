# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
datas_dnd, binaries_dnd, hiddenimports_dnd = collect_all("tkinterdnd2")

a = Analysis(
    [os.path.join(ROOT, "src", "app.py")],
    pathex=[os.path.join(ROOT, "src")],
    binaries=binaries_dnd,
    datas=[(os.path.join(ROOT, "src", "dedrm"), "dedrm")] + datas_dnd,
    hiddenimports=[
        "tkinter", "tkinter.ttk", "tkinter.filedialog",
        "tkinter.scrolledtext", "tkinter.messagebox",
        "Crypto", "Crypto.Cipher", "Crypto.Util",
        "lxml", "lxml.etree",
        "ctypes", "ctypes.wintypes",
    ] + hiddenimports_dnd,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="BibliothequeToKindle",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join(ROOT, "src", "icon.ico"),
)
