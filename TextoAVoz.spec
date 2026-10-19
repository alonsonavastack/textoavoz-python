# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files
import sys
import os

block_cipher = None

datas = [
    ('configuraciones.json', '.'),
    ('assets', 'assets'),
]

binaries = []
hiddenimports = [
    'scipy.signal',
    'scipy.special',
    'scipy.linalg',
    'multiprocessing',
    'asyncio',
    'edge_tts',
    'sounddevice',
    'soundfile',
]

# Recolectar datos y dependencias de librerías críticas
for pkg in ['customtkinter', 'soundfile', 'sounddevice', 'edge_tts', '_soundfile_data']:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# Eliminar duplicados en hiddenimports
hiddenimports = list(set(hiddenimports))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='TextoAVoz',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'] if os.path.exists('assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TextoAVoz',
)
