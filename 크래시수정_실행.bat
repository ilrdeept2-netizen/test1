@echo off
chcp 65001 >nul
echo ============================================
echo  Claude Desktop 크래시 수정 도구 실행
echo ============================================
echo.

REM 스크립트 위치 확인
set "SCRIPT_DIR=%~dp0"

REM 실행할 스크립트 선택
echo  [1] 일반 진단 + 수정  (fix_claude_desktop_crash.ps1)
echo  [2] 전체 수정 -FullFix (관리자 권한 필요)
echo  [3] 진단만 -DiagOnly   (수정 없이 문제 파악만)
echo  [4] 즉시 크래시 딥 클린 (fix_instant_crash_deepclean.ps1)
echo.
set /p choice="번호를 선택하세요 (1-4): "

if "%choice%"=="1" (
    echo.
    echo [실행] fix_claude_desktop_crash.ps1 ...
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%fix_claude_desktop_crash.ps1"
) else if "%choice%"=="2" (
    echo.
    echo [실행] fix_claude_desktop_crash.ps1 -FullFix ...
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%fix_claude_desktop_crash.ps1" -FullFix
) else if "%choice%"=="3" (
    echo.
    echo [실행] fix_claude_desktop_crash.ps1 -DiagOnly ...
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%fix_claude_desktop_crash.ps1" -DiagOnly
) else if "%choice%"=="4" (
    echo.
    echo [실행] fix_instant_crash_deepclean.ps1 ...
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%fix_instant_crash_deepclean.ps1"
) else (
    echo.
    echo 잘못된 선택입니다. 1~4 중 하나를 입력하세요.
)

echo.
pause
