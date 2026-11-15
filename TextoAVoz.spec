# -*- mode: python ; coding: utf-8 -*-
# Genera dos ejecutables en la misma carpeta (dist/TextoAVoz):
#   TextoAVoz.exe     -> la aplicación de escritorio (ventana)
#   TextoAVozMCP.exe  -> el conector para Claude Code (consola: MCP habla por stdin/stdout)
from PyInstaller.utils.hooks import collect_all
import sys
import os

block_cipher = None

COMUNES = [
    'scipy.signal', 'scipy.special', 'scipy.linalg',
    'multiprocessing', 'asyncio', 'edge_tts', 'soundfile', 'voz_core',
]
PKGS_COMUNES = ['soundfile', 'edge_tts', '_soundfile_data']
PKGS_APP = ['customtkinter', 'sounddevice']
PKGS_MCP = [
    'mcp', 'pydantic', 'pydantic_core', 'pydantic_settings', 'anyio', 'httpx', 'httpx_sse', 'httpcore',
    'starlette', 'uvicorn', 'sse_starlette', 'jsonschema', 'jsonschema_specifications', 'referencing',
    'rpds', 'h11', 'click', 'certifi', 'idna', 'sniffio', 'multipart', 'typing_inspection',
    'annotated_types', 'jwt', 'cryptography',
]

def recolectar(paquetes):
    datas, binaries, hidden = [], [], []
    for pkg in paquetes:
        try:
            d, b, h = collect_all(pkg)
            datas += d
            binaries += b
            hidden += h
        except Exception:
            pass
    return datas, binaries, hidden

icono = ['assets/icon.ico'] if os.path.exists('assets/icon.ico') else None

# ── Aplicación de escritorio ─────────────────────────────────────────────────
d1, b1, h1 = recolectar(PKGS_COMUNES + PKGS_APP)
a_app = Analysis(
    ['app.py'],
    pathex=[],
    binaries=b1,
    datas=[('configuraciones.json', '.'), ('assets', 'assets')] + d1,
    hiddenimports=list(set(COMUNES + ['sounddevice'] + h1)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_app = PYZ(a_app.pure, a_app.zipped_data, cipher=block_cipher)
exe_app = EXE(
    pyz_app,
    a_app.scripts,
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
    icon=icono,
)

# ── Conector MCP para Claude Code ────────────────────────────────────────────
d2, b2, h2 = recolectar(PKGS_COMUNES + PKGS_MCP)
a_mcp = Analysis(
    ['mcp_server.py'],
    pathex=[],
    binaries=b2,
    datas=d2,
    hiddenimports=list(set(COMUNES + h2)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['customtkinter', 'tkinter', 'sounddevice'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_mcp = PYZ(a_mcp.pure, a_mcp.zipped_data, cipher=block_cipher)
exe_mcp = EXE(
    pyz_mcp,
    a_mcp.scripts,
    [],
    exclude_binaries=True,
    name='TextoAVozMCP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icono,
)

# Una sola carpeta con los dos ejecutables y las librerías compartidas
coll = COLLECT(
    exe_app,
    exe_mcp,
    a_app.binaries, a_app.zipfiles, a_app.datas,
    a_mcp.binaries, a_mcp.zipfiles, a_mcp.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TextoAVoz',
)

# En macOS se empaqueta ademas como TextoAVoz.app (el conector queda en Contents/MacOS/TextoAVozMCP)
if sys.platform == 'darwin':
    app_mac = BUNDLE(
        coll,
        name='TextoAVoz.app',
        icon='assets/icon.icns' if os.path.exists('assets/icon.icns') else None,
        bundle_identifier='com.alonsonavastack.textoavoz',
        info_plist={
            'CFBundleName': 'Texto a Voz Studio',
            'CFBundleDisplayName': 'Texto a Voz Studio',
            'NSHighResolutionCapable': True,
        },
    )
