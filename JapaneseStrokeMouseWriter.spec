# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

root = Path(SPECPATH)

a = Analysis(
    [str(root / "mouse_writer_ui.pyw")],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "data"), "data")],
    hiddenimports=["svg.path", "pyautogui"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JapaneseStrokeMouseWriter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="JapaneseStrokeMouseWriter-v2.0.2-win-x64-portable",
)
