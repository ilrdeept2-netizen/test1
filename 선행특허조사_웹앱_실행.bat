@echo off
chcp 65001 > nul
title 선행특허조사 웹앱 (모바일 지원)

echo.
echo ================================================
echo   🔍 선행특허조사 웹앱 (모바일 지원)
echo ================================================
echo.

REM Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo    https://www.python.org/downloads/ 에서 Python을 설치해주세요.
    pause
    exit /b 1
)

echo 📦 필요한 패키지를 확인하고 설치합니다...
echo.

REM 필요한 패키지 설치
pip install flask flask-cors python-docx PyPDF2 python-pptx openpyxl olefile -q

echo.
echo ✅ 패키지 설치 완료!
echo.
echo ================================================
echo   PC 브라우저: http://localhost:5000
echo.
echo   📱 모바일에서 접속하려면:
echo      같은 WiFi에 연결된 상태에서
echo      PC의 IP 주소로 접속하세요
echo      예: http://192.168.0.xxx:5000
echo.
echo   종료하려면 이 창을 닫거나 Ctrl+C
echo ================================================
echo.

REM Flask 앱 실행
python "%~dp0patent_search_server.py"

pause
