# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
package_name = os.environ.get(
    "JSMW_PACKAGE_NAME",
    "JapaneseStrokeMouseWriter-v2.7.1-win-x64-portable",
)

a = Analysis(
    [str(root / "mouse_writer_ui.pyw")],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "data"), "data"), *collect_data_files("ttkbootstrap")],
    hiddenimports=["svg.path", "pyautogui", "ttkbootstrap"],
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
    icon=str(root / "data" / "ui" / "JapaneseStrokeMouseWriter.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=package_name,
)

