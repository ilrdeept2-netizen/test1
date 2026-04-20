@echo off
chcp 65001 > nul
title 한국특허서식 변환기 - 웹 서버

echo.
echo ============================================================
echo   한국특허서식 변환기 - 웹 서버
echo   HWP/DOCX/PDF → HLT 변환
echo ============================================================
echo.

REM Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python을 설치해주세요.
    echo.
    pause
    exit /b 1
)

REM 서버 시작
echo 서버를 시작합니다...
echo 잠시 후 브라우저가 자동으로 열립니다.
echo 종료하려면 이 창을 닫거나 Ctrl+C를 누르세요.
echo.

python start_patent_web.py

pause
