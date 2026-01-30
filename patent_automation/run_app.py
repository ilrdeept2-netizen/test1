#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
특허 업무 자동화 시스템 실행 스크립트
"""

import os
import sys
import webbrowser
from threading import Timer

def open_browser(port):
    """브라우저 자동 열기"""
    webbrowser.open(f'http://localhost:{port}')

def main():
    """메인 함수"""
    # 환경 변수 확인
    api_keys_found = []
    if os.environ.get('OPENAI_API_KEY'):
        api_keys_found.append('OpenAI')
    if os.environ.get('ANTHROPIC_API_KEY'):
        api_keys_found.append('Anthropic')
    if os.environ.get('GOOGLE_API_KEY'):
        api_keys_found.append('Google')

    print("=" * 60)
    print("     특허 업무 자동화 시스템")
    print("     Patent Application Automation System")
    print("=" * 60)
    print()

    if api_keys_found:
        print(f"✓ 감지된 API 키: {', '.join(api_keys_found)}")
    else:
        print("⚠ API 키가 설정되지 않았습니다.")
        print("  환경 변수로 설정하거나 웹 UI의 'AI 설정' 메뉴에서 입력하세요.")
        print()
        print("  예시:")
        print("  export OPENAI_API_KEY='sk-...'")
        print("  export ANTHROPIC_API_KEY='sk-ant-...'")
        print("  export GOOGLE_API_KEY='...'")
    print()

    # 포트 설정
    port = int(os.environ.get('PORT', 5001))

    print(f"서버를 시작합니다... (포트: {port})")
    print(f"웹 브라우저에서 http://localhost:{port} 로 접속하세요.")
    print()
    print("종료하려면 Ctrl+C를 누르세요.")
    print("=" * 60)

    # 브라우저 자동 열기 (1초 후)
    if '--no-browser' not in sys.argv:
        Timer(1.0, open_browser, args=[port]).start()

    # Flask 앱 실행
    from patent_automation.web_app import create_app

    app = create_app()
    app.run(
        host='0.0.0.0',
        port=port,
        debug='--debug' in sys.argv
    )


if __name__ == '__main__':
    main()
