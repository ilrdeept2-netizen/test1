@echo off
chcp 65001 > nul
title 선행특허조사 앱

echo.
echo ================================================
echo   🔍 선행특허조사 앱 (Prior Art Patent Search)
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
pip install streamlit python-docx PyPDF2 python-pptx openpyxl olefile -q

echo.
echo ✅ 패키지 설치 완료!
echo.
echo ================================================
echo   웹 브라우저에서 http://localhost:8501 로 접속하세요
echo   종료하려면 이 창을 닫으세요
echo ================================================
echo.

REM Streamlit 앱 실행
python -m streamlit run "%~dp0patent_search_web.py" --server.headless true --browser.gatherUsageStats false

pause
