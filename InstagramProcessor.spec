# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all necessary hidden imports
hidden_imports = [
    'playwright',
    'playwright.sync_api',
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'logging',
    'requests',
    'yt_dlp',
]

# Collect all the data files needed
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
]

a = Analysis(
    ['utils\main.py'],  # Your main script
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'playwright.browsers',  # Exclude the browser files
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unnecessary modules to reduce size
excluded_binaries = [
    'playwright/driver',
    'playwright/browsers',
    'tensorflow',
    'torch',
    'cv2',
]

a.binaries = TOC([x for x in a.binaries if not any(
    excluded in x[0] for excluded in excluded_binaries
)])

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='InstagramProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True if you want to see console output for debugging
    icon='static/icon.ico',  # Add your icon file path here
    
)