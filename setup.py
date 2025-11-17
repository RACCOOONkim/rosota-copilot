"""
Rosota Copilot macOS 앱 빌드 설정
py2app을 사용하여 .app 번들 생성
"""
# Python 3.12+ 호환성: setuptools만 사용
try:
    from setuptools import setup
except ImportError:
    # Python 3.12+에서는 setuptools가 distutils를 대체
    import sys
    print("❌ setuptools가 필요합니다. 다음 명령어를 실행하세요:")
    print("   pip install --upgrade setuptools")
    sys.exit(1)

from pathlib import Path

# 데이터 파일 자동 수집
def collect_data_files():
    """데이터 파일 자동 수집"""
    data_files = []
    
    # templates 폴더 전체
    templates_dir = Path('rosota_copilot/templates')
    if templates_dir.exists():
        templates_files = []
        for file in templates_dir.rglob('*'):
            if file.is_file():
                templates_files.append(str(file))
        if templates_files:
            data_files.append(('templates', templates_files))
    
    # static 폴더 전체
    static_dir = Path('rosota_copilot/static')
    if static_dir.exists():
        static_files = []
        for file in static_dir.rglob('*'):
            if file.is_file():
                static_files.append(str(file))
        if static_files:
            data_files.append(('static', static_files))
    
    # resources 폴더 전체
    resources_dir = Path('rosota_copilot/resources')
    if resources_dir.exists():
        resources_files = []
        for file in resources_dir.rglob('*'):
            if file.is_file():
                resources_files.append(str(file))
        if resources_files:
            data_files.append(('resources', resources_files))
    
    return data_files

APP = ['rosota_copilot/__main__.py']
DATA_FILES = collect_data_files()

OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'uvicorn',
        'fastapi',
        'starlette',
        'socketio',
        'engineio',
        'pydantic',
        'jinja2',
        'serial',
        'feetech_servo_sdk',
        'numpy',
        'loguru',
        'rosota_copilot',
    ],
    'includes': [
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'serial.tools',
        'serial.tools.list_ports',
    ],
    'excludes': [
        'matplotlib',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
    ],
    'iconfile': None,  # 아이콘 파일이 있으면 경로 지정
    'plist': {
        'CFBundleName': 'Rosota Copilot',
        'CFBundleDisplayName': 'Rosota Copilot',
        'CFBundleGetInfoString': 'SO Arm 100/101 제어 시스템',
        'CFBundleIdentifier': 'com.rosota.copilot',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13',
    },
}

setup(
    app=APP,
    name='Rosota Copilot',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

