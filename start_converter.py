#!/usr/bin/env python3
"""
특허 문서 변환기 실행 파일
더블클릭으로 실행하세요!
"""

import os
import sys
import time
import webbrowser
from pathlib import Path
import subprocess

def check_dependencies():
    """필요한 라이브러리가 설치되어 있는지 확인"""
    print("=" * 60)
    print("특허 문서 변환기 시작 중...")
    print("Patent Document Converter Starting...")
    print("=" * 60)
    print()

    # 필요한 모듈 확인
    required_modules = {
        'flask': 'Flask',
        'docx': 'python-docx',
        'lxml': 'lxml'
    }

    missing = []
    for module, package in required_modules.items():
        try:
            __import__(module)
            print(f"✓ {package} 설치됨")
        except ImportError:
            print(f"✗ {package} 필요")
            missing.append(package)

    if missing:
        print()
        print("=" * 60)
        print("⚠️  필요한 라이브러리를 설치합니다...")
        print("=" * 60)
        print()

        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print()
            print("✓ 설치 완료!")
            print()
        except Exception as e:
            print(f"❌ 설치 실패: {e}")
            print()
            print("수동으로 설치하려면 다음 명령어를 실행하세요:")
            print("pip install -r requirements.txt")
            input("\n아무 키나 눌러 종료...")
            sys.exit(1)

def start_server():
    """Flask 서버 시작"""
    print("=" * 60)
    print("🚀 웹 서버 시작 중...")
    print("=" * 60)
    print()

    # Flask 앱 임포트
    try:
        from app import app

        # 포트 찾기
        port = 5000
        print(f"서버 주소: http://localhost:{port}")
        print()
        print("브라우저가 자동으로 열립니다...")
        print("(안 열리면 위 주소를 복사해서 브라우저에 붙여넣으세요)")
        print()
        print("=" * 60)
        print()

        # 브라우저 자동 열기 (3초 후)
        def open_browser():
            time.sleep(3)
            webbrowser.open(f'http://localhost:{port}')

        import threading
        threading.Thread(target=open_browser, daemon=True).start()

        # 서버 실행
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        print()
        input("아무 키나 눌러 종료...")
        sys.exit(1)

def main():
    """메인 함수"""
    try:
        # 의존성 확인
        check_dependencies()

        # 서버 시작
        start_server()

    except KeyboardInterrupt:
        print()
        print()
        print("=" * 60)
        print("서버를 종료합니다...")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        input("\n아무 키나 눌러 종료...")
        sys.exit(1)

if __name__ == '__main__':
    main()
