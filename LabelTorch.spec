# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['labeltorch\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('labeltorch\\app\\infra\\db\\migrations', 'labeltorch\\app\\infra\\db\\migrations')],
    hiddenimports=['labeltorch.app.infra.db.migrations.v001_initial', 'labeltorch.app.domain.enums', 'ultralytics', 'ultralytics.nn', 'ultralytics.models', 'ultralytics.engine', 'PIL', 'PIL.Image'],
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
    name='LabelTorch',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LabelTorch',
)
