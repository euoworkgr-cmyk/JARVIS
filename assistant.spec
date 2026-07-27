# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['assistant.py'],
    pathex=['.runtime_deps'],
    binaries=[('.runtime_deps/numpy.libs/*.dll', '.')],
    datas=[
        ('programs.json', '.'),
        ('assets/pet', 'assets/pet'),
        ('assets/icons', 'assets/icons'),
        ('qml', 'qml'),
        ('models', 'models'),
        ('tools/whisper.cpp/Release', 'tools/whisper.cpp/Release'),
    ],
    hiddenimports=[
        'PySide6.QtNetwork',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickControls2',
        'PySide6.QtSvg',
        'PySide6.QtWidgets',
        'numpy',
        'onnxruntime',
        'openwakeword.model',
        'scipy.signal',
        'sounddevice',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PIL', 'tkinter', '_tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='assistant',
    exclude_binaries=True,
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

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='assistant',
)
