#!/usr/bin/env python3
"""
멀티 에이전트 워크플로우 - 빠른 시작 가이드

이 스크립트는 시스템 설정 및 실행을 도와줍니다.
"""

import os
import subprocess
import sys


def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        print("오류: Python 3.8 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        return False
    print(f"✓ Python 버전: {sys.version}")
    return True


def install_dependencies():
    """의존성 설치"""
    print("\n의존성 설치 중...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"
        ])
        print("✓ 의존성 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"오류: 의존성 설치 실패 - {e}")
        return False


def check_api_key():
    """API 키 확인"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("✓ ANTHROPIC_API_KEY 설정됨")
        return True
    else:
        print("⚠ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("  환경 변수를 설정하세요:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        return False


def run_demo():
    """데모 실행"""
    print("\n데모 실행 중...")
    try:
        subprocess.run([sys.executable, "main.py", "demo"])
    except KeyboardInterrupt:
        print("\n데모 중단됨")


def run_interactive():
    """대화형 모드 실행"""
    print("\n대화형 모드 시작...")
    try:
        subprocess.run([sys.executable, "main.py", "interactive"])
    except KeyboardInterrupt:
        print("\n대화형 모드 종료")


def main():
    """메인 함수"""
    print("="*60)
    print("  멀티 에이전트 워크플로우 시스템 - 빠른 시작")
    print("="*60)

    # 1. Python 버전 확인
    if not check_python_version():
        return

    # 2. 의존성 설치
    response = input("\n의존성을 설치하시겠습니까? (y/N): ").strip().lower()
    if response == 'y':
        install_dependencies()

    # 3. API 키 확인
    print()
    check_api_key()

    # 4. 실행 옵션
    print("\n실행 옵션:")
    print("  1. 데모 실행")
    print("  2. 대화형 모드")
    print("  3. 종료")

    choice = input("\n선택 (1/2/3): ").strip()

    if choice == "1":
        run_demo()
    elif choice == "2":
        run_interactive()
    else:
        print("종료합니다.")


if __name__ == "__main__":
    main()
