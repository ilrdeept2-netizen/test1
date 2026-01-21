#!/bin/bash

echo ""
echo "================================================"
echo "  🔍 선행특허조사 앱 (Prior Art Patent Search)"
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
pip3 install streamlit python-docx PyPDF2 python-pptx openpyxl olefile -q 2>/dev/null

echo ""
echo "✅ 패키지 설치 완료!"
echo ""
echo "================================================"
echo "  웹 브라우저에서 http://localhost:8501 로 접속하세요"
echo "  종료하려면 Ctrl+C를 누르세요"
echo "================================================"
echo ""

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# Streamlit 앱 실행
python3 -m streamlit run patent_search_web.py --server.headless true --browser.gatherUsageStats false
