@echo off
chcp 65001 > nul
title AI 뉴스 다이제스트

echo.
echo ═══════════════════════════════════════════════════════
echo   🌅 AI 뉴스 다이제스트 - 모바일 웹앱 시작
echo ═══════════════════════════════════════════════════════
echo.

python start_ai_news.py

if errorlevel 1 (
    echo.
    echo ❌ 오류가 발생했습니다.
    echo    Python이 설치되어 있는지 확인하세요.
    pause
)
