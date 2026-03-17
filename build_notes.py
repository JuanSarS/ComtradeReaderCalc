# PyInstaller Build Script
# =========================
# This script can be used to package the application with PyInstaller
#
# Usage:
#   1. Install PyInstaller: pip install pyinstaller
#   2. Run this file: python build_spec.py
#   3. Or use directly: pyinstaller comtrade_tool.spec

# To create initial spec file:
# pyinstaller --name="COMTRADEPro" --windowed --onefile src/main.py

# Basic PyInstaller command for manual build:
# pyinstaller --windowed --onefile --name="COMTRADEPro" ^
#     --add-data="README.md;." ^
#     --add-data="dash_app\assets;dash_app\assets" ^
#     --hidden-import=PyQt6 ^
#     --hidden-import=PyQt6.QtWebEngineWidgets ^
#     --hidden-import=PyQt6.QtWebEngineCore ^
#     --hidden-import=dash ^
#     --hidden-import=plotly ^
#     --hidden-import=scipy ^
#     src/main.py

# Spec file template (comtrade_tool.spec) - create this for advanced builds
"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('README.md', '.'), ('dash_app/assets', 'dash_app/assets')],
    hiddenimports=['PyQt6', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore', 'matplotlib', 'dash', 'plotly', 'scipy', 'numpy', 'pandas'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='COMTRADEPro',
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
    icon='icon.ico'  # Add your icon file here
)
"""

# Instructions:
# 1. Save the spec template above as 'comtrade_tool.spec'
# 2. Customize paths and options as needed
# 3. Run: pyinstaller comtrade_tool.spec
# 4. Executable will be in dist/ folder
