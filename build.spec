# -*- mode: python ; coding: utf-8 -*-
import os
import sys

sys.path.insert(0, r'E:\LocalRepository\Project26.4\pyflow\venv_build\Lib\site-packages')

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = collect_data_files('pynput')
subms = collect_submodules('pynput')

hiddenimports = subms + [
    'pynput',
    'pynput.mouse',
    'pynput.keyboard',
    'pynput._info',
    'pynput._util',
    'pynput._util.win32',
    'pynput.mouse._base',
    'pynput.mouse._win32',
    'pynput.keyboard._base',
    'pynput.keyboard._win32',
    'pygetwindow',
    'pyautogui',
    'pyperclip',
]

a = Analysis(
    ['main.py'],
    pathex=[r'E:\LocalRepository\Project26.4\pyflow\venv_build\Lib\site-packages'],
    binaries=[],
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
    name='PyFlow',
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
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PyFlow_v32',
)
