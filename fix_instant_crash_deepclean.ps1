#Requires -Version 5.1
<#
.SYNOPSIS
    Claude Desktop "즉시 크래시(Instant Crash)" 전용 딥 클린(Deep Clean) 스크립트

.DESCRIPTION
    Claude Desktop 앱이 실행 후 1~2초 만에 즉시 꺼져버리는 "크래시 루프(Crash Loop)"를
    근본적으로 해결하기 위한 4단계 딥 클린 스크립트입니다.

    기존 fix_claude_desktop_crash.ps1이 선별적 캐시 정리를 수행하는 반면,
    이 스크립트는 앱 데이터를 통째로 삭제하여 백지 상태로 초기화합니다.

    4단계 프로세스:
      1단계: 좀비 프로세스 완벽 종료
      2단계: 앱 데이터 완전 삭제 (%APPDATA%\Claude + %LOCALAPPDATA%\Claude)
      3단계: GPU 하드웨어 가속 강제 비활성화 (바로가기 + electron-flags)
      4단계: 안정 실행 런처 생성 및 트레이 설정 안내

    ※ 대화 내역은 클라우드 서버에 보관되므로 이 작업으로 삭제되지 않습니다.

.NOTES
    실행 방법:
      PowerShell -> .\fix_instant_crash_deepclean.ps1
      또는 관리자 PowerShell -> .\fix_instant_crash_deepclean.ps1 -IncludeDefenderExclusion

.PARAMETER IncludeDefenderExclusion
    Windows Defender 예외에 Claude 경로를 등록합니다 (관리자 권한 필요).

.PARAMETER SkipConfirm
    확인 프롬프트 없이 즉시 실행합니다.

.PARAMETER BackupConfig
    삭제 전 claude_desktop_config.json을 바탕화면에 백업합니다.
#>

param(
    [switch]$IncludeDefenderExclusion,
    [switch]$SkipConfirm,
    [switch]$BackupConfig
)

$ErrorActionPreference = "Continue"

# ── 유틸리티 함수 ──
function Write-Step  { param($msg) Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan; Write-Host "  $msg" -ForegroundColor White; Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan }
function Write-OK    { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "  [X] $msg" -ForegroundColor Red }
function Write-Info  { param($msg) Write-Host "  [i] $msg" -ForegroundColor Gray }
function Write-Fix   { param($msg) Write-Host "  [FIX] $msg" -ForegroundColor Magenta }

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# ── 경로 정의 ──
$claudeAppData      = "$env:APPDATA\Claude"
$claudeLocalAppData = "$env:LOCALAPPDATA\Claude"
$claudeUpdater      = "$env:LOCALAPPDATA\claude-updater"
$claudePrograms     = "$env:LOCALAPPDATA\Programs\Claude"

$claudeExePaths = @(
    "$claudePrograms\Claude.exe",
    "$env:PROGRAMFILES\Claude\Claude.exe",
    "${env:PROGRAMFILES(x86)}\Claude\Claude.exe"
)

# Claude 실행 파일 찾기
$claudeExe = $null
foreach ($p in $claudeExePaths) {
    if (Test-Path $p) { $claudeExe = $p; break }
}

# ══════════════════════════════════════════════════════════════
# 시작 배너
# ══════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "============================================================" -ForegroundColor Red
Write-Host "  Claude Desktop 즉시 크래시 전용 - 딥 클린(Deep Clean)" -ForegroundColor White
Write-Host "  v1.0.0 | $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""
Write-Host "  이 스크립트는 Claude Desktop 앱이 켜자마자 1~2초 만에" -ForegroundColor Yellow
Write-Host "  죽어버리는 '즉시 크래시(Instant Crash)' 현상을 해결합니다." -ForegroundColor Yellow
Write-Host ""
Write-Host "  [안전] 대화 내역은 서버에 보관되므로 삭제되지 않습니다." -ForegroundColor Green
Write-Host ""

if ($isAdmin) {
    Write-Host "  [관리자 권한으로 실행 중]" -ForegroundColor Green
} else {
    Write-Host "  [일반 사용자 권한으로 실행 중]" -ForegroundColor Gray
    if ($IncludeDefenderExclusion) {
        Write-Warn "Defender 예외 등록은 관리자 권한이 필요합니다. 해당 단계는 건너뜁니다."
        $IncludeDefenderExclusion = $false
    }
}

# ── 확인 프롬프트 ──
if (-not $SkipConfirm) {
    Write-Host ""
    Write-Host "  다음 폴더가 완전히 삭제됩니다:" -ForegroundColor Yellow
    Write-Host "    - $claudeAppData" -ForegroundColor Gray
    Write-Host "    - $claudeLocalAppData" -ForegroundColor Gray
    if (Test-Path $claudeUpdater) {
        Write-Host "    - $claudeUpdater" -ForegroundColor Gray
    }
    Write-Host ""
    $confirm = Read-Host "  계속하시겠습니까? (Y/N)"
    if ($confirm -notin @("Y", "y", "예", "네")) {
        Write-Host "`n  작업이 취소되었습니다." -ForegroundColor Yellow
        exit 0
    }
}

# ══════════════════════════════════════════════════════════════
# 1단계: 좀비 프로세스 완벽 종료
# ══════════════════════════════════════════════════════════════
Write-Step "1단계: 좀비 프로세스 완벽 종료"

$claudeProcessNames = @("Claude", "Claude Helper", "Claude Helper (GPU)", "Claude Helper (Renderer)", "Claude Helper (Plugin)")
$killedCount = 0

foreach ($procName in $claudeProcessNames) {
    $procs = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if ($procs) {
        foreach ($proc in $procs) {
            try {
                $proc | Stop-Process -Force -ErrorAction SilentlyContinue
                $killedCount++
            } catch {
                # 이미 종료된 프로세스 무시
            }
        }
    }
}

# taskkill로 한번 더 확인 (자식 프로세스 포함)
$taskKillResult = & taskkill /f /im "Claude.exe" /t 2>&1
if ($taskKillResult -match "SUCCESS") {
    $killedCount++
}

if ($killedCount -gt 0) {
    Write-OK "Claude 프로세스 ${killedCount}개 강제 종료 완료"
} else {
    Write-OK "실행 중인 Claude 프로세스 없음 (정상)"
}

# Cowork VM 관련 프로세스도 확인
$vmProcs = Get-Process -Name "vmwp" -ErrorAction SilentlyContinue
if ($vmProcs) {
    Write-Info "Cowork VM 프로세스 감지 (${($vmProcs.Count)}개). VM은 유지됩니다."
}

# 프로세스 종료 후 파일 잠금 해제 대기
Start-Sleep -Seconds 3
Write-OK "1단계 완료: 좀비 프로세스 정리됨"

# ══════════════════════════════════════════════════════════════
# 2단계: 앱 데이터 완전 삭제 (가장 중요)
# ══════════════════════════════════════════════════════════════
Write-Step "2단계: 앱 데이터 완전 삭제 (핵심 단계)"

# 설정 파일 백업 (요청 시)
if ($BackupConfig) {
    $configFile = "$claudeAppData\claude_desktop_config.json"
    if (Test-Path $configFile) {
        $backupPath = "$env:USERPROFILE\Desktop\claude_desktop_config_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        Copy-Item -Path $configFile -Destination $backupPath -ErrorAction SilentlyContinue
        if (Test-Path $backupPath) {
            Write-OK "설정 파일 백업 완료: $backupPath"
        } else {
            Write-Warn "설정 파일 백업 실패"
        }
    } else {
        Write-Info "백업할 설정 파일 없음"
    }
}

$deletedFolders = 0
$totalSizeMB = 0

# 2-1. %APPDATA%\Claude 전체 삭제
if (Test-Path $claudeAppData) {
    $size = (Get-ChildItem -Path $claudeAppData -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 1)
    $totalSizeMB += $sizeMB
    Write-Info "삭제 대상: $claudeAppData (${sizeMB}MB)"

    try {
        Remove-Item -Path $claudeAppData -Recurse -Force -ErrorAction Stop
        Write-OK "%APPDATA%\Claude 폴더 삭제 완료 (${sizeMB}MB)"
        $deletedFolders++
    } catch {
        Write-Warn "일부 파일 잠금으로 전체 삭제 실패. 개별 삭제를 시도합니다..."
        # 개별 삭제 시도
        Get-ChildItem -Path $claudeAppData -Force -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            } catch {
                Write-Err "삭제 불가: $($_.Name) (재부팅 후 수동 삭제 필요)"
            }
        }
        $deletedFolders++
    }
} else {
    Write-Info "%APPDATA%\Claude 폴더 없음 (이미 삭제됨)"
}

# 2-2. %LOCALAPPDATA%\Claude 삭제 (업데이터 캐시)
if (Test-Path $claudeLocalAppData) {
    $size = (Get-ChildItem -Path $claudeLocalAppData -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 1)
    $totalSizeMB += $sizeMB
    Write-Info "삭제 대상: $claudeLocalAppData (${sizeMB}MB)"

    try {
        Remove-Item -Path $claudeLocalAppData -Recurse -Force -ErrorAction Stop
        Write-OK "%LOCALAPPDATA%\Claude 폴더 삭제 완료 (${sizeMB}MB)"
        $deletedFolders++
    } catch {
        Write-Warn "일부 파일 잠금 — 개별 삭제 시도 중..."
        Get-ChildItem -Path $claudeLocalAppData -Force -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            } catch {
                Write-Err "삭제 불가: $($_.Name)"
            }
        }
        $deletedFolders++
    }
} else {
    Write-Info "%LOCALAPPDATA%\Claude 폴더 없음"
}

# 2-3. claude-updater 폴더 삭제 (존재하는 경우)
if (Test-Path $claudeUpdater) {
    $size = (Get-ChildItem -Path $claudeUpdater -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 1)
    $totalSizeMB += $sizeMB
    Write-Info "삭제 대상: $claudeUpdater (${sizeMB}MB)"

    try {
        Remove-Item -Path $claudeUpdater -Recurse -Force -ErrorAction Stop
        Write-OK "claude-updater 폴더 삭제 완료 (${sizeMB}MB)"
        $deletedFolders++
    } catch {
        Write-Warn "claude-updater 삭제 실패 (수동 삭제 필요)"
    }
} else {
    Write-Info "claude-updater 폴더 없음"
}

Write-OK "2단계 완료: ${deletedFolders}개 폴더 삭제 (총 ${totalSizeMB}MB 정리)"

# ══════════════════════════════════════════════════════════════
# 3단계: GPU 하드웨어 가속 강제 비활성화
# ══════════════════════════════════════════════════════════════
Write-Step "3단계: GPU 하드웨어 가속 강제 비활성화"

# 3-1. %APPDATA%\Claude 폴더 재생성 (electron-flags.conf용)
if (-not (Test-Path $claudeAppData)) {
    New-Item -ItemType Directory -Path $claudeAppData -Force | Out-Null
    Write-Info "Claude 설정 폴더 재생성: $claudeAppData"
}

# 3-2. electron-flags.conf 생성 (GPU 비활성화)
$electronFlagsFile = "$claudeAppData\electron-flags.conf"
$gpuFlags = @"
--disable-gpu
--disable-gpu-compositing
--disable-gpu-sandbox
--disable-software-rasterizer
"@
Set-Content -Path $electronFlagsFile -Value $gpuFlags -Encoding UTF8
Write-OK "GPU 비활성화 플래그 파일 생성: $electronFlagsFile"

# 3-3. 바로가기에 --disable-gpu 추가
$shortcuts = @(
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Claude.lnk",
    "$env:USERPROFILE\Desktop\Claude.lnk",
    "$env:PUBLIC\Desktop\Claude.lnk"
)

$shortcutUpdated = 0
$shell = New-Object -ComObject WScript.Shell
foreach ($shortcutPath in $shortcuts) {
    if (Test-Path $shortcutPath) {
        try {
            $shortcut = $shell.CreateShortcut($shortcutPath)
            if ($shortcut.Arguments -notmatch "disable-gpu") {
                $shortcut.Arguments = "$($shortcut.Arguments) --disable-gpu".Trim()
                $shortcut.Save()
                Write-OK "바로가기 수정 완료: $shortcutPath"
                $shortcutUpdated++
            } else {
                Write-Info "바로가기에 이미 --disable-gpu 적용됨: $shortcutPath"
            }
        } catch {
            Write-Warn "바로가기 수정 실패: $shortcutPath"
        }
    }
}

if ($shortcutUpdated -eq 0 -and -not ($shortcuts | Where-Object { Test-Path $_ })) {
    Write-Info "바로가기 파일을 찾을 수 없음 (수동 설정 필요)"
    Write-Info "바탕화면/시작 메뉴의 Claude 바로가기 > 속성 > 대상(T) 끝에:"
    Write-Host "        --disable-gpu" -ForegroundColor White
    Write-Info "을 추가하세요."
}

# 3-4. Windows Defender 예외 등록 (관리자 + 옵션 활성 시)
if ($IncludeDefenderExclusion -and $isAdmin) {
    $defenderPaths = @($claudeAppData, $claudeLocalAppData, $claudePrograms)
    foreach ($dPath in $defenderPaths) {
        if (Test-Path $dPath) {
            try {
                Add-MpPreference -ExclusionPath $dPath -ErrorAction SilentlyContinue
                Write-Fix "Defender 예외 등록: $dPath"
            } catch {
                Write-Warn "Defender 예외 등록 실패: $dPath"
            }
        }
    }
}

Write-OK "3단계 완료: GPU 하드웨어 가속 비활성화 적용됨"

# ══════════════════════════════════════════════════════════════
# 4단계: 안정 실행 런처 생성 및 트레이 설정 안내
# ══════════════════════════════════════════════════════════════
Write-Step "4단계: 안정 실행 런처 생성 및 설정 안내"

# 4-1. 바탕화면에 "딥 클린 안정 실행" 배치 파일 생성
$stableLauncher = "$env:USERPROFILE\Desktop\Claude_딥클린_안정실행.bat"
$launcherContent = @"
@echo off
chcp 65001 >nul
echo ============================================
echo  Claude Desktop - Deep Clean Safe Launch
echo  (GPU 비활성화 + 크래시 방지 모드)
echo ============================================
echo.

REM 1. 기존 Claude 프로세스 완전 종료
taskkill /f /im "Claude.exe" /t >nul 2>&1
timeout /t 2 >nul

echo [1/3] 기존 Claude 프로세스 정리 완료
echo [2/3] GPU 하드웨어 가속 비활성화 모드로 시작합니다...

REM 2. GPU 비활성화하여 실행
if exist "%LOCALAPPDATA%\Programs\Claude\Claude.exe" (
    echo [3/3] Claude Desktop 실행 중...
    start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox --in-process-gpu
) else if exist "%PROGRAMFILES%\Claude\Claude.exe" (
    echo [3/3] Claude Desktop 실행 중...
    start "" "%PROGRAMFILES%\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox --in-process-gpu
) else (
    echo.
    echo [오류] Claude Desktop 실행 파일을 찾을 수 없습니다.
    echo 설치 경로를 확인하거나 https://claude.com/download 에서 재설치하세요.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  [중요] 로그인 후 반드시 아래 설정을 확인하세요:
echo.
echo  Settings(톱니바퀴) ^> General ^> "Menu bar" 옵션 활성화(ON)
echo.
echo  이 설정이 켜져 있어야 화면 에러 시에도 앱이
echo  백그라운드에서 버티며 복구를 시도할 수 있습니다.
echo ============================================
echo.
echo 이 창은 10초 후 자동으로 닫힙니다.
timeout /t 10 >nul
"@

Set-Content -Path $stableLauncher -Value $launcherContent -Encoding UTF8
Write-OK "안정 실행 런처 생성: $stableLauncher"

# 4-2. 설정 복원 (백업한 경우)
if ($BackupConfig) {
    $backupFiles = Get-ChildItem -Path "$env:USERPROFILE\Desktop" -Filter "claude_desktop_config_backup_*.json" -ErrorAction SilentlyContinue |
                   Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($backupFiles) {
        $configDir = "$claudeAppData"
        if (-not (Test-Path $configDir)) {
            New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        }
        Copy-Item -Path $backupFiles.FullName -Destination "$configDir\claude_desktop_config.json" -ErrorAction SilentlyContinue
        Write-OK "설정 파일 복원 완료: claude_desktop_config.json"
    }
}

Write-OK "4단계 완료: 안정 실행 런처 및 안내 준비됨"

# ══════════════════════════════════════════════════════════════
# 최종 결과 요약
# ══════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  딥 클린(Deep Clean) 완료!" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  수행된 작업:" -ForegroundColor White
Write-Host "    1. Claude 좀비 프로세스 완전 종료" -ForegroundColor Gray
Write-Host "    2. 앱 데이터 통째 삭제 (${totalSizeMB}MB 정리)" -ForegroundColor Gray
Write-Host "    3. GPU 하드웨어 가속 강제 비활성화" -ForegroundColor Gray
Write-Host "    4. 바탕화면에 안정 실행 런처 생성" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  다음 단계 (반드시 따라하세요)" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. 바탕화면의 'Claude_딥클린_안정실행.bat'을 더블클릭하세요." -ForegroundColor White
Write-Host "     (초기화되어 로그인 화면이 뜹니다)" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. 로그인 직후, 아무 대화도 열지 말고 즉시:" -ForegroundColor Yellow
Write-Host "     Settings(톱니바퀴) > General > 'Menu bar' 옵션 ON" -ForegroundColor White
Write-Host ""
Write-Host "     이 설정이 켜져 있어야 나중에 코워크 작업 중" -ForegroundColor Gray
Write-Host "     화면 에러가 나도 앱이 즉시 종료되지 않고" -ForegroundColor Gray
Write-Host "     백그라운드에서 버티며 복구를 시도합니다." -ForegroundColor Gray
Write-Host ""
Write-Host "  3. 이후 정상적으로 사용하시면 됩니다." -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  영구적 해결을 원하시면" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Guardian 시스템을 설치하면 업데이트 후에도" -ForegroundColor Gray
Write-Host "  설정이 자동으로 복구됩니다:" -ForegroundColor Gray
Write-Host ""
Write-Host "    .\claude_desktop_guardian.ps1 -Install" -ForegroundColor Green
Write-Host ""
Write-Host "  무거운 코딩 작업(Cowork 등)은 터미널 기반" -ForegroundColor Gray
Write-Host "  Claude Code(CLI)에서 진행하시는 것을 권장합니다." -ForegroundColor Gray
Write-Host "  CLI 환경은 이 UI 렌더링 버그에서 완전히 자유롭습니다." -ForegroundColor Gray
Write-Host ""
Write-Host "  문제 지속 시: https://github.com/anthropics/claude-code/issues" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
