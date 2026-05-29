#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
특허 업무 자동화 시스템 간편 실행 스크립트
"""

import os
import sys
import subprocess

def check_dependencies():
    """필수 패키지 확인 및 설치"""
    required = ['flask', 'openai', 'anthropic', 'google-generativeai']
    missing = []

    for package in required:
        try:
            __import__(package.replace('-', '_').split('.')[0])
        except ImportError:
            missing.append(package)

    if missing:
        print(f"필요한 패키지를 설치합니다: {', '.join(missing)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
        print("패키지 설치 완료!")

def main():
    # 작업 디렉토리 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # 패키지 경로 추가
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          특허 업무 자동화 시스템 v1.0                      ║")
    print("║          Patent Application Automation System              ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print("║  주요 기능:                                                ║")
    print("║  • 특허 명세서 자동 작성 (기술분야, 배경기술, 효과 등)     ║")
    print("║  • 도면 계획 및 부호체계 관리                              ║")
    print("║  • 청구항 작성 (독립항, 종속항)                            ║")
    print("║  • OA(의견제출통지서) 대응 자동화                          ║")
    print("║  • 전체 워크플로우 자동 실행                               ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # 의존성 확인
    print("필수 패키지 확인 중...")
    check_dependencies()
    print()

    # 앱 실행
    from patent_automation.web_app import create_app
    import webbrowser
    from threading import Timer

    port = 5001

    def open_browser():
        webbrowser.open(f'http://localhost:{port}')

    app = create_app()

    print(f"서버 시작: http://localhost:{port}")
    print("브라우저가 자동으로 열립니다...")
    print()
    print("종료하려면 Ctrl+C를 누르세요.")
    print("-" * 60)

    Timer(1.5, open_browser).start()
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()
