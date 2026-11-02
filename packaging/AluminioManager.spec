# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

BASE = os.path.abspath(SPECPATH)
ROOT = os.path.dirname(BASE)

datas, binaries, hiddenimports = [], [], []
for pacote in ("pyhanko", "pyhanko_certvalidator", "matplotlib", "mysql.connector"):
    try:
        d, b, h = collect_all(pacote)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

if os.path.exists(os.path.join(ROOT, "credentials.json")):
    datas.append((os.path.join(ROOT, "credentials.json"), "."))

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AluminioManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(BASE, "aluminio.ico"),
)
