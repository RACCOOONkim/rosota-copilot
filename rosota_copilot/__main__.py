#!/usr/bin/env python3
"""
Rosota Copilot 메인 진입점
PyInstaller로 패키징할 때 사용
"""
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

# 패키징된 경우 (PyInstaller 또는 py2app) 리소스 경로 조정
if getattr(sys, 'frozen', False):
    # PyInstaller로 패키징된 경우
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
    else:
        # py2app으로 패키징된 경우
        base_path = Path(sys.executable).parent.parent / 'Resources'
    templates_dir = base_path / 'templates'
    static_dir = base_path / 'static'
    resources_dir = base_path / 'resources'
else:
    # 일반 실행
    base_path = Path(__file__).parent
    templates_dir = base_path / 'templates'
    static_dir = base_path / 'static'
    resources_dir = base_path / 'resources'

# 경로를 환경 변수로 설정 (server.py에서 사용)
os.environ['ROSOTA_TEMPLATES_DIR'] = str(templates_dir)
os.environ['ROSOTA_STATIC_DIR'] = str(static_dir)
os.environ['ROSOTA_RESOURCES_DIR'] = str(resources_dir)

def open_browser():
    """서버 시작 후 브라우저 자동 열기"""
    time.sleep(2)  # 서버 시작 대기
    url = "http://localhost:8000"
    print(f"\n🌐 브라우저를 열고 있습니다: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️  브라우저를 자동으로 열 수 없습니다: {e}")
        print(f"   수동으로 {url} 에 접속하세요.")

def main():
    """메인 함수"""
    # GUI 앱으로 실행되는 경우 콘솔 출력 최소화
    # py2app 또는 PyInstaller로 패키징된 경우
    is_gui_app = getattr(sys, 'frozen', False)
    
    if not is_gui_app:
        print("=" * 60)
        print("Rosota Copilot")
        print("=" * 60)
        print(f"Python: {sys.version}")
        print(f"기본 경로: {base_path}")
        print(f"템플릿: {templates_dir}")
        print(f"정적 파일: {static_dir}")
        print("=" * 60)
    
    # 브라우저 자동 열기 (백그라운드 스레드)
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # 서버 시작
    import uvicorn
    from rosota_copilot.server import asgi
    
    host = os.environ.get("HOST", "127.0.0.1")  # 기본값을 localhost로 변경
    port = int(os.environ.get("PORT", "8000"))
    
    if not is_gui_app:
        print(f"\n🚀 서버 시작 중...")
        print(f"   주소: http://{host}:{port}")
        print(f"   종료: Ctrl+C\n")
    
    try:
        uvicorn.run(
            asgi,
            host=host,
            port=port,
            log_level="info" if not is_gui_app else "warning",  # GUI 앱에서는 로그 최소화
            factory=True
        )
    except KeyboardInterrupt:
        if not is_gui_app:
            print("\n\n서버를 종료합니다...")
    except Exception as e:
        if not is_gui_app:
            print(f"\n❌ 서버 시작 실패: {e}")
            import traceback
            traceback.print_exc()
        # GUI 앱에서는 에러 다이얼로그 표시
        if is_gui_app:
            try:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Rosota Copilot 오류", f"서버 시작 실패:\n{e}")
            except:
                pass
        sys.exit(1)

if __name__ == '__main__':
    main()

