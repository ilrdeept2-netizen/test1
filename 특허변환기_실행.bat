@echo off
chcp 65001 >nul
title 특허 문서 변환기

echo.
echo ====================================================
echo 특허 문서 변환기 (Patent Document Converter)
echo ====================================================
echo.

REM Python이 설치되어 있는지 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다!
    echo.
    echo Python을 먼저 설치해주세요:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✓ Python 설치 확인
echo.

REM start_converter.py 실행
python start_converter.py

pause
