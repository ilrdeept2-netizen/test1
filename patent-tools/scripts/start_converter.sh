#!/bin/bash

echo "===================================================="
echo "특허 문서 변환기 (Patent Document Converter)"
echo "===================================================="
echo ""

# Python 확인
if ! command -v python3 &> /dev/null
then
    echo "❌ Python3가 설치되어 있지 않습니다!"
    echo ""
    echo "Python을 먼저 설치해주세요."
    exit 1
fi

echo "✓ Python 설치 확인"
echo ""

# start_converter.py 실행
python3 start_converter.py
