#!/usr/bin/env python3
"""
선행특허조사 앱 실행 스크립트
============================
필요한 패키지를 자동 설치하고 웹 앱을 실행합니다.
"""

import subprocess
import sys
import os


def check_and_install_packages():
    """필요한 패키지 확인 및 설치"""
    required_packages = {
        'streamlit': 'streamlit',
        'python-docx': 'docx',
        'PyPDF2': 'PyPDF2',
        'python-pptx': 'pptx',
        'openpyxl': 'openpyxl',
        'olefile': 'olefile',
    }

    missing_packages = []

    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        print("📦 필요한 패키지를 설치합니다...")
        print(f"   설치할 패키지: {', '.join(missing_packages)}")

        for package in missing_packages:
            print(f"   ⏳ {package} 설치 중...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', package, '-q'
            ])
            print(f"   ✅ {package} 설치 완료")

        print("✅ 모든 패키지가 설치되었습니다!\n")


def run_streamlit_app():
    """Streamlit 앱 실행"""
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patent_search_web.py')

    if not os.path.exists(app_path):
        print(f"❌ 앱 파일을 찾을 수 없습니다: {app_path}")
        return

    print("=" * 50)
    print("🔍 선행특허조사 앱 실행")
    print("=" * 50)
    print()
    print("📌 웹 브라우저에서 아래 주소로 접속하세요:")
    print("   http://localhost:8501")
    print()
    print("📌 종료하려면 Ctrl+C를 누르세요.")
    print("=" * 50)
    print()

    # Streamlit 실행
    subprocess.run([
        sys.executable, '-m', 'streamlit', 'run', app_path,
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ])


def main():
    print()
    print("=" * 50)
    print("🔍 선행특허조사 앱 (Prior Art Patent Search)")
    print("=" * 50)
    print()

    # 패키지 확인 및 설치
    check_and_install_packages()

    # 앱 실행
    run_streamlit_app()


if __name__ == "__main__":
    main()
