#!/usr/bin/env python3
"""
AI 뉴스 다이제스트 모바일 앱 실행기
"""

import subprocess
import sys
import os
import socket

def get_local_ip():
    """로컬 IP 주소 가져오기"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def check_dependencies():
    """필요한 패키지 확인 및 설치"""
    required = ['flask', 'flask_cors', 'feedparser', 'beautifulsoup4', 'requests']
    missing = []

    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"📦 필요한 패키지 설치 중: {', '.join(missing)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing + ['-q'])
        print("✅ 설치 완료!\n")

def main():
    """메인 함수"""
    print("\n" + "="*55)
    print("  🌅 AI 뉴스 다이제스트 - 모바일 웹앱")
    print("="*55)

    # 의존성 확인
    check_dependencies()

    local_ip = get_local_ip()
    port = 5050

    print(f"""
📱 모바일에서 접속하는 방법:
   ─────────────────────────────
   1. 같은 Wi-Fi에 연결
   2. 브라우저에서 접속:

      http://{local_ip}:{port}

   3. '홈 화면에 추가'로 앱처럼 사용!

💡 PC에서 접속: http://localhost:{port}
─────────────────────────────
   Ctrl+C 로 종료
""")

    # Flask 앱 실행
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    from ai_news_app import app
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
