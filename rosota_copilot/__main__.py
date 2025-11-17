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

# loguru 초기화 (PyInstaller 환경에서 포매터 오류 방지)
# 패키지 import 전에 초기화하여 모든 모듈에서 일관된 설정 사용
import os

# PyInstaller로 빌드된 경우 sys.stderr가 None일 수 있으므로 처리
if getattr(sys, 'frozen', False):
    # windowed 모드에서 sys.stderr가 None인 경우 파일로 리디렉션
    if sys.stderr is None:
        try:
            log_dir = Path(sys.executable).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'app.log'
            sys.stderr = open(str(log_file), 'w', encoding='utf-8')
        except Exception:
            # 파일 생성 실패 시 devnull로 리디렉션
            sys.stderr = open(os.devnull, 'w')
    
    if sys.stdout is None:
        try:
            log_dir = Path(sys.executable).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'app.log'
            sys.stdout = open(str(log_file), 'w', encoding='utf-8')
        except Exception:
            sys.stdout = open(os.devnull, 'w')

try:
    from loguru import logger
    
    # 모든 기존 핸들러 제거 시도
    try:
        logger.remove()  # 기본 핸들러 제거
    except (ValueError, AttributeError, TypeError):
        # 핸들러가 없거나 이미 제거된 경우 무시
        pass
    
    # 출력 스트림 결정 (sys.stderr가 None이 아닌 경우에만 사용)
    if sys.stderr is not None and not (hasattr(sys.stderr, 'closed') and sys.stderr.closed):
        # 간단한 포매터로 새 핸들러 추가
        logger.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="INFO",
            colorize=False,  # 색상 비활성화로 추가 오류 방지
            enqueue=False    # 큐 비활성화로 추가 오류 방지
        )
    else:
        # sys.stderr를 사용할 수 없는 경우 파일로 로깅
        try:
            if getattr(sys, 'frozen', False):
                log_dir = Path(sys.executable).parent / 'logs'
            else:
                try:
                    log_dir = Path(__file__).parent / 'logs'
                except NameError:
                    # __file__이 없는 경우 현재 작업 디렉토리 사용
                    log_dir = Path.cwd() / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'app.log'
            logger.add(
                str(log_file),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
                level="INFO",
                rotation="10 MB",
                retention="7 days"
            )
        except Exception:
            # 파일 로깅도 실패하면 devnull로
            logger.add(
                os.devnull,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
                level="INFO"
            )
except Exception as e:
    # loguru 초기화 실패 시에도 계속 진행
    # 표준 logging으로 대체
    import logging
    try:
        if getattr(sys, 'frozen', False):
            log_dir = Path(sys.executable).parent / 'logs'
        else:
            try:
                log_dir = Path(__file__).parent / 'logs'
            except NameError:
                # __file__이 없는 경우 현재 작업 디렉토리 사용
                log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / 'app.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[logging.FileHandler(str(log_file), encoding='utf-8')]
        )
    except Exception:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    # print는 사용하지 않음 (sys.stdout이 None일 수 있음)

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

