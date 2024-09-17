# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['BookPreviewer.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/*', './resources')],
    hiddenimports=['re','PyQt5.QtWidgets','PyQt5.QtCore','PyQt5.QtGui','datetime','csv'],
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
    name='BookPreviewer',
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
    icon='resources/smartphone.png'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    a.zipfiles,
    a.scripts,
    a.binaries,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BookPreviewer'
)