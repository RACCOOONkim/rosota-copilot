# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('templates', 'templates'), ('static', 'static')]
binaries = []
hiddenimports = ['socketio', 'socketio.async_server', 'socketio.asgi', 'socketio.client', 'socketio.server', 'engineio', 'engineio.async_drivers', 'engineio.async_drivers.asgi', 'uvicorn', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'fastapi', 'fastapi.middleware', 'fastapi.middleware.cors', 'starlette', 'starlette.applications', 'starlette.routing', 'starlette.responses', 'starlette.middleware', 'starlette.middleware.cors', 'pydantic', 'jinja2', 'serial', 'serial.tools', 'serial.tools.list_ports', 'scservo_sdk', 'scservo_sdk.port_handler', 'scservo_sdk.packet_handler', 'scservo_sdk.group_sync_write', 'scservo_sdk.group_sync_read', 'numpy', 'loguru', 'dotenv', 'requests']
tmp_ret = collect_all('uvicorn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('fastapi')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('socketio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('engineio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('loguru')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'torchaudio', 'tensorflow', 'pandas', 'scipy', 'matplotlib', 'bokeh', 'plotly', 'IPython', 'jupyter', 'notebook', 'sphinx', 'pytest', 'black', 'sklearn', 'skimage', 'dask', 'distributed'],
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
