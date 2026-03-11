#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
특허 문서 변환기 - 올인원 실행 파일
Word/HWP/PDF → HLT 형식 변환

더블클릭으로 실행하세요!
"""

import os
import sys
import subprocess
import time
import webbrowser
import socket

def find_free_port():
    """사용 가능한 포트 찾기"""
    for port in range(5000, 5100):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except:
            continue
    return 5000

def install_dependencies():
    """필요한 라이브러리 설치"""
    print("=" * 70)
    print("특허 문서 변환기 (Patent Document Converter)")
    print("Word/HWP/PDF → HLT 변환")
    print("=" * 70)
    print()

    packages = [
        'flask',
        'flask-cors',
        'python-docx',
        'lxml',
        'olefile',
        'PyPDF2',
        'pdf2image',
    ]

    print("필요한 프로그램 확인 중...")
    print()

    missing = []
    for package in packages:
        module_name = package.replace('-', '_').split('[')[0]
        try:
            __import__(module_name)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - 설치 필요")
            missing.append(package)

    if missing:
        print()
        print("=" * 70)
        print("필요한 프로그램 설치 중... (처음 한 번만 실행됩니다)")
        print("=" * 70)
        print()

        for package in missing:
            print(f"설치 중: {package}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install',
                    package, '--quiet'
                ])
                print(f"✓ {package} 설치 완료")
            except Exception as e:
                print(f"⚠️  {package} 설치 중 오류: {e}")

        print()
        print("✓ 모든 프로그램 설치 완료!")
        print()
    else:
        print()
        print("✓ 모든 프로그램이 이미 설치되어 있습니다")
        print()

def download_files():
    """필요한 파일 다운로드"""
    print("=" * 70)
    print("변환기 파일 확인 중...")
    print("=" * 70)
    print()

    files_needed = {
        'app.py': 'https://raw.githubusercontent.com/ilrdeept2-netizen/test1/claude/patent-format-converter-9SMxa/app.py',
        'patent_format_converter.py': 'https://raw.githubusercontent.com/ilrdeept2-netizen/test1/claude/patent-format-converter-9SMxa/patent_format_converter.py',
        'templates/index.html': 'https://raw.githubusercontent.com/ilrdeept2-netizen/test1/claude/patent-format-converter-9SMxa/templates/index.html'
    }

    import urllib.request

    for filename, url in files_needed.items():
        if os.path.exists(filename):
            print(f"✓ {filename} 있음")
        else:
            print(f"다운로드 중: {filename}...")
            try:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                urllib.request.urlretrieve(url, filename)
                print(f"✓ {filename} 다운로드 완료")
            except Exception as e:
                print(f"⚠️  {filename} 다운로드 실패: {e}")

    print()

def start_web_server():
    """웹 서버 시작"""
    print("=" * 70)
    print("웹 서버 시작 중...")
    print("=" * 70)
    print()

    port = find_free_port()
    url = f'http://127.0.0.1:{port}'

    print(f"서버 주소: {url}")
    print()
    print("✓ 브라우저가 3초 후 자동으로 열립니다")
    print()
    print("사용 방법:")
    print("  1. 브라우저에서 Word 파일을 드래그 앤 드롭")
    print("  2. 자동으로 HLT 파일 다운로드")
    print("  3. K-Editor에서 HLT 파일 열기")
    print()
    print("=" * 70)
    print()
    print("서버를 종료하려면 이 창을 닫으세요")
    print()

    # 브라우저 자동 열기
    def open_browser():
        time.sleep(3)
        try:
            webbrowser.open(url)
            print("✓ 브라우저 열림")
        except:
            print(f"브라우저를 수동으로 여세요: {url}")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Flask 앱 실행
    try:
        from app import app
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        input("\n아무 키나 눌러 종료...")
        sys.exit(1)

def main():
    """메인 함수"""
    try:
        # 1. 의존성 설치
        install_dependencies()

        # 2. 파일 다운로드
        download_files()

        # 3. 서버 시작
        start_web_server()

    except KeyboardInterrupt:
        print()
        print()
        print("=" * 70)
        print("프로그램 종료")
        print("=" * 70)
        sys.exit(0)
    except Exception as e:
        print()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        print()
        input("아무 키나 눌러 종료...")
        sys.exit(1)

if __name__ == '__main__':
    main()
