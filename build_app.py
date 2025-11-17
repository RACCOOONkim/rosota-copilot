#!/usr/bin/env python3
"""
Rosota Copilot macOS 앱 빌드 스크립트
PyInstaller를 사용하여 단일 실행 파일로 패키징
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_dependencies():
    """필요한 패키지가 설치되어 있는지 확인"""
    try:
        import PyInstaller
        print("✓ PyInstaller 설치됨")
    except ImportError:
        print("❌ PyInstaller가 설치되지 않았습니다.")
        print("설치 중: pip install pyinstaller")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller 설치 완료")

def create_spec_file():
    """PyInstaller spec 파일 생성"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['rosota_copilot/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('rosota_copilot/templates', 'templates'),
        ('rosota_copilot/static', 'static'),
        ('rosota_copilot/resources', 'resources'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.auto',
        'socketio',
        'engineio',
        'fastapi',
        'starlette',
        'pydantic',
        'jinja2',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'feetech_servo_sdk',
        'numpy',
        'loguru',
    ],
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
    name='RosotaCopilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 디버깅을 위해 콘솔 표시
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일이 있으면 여기에 경로 지정
)
'''
    
    spec_path = Path('RosotaCopilot.spec')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✓ Spec 파일 생성: {spec_path}")
    return spec_path

def build_app():
    """앱 빌드"""
    print("\n🔨 앱 빌드 시작...")
    
    # 빌드 디렉토리 정리
    build_dir = Path('build')
    dist_dir = Path('dist')
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # PyInstaller 실행
    spec_file = create_spec_file()
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        str(spec_file)
    ]
    
    print(f"실행 명령: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    print("\n✓ 빌드 완료!")
    print(f"실행 파일 위치: {dist_dir / 'RosotaCopilot'}")
    
    return dist_dir / 'RosotaCopilot'

def create_dmg(app_path):
    """DMG 파일 생성 (선택사항)"""
    print("\n📦 DMG 생성 중...")
    
    dmg_name = "RosotaCopilot.dmg"
    dmg_path = Path(dmg_name)
    
    if dmg_path.exists():
        dmg_path.unlink()
    
    # create-dmg가 설치되어 있는지 확인
    try:
        subprocess.check_call(['which', 'create-dmg'], stdout=subprocess.DEVNULL)
        has_create_dmg = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        has_create_dmg = False
        print("⚠️  create-dmg가 설치되지 않았습니다.")
        print("   DMG 생성을 원하면 다음 명령으로 설치하세요:")
        print("   brew install create-dmg")
    
    if has_create_dmg:
        # 임시 디렉토리 생성
        temp_dir = Path('dmg_temp')
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        # .app 번들 생성
        app_name = "RosotaCopilot.app"
        app_bundle = temp_dir / app_name
        create_app_bundle(app_path, app_bundle)
        
        # DMG 생성
        cmd = [
            'create-dmg',
            '--volname', 'Rosota Copilot',
            '--window-pos', '200', '120',
            '--window-size', '600', '400',
            '--icon-size', '100',
            '--icon', app_name, '175', '190',
            '--hide-extension', app_name,
            '--app-drop-link', '425', '190',
            str(dmg_path),
            str(temp_dir)
        ]
        
        subprocess.check_call(cmd)
        
        # 정리
        shutil.rmtree(temp_dir)
        
        print(f"✓ DMG 생성 완료: {dmg_path}")
    else:
        print("\n💡 수동 DMG 생성 방법:")
        print("1. Disk Utility를 엽니다")
        print("2. File > New Image > Image from Folder")
        print(f"3. '{app_path.parent}' 폴더 선택")
        print("4. 읽기/쓰기 형식으로 저장")
        print(f"5. 생성된 이미지를 '{dmg_name}'로 이름 변경")

def create_app_bundle(executable_path, app_bundle_path):
    """macOS .app 번들 생성"""
    print(f"\n📱 .app 번들 생성: {app_bundle_path}")
    
    # .app 구조 생성
    if app_bundle_path.exists():
        shutil.rmtree(app_bundle_path)
    app_bundle_path.mkdir(parents=True, exist_ok=True)
    contents_dir = app_bundle_path / 'Contents'
    contents_dir.mkdir()
    macos_dir = contents_dir / 'MacOS'
    macos_dir.mkdir()
    resources_dir = contents_dir / 'Resources'
    resources_dir.mkdir()
    
    # Info.plist 생성
    info_plist = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>RosotaCopilot</string>
    <key>CFBundleIdentifier</key>
    <string>com.rosota.copilot</string>
    <key>CFBundleName</key>
    <string>Rosota Copilot</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
'''
    with open(contents_dir / 'Info.plist', 'w') as f:
        f.write(info_plist)
    
    # 실행 파일을 MacOS 디렉토리로 복사
    launcher = macos_dir / 'RosotaCopilot'
    shutil.copy2(executable_path, launcher)
    
    # 실행 권한 부여
    os.chmod(launcher, 0o755)
    
    print(f"✓ .app 번들 생성 완료: {app_bundle_path}")
    return app_bundle_path

def main():
    """메인 함수"""
    print("=" * 60)
    print("Rosota Copilot macOS 앱 빌드")
    print("=" * 60)
    
    # 의존성 확인
    check_dependencies()
    
    # 빌드
    app_path = build_app()
    
    # DMG 생성 (선택사항)
    create_dmg = input("\nDMG 파일을 생성하시겠습니까? (y/N): ").strip().lower()
    if create_dmg == 'y':
        create_dmg(app_path)
    
    print("\n" + "=" * 60)
    print("✅ 빌드 완료!")
    print(f"실행 파일: {app_path}")
    print("\n실행 방법:")
    print(f"  ./{app_path}")
    print("=" * 60)

if __name__ == '__main__':
    main()

