#!/bin/bash

echo ""
echo "============================================================"
echo "  한국특허서식 변환기 - 웹 서버"
echo "  HWP/DOCX/PDF → HLT 변환"
echo "============================================================"
echo ""

# Python 확인
if ! command -v python3 &> /dev/null; then
    echo "[오류] Python3가 설치되어 있지 않습니다."
    echo "Python을 먼저 설치해주세요."
    exit 1
fi

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 서버 시작
echo "서버를 시작합니다..."
echo "잠시 후 브라우저가 자동으로 열립니다."
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

python3 start_patent_web.py
