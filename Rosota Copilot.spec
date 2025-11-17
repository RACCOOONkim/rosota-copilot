# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('rosota_copilot/templates', 'templates'), ('rosota_copilot/static', 'static'), ('rosota_copilot/resources', 'resources')]
binaries = []
hiddenimports = ['socketio.async_server', 'socketio.asgi', 'uvicorn', 'fastapi', 'starlette', 'engineio', 'pydantic', 'jinja2', 'serial', 'serial.tools.list_ports', 'feetech_servo_sdk', 'numpy', 'loguru']
tmp_ret = collect_all('uvicorn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('fastapi')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('socketio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['rosota_copilot/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='Rosota Copilot',
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
    name='Rosota Copilot',
)
app = BUNDLE(
    coll,
    name='Rosota Copilot.app',
    icon=None,
    bundle_identifier=None,
)
