# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['assistant.py'],
    pathex=['.runtime_deps'],
    binaries=[],
    datas=[
        ('programs.json', '.'),
        ('assets/pet', 'assets/pet'),
        ('assets/icons', 'assets/icons'),
        ('qml', 'qml'),
    ],
    hiddenimports=[
        'PySide6.QtNetwork',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtSvg',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PIL', 'numpy'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='JARVIS',
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
)
