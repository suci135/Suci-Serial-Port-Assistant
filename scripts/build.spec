# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None
# PyInstaller executes spec files with SPECPATH instead of __file__.
ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'src/resource/*.png'), 'src/resource'),
        (str(ROOT / 'src/resource/*.ttf'), 'src/resource'),
        (str(ROOT / 'quick_commands.json'), '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'qasync',
        'asyncio',
        'bleak',
        'bleak.backends',
        'bleak.backends.winrt',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Suci串口助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'src/resource/Assistant.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Suci串口助手',
)
