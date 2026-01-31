#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국특허서식 변환기 웹 서버 시작 스크립트
Easy Start Script for Korean Patent Converter Web Server
"""

import subprocess
import sys
import os
import webbrowser
import time
import socket

def check_port(port):
    """포트 사용 가능 여부 확인"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        return True
    except:
        return False
    finally:
        sock.close()

def install_dependencies():
    """필요한 패키지 설치"""
    packages = [
        'flask',
        'flask-cors',
        'python-docx',
        'PyPDF2',
        'olefile',
        'lxml'
    ]

    print("필요한 패키지를 확인하고 설치합니다...")
    for package in packages:
        try:
            __import__(package.replace('-', '_').split('[')[0])
        except ImportError:
            print(f"  설치 중: {package}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
    print("패키지 설치 완료!")
    print()

def main():
    print()
    print("=" * 60)
    print("  한국특허서식 변환기 웹 서버")
    print("  HWP/DOCX/PDF → HLT 변환")
    print("=" * 60)
    print()

    # 의존성 설치
    try:
        install_dependencies()
    except Exception as e:
        print(f"패키지 설치 중 오류: {e}")
        print("수동으로 설치하세요: pip install flask flask-cors python-docx PyPDF2 olefile lxml")
        print()

    # 포트 확인
    port = 5000
    if not check_port(port):
        for p in range(5001, 5100):
            if check_port(p):
                port = p
                break
        else:
            print("사용 가능한 포트를 찾을 수 없습니다.")
            sys.exit(1)

    url = f"http://localhost:{port}"
    print(f"서버를 시작합니다: {url}")
    print()
    print("잠시 후 브라우저가 자동으로 열립니다...")
    print("종료하려면 Ctrl+C를 누르세요.")
    print()

    # 브라우저 열기 (서버 시작 후 1.5초)
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # 서버 시작
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, 'korean_patent_converter_web.py')

    try:
        subprocess.run([
            sys.executable,
            server_script,
            '-p', str(port)
        ])
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")

if __name__ == '__main__':
    main()
