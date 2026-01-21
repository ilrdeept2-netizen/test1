#!/bin/bash

echo ""
echo "================================================"
echo "  🔍 선행특허조사 웹앱 (모바일 지원)"
echo "================================================"
echo ""

# Python 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다."
    echo "   sudo apt install python3 python3-pip 로 설치해주세요."
    exit 1
fi

echo "📦 필요한 패키지를 확인하고 설치합니다..."
echo ""

# 필요한 패키지 설치
pip3 install flask flask-cors python-docx PyPDF2 python-pptx openpyxl olefile -q 2>/dev/null

echo ""
echo "✅ 패키지 설치 완료!"
echo ""

# IP 주소 확인
IP_ADDR=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$IP_ADDR" ]; then
    IP_ADDR=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
fi

echo "================================================"
echo "  PC 브라우저: http://localhost:5000"
echo ""
echo "  📱 모바일에서 접속하려면:"
if [ -n "$IP_ADDR" ]; then
    echo "     http://$IP_ADDR:5000"
else
    echo "     같은 네트워크의 PC IP 주소:5000"
fi
echo ""
echo "  종료하려면 Ctrl+C를 누르세요"
echo "================================================"
echo ""

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# Flask 앱 실행
python3 patent_search_server.py
