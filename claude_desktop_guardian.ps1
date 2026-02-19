#Requires -Version 5.1
<#
.SYNOPSIS
    Claude Desktop Guardian - 영구적 크래시 방지 및 자동 복구 시스템

.DESCRIPTION
    Claude Desktop 앱이 반복적으로 크래시되는 문제를 근본적으로 해결합니다.
    일회성 수정이 아닌, 시스템 시작 시 자동으로 안정성을 보장하고
    크래시 발생 시 자동 복구하는 상시 감시 시스템입니다.

    주요 기능:
      1) 시스템 시작 시 자동으로 안정성 설정 적용 (업데이트 후에도 유지)
      2) Claude Desktop 프로세스 감시 및 크래시 시 자동 재시작
      3) 업데이트로 인한 설정 리셋 자동 감지/복구
      4) GPU 가속 설정의 영구적 관리
      5) 캐시 손상 자동 감지/정리
      6) 크래시 패턴 학습 및 적응형 안정화
      7) Windows 스케줄 작업으로 영구 등록

    실행 방법:
      # 최초 설치 (관리자 권한 권장)
      .\claude_desktop_guardian.ps1 -Install

      # 수동 감시 시작
      .\claude_desktop_guardian.ps1 -Watch

      # 설정 보호만 적용
      .\claude_desktop_guardian.ps1 -Protect

      # 제거
      .\claude_desktop_guardian.ps1 -Uninstall

.PARAMETER Install
    Guardian을 Windows 스케줄 작업으로 등록하여 로그인 시 자동 실행합니다.

.PARAMETER Watch
    Claude Desktop 프로세스를 감시하고 크래시 시 자동 복구합니다.

.PARAMETER Protect
    안정성 설정을 확인하고 필요 시 복구합니다 (감시 없이 1회 실행).

.PARAMETER Uninstall
    Guardian 스케줄 작업 및 관련 설정을 제거합니다.

.PARAMETER Silent
    출력 없이 백그라운드에서 실행합니다 (스케줄 작업용).
#>

param(
    [switch]$Install,
    [switch]$Watch,
    [switch]$Protect,
    [switch]$Uninstall,
    [switch]$Silent
)

$ErrorActionPreference = "Continue"

# ── 상수 ──
$GUARDIAN_VERSION = "2.0.0"
$GUARDIAN_NAME = "ClaudeDesktopGuardian"
$GUARDIAN_LOG_DIR = "$env:APPDATA\Claude\guardian_logs"
$GUARDIAN_CONFIG = "$env:APPDATA\Claude\guardian_config.json"
$CLAUDE_CONFIG_DIR = "$env:APPDATA\Claude"
$ELECTRON_FLAGS_FILE = "$CLAUDE_CONFIG_DIR\electron-flags.conf"
$CLAUDE_DESKTOP_CONFIG = "$CLAUDE_CONFIG_DIR\claude_desktop_config.json"
$CRASH_HISTORY_FILE = "$CLAUDE_CONFIG_DIR\guardian_crash_history.json"

$CLAUDE_EXE_PATHS = @(
    "$env:LOCALAPPDATA\Programs\Claude\Claude.exe",
    "$env:PROGRAMFILES\Claude\Claude.exe",
    "$env:PROGRAMFILES(x86)\Claude\Claude.exe"
)

$CACHE_DIRS = @(
    "$env:APPDATA\Claude\Cache",
    "$env:APPDATA\Claude\GPUCache",
    "$env:APPDATA\Claude\Code Cache",
    "$env:APPDATA\Claude\DawnCache",
    "$env:APPDATA\Claude\DawnGraphiteCache",
    "$env:APPDATA\Claude\blob_storage",
    "$env:APPDATA\Claude\Service Worker",
    "$env:LOCALAPPDATA\Claude\Cache"
)

$GPU_STABLE_FLAGS = @(
    "--disable-gpu",
    "--disable-gpu-compositing",
    "--disable-gpu-sandbox",
    "--disable-software-rasterizer",
    "--in-process-gpu"
)

# ── 유틸리티 함수 ──
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")

    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $logLine = "[$timestamp] [$Level] $Message"

    if (-not (Test-Path $GUARDIAN_LOG_DIR)) {
        New-Item -ItemType Directory -Path $GUARDIAN_LOG_DIR -Force | Out-Null
    }

    $logFile = Join-Path $GUARDIAN_LOG_DIR "guardian_$(Get-Date -Format 'yyyyMMdd').log"
    Add-Content -Path $logFile -Value $logLine -ErrorAction SilentlyContinue

    if (-not $Silent) {
        $color = switch ($Level) {
            "INFO"  { "Gray" }
            "OK"    { "Green" }
            "WARN"  { "Yellow" }
            "ERROR" { "Red" }
            "FIX"   { "Magenta" }
            default { "White" }
        }
        Write-Host "  [$Level] $Message" -ForegroundColor $color
    }
}

function Write-Banner {
    if ($Silent) { return }
    Write-Host ""
    Write-Host "  ========================================================" -ForegroundColor Cyan
    Write-Host "   Claude Desktop Guardian v$GUARDIAN_VERSION" -ForegroundColor White
    Write-Host "   영구적 크래시 방지 및 자동 복구 시스템" -ForegroundColor Gray
    Write-Host "  ========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Find-ClaudeExe {
    foreach ($p in $CLAUDE_EXE_PATHS) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

function Get-GuardianConfig {
    if (Test-Path $GUARDIAN_CONFIG) {
        try {
            return Get-Content -Path $GUARDIAN_CONFIG -Raw | ConvertFrom-Json
        } catch {
            return $null
        }
    }
    return $null
}

function Save-GuardianConfig {
    param($Config)
    if (-not (Test-Path $CLAUDE_CONFIG_DIR)) {
        New-Item -ItemType Directory -Path $CLAUDE_CONFIG_DIR -Force | Out-Null
    }
    $Config | ConvertTo-Json -Depth 10 | Set-Content -Path $GUARDIAN_CONFIG -Encoding UTF8
}

function Get-CrashHistory {
    if (Test-Path $CRASH_HISTORY_FILE) {
        try {
            return Get-Content -Path $CRASH_HISTORY_FILE -Raw | ConvertFrom-Json
        } catch {
            return @{ crashes = @(); totalCrashes = 0; lastReset = (Get-Date).ToString("o") }
        }
    }
    return @{ crashes = @(); totalCrashes = 0; lastReset = (Get-Date).ToString("o") }
}

function Save-CrashHistory {
    param($History)
    $History | ConvertTo-Json -Depth 10 | Set-Content -Path $CRASH_HISTORY_FILE -Encoding UTF8
}

# ══════════════════════════════════════════════════════════════
# 핵심 기능 1: 안정성 설정 보호 (업데이트 후에도 유지)
# ══════════════════════════════════════════════════════════════
function Protect-StabilitySettings {
    Write-Log "안정성 설정 보호 점검 시작" "INFO"

    $fixCount = 0

    # 1. 설정 디렉토리 확인
    if (-not (Test-Path $CLAUDE_CONFIG_DIR)) {
        New-Item -ItemType Directory -Path $CLAUDE_CONFIG_DIR -Force | Out-Null
        Write-Log "Claude 설정 디렉토리 생성" "FIX"
    }

    # 2. Electron GPU 플래그 확인/복구
    $needGpuFlags = $false
    $config = Get-GuardianConfig

    if ($config -and $config.forceDisableGpu) {
        $needGpuFlags = $true
    }

    # 크래시 히스토리 기반 자동 판단
    $history = Get-CrashHistory
    if ($history.totalCrashes -ge 2) {
        $needGpuFlags = $true
        Write-Log "크래시 이력 $($history.totalCrashes)회 - GPU 비활성화 강제 적용" "WARN"
    }

    if ($needGpuFlags) {
        $currentFlags = ""
        if (Test-Path $ELECTRON_FLAGS_FILE) {
            $currentFlags = Get-Content -Path $ELECTRON_FLAGS_FILE -Raw -ErrorAction SilentlyContinue
        }

        $expectedFlags = $GPU_STABLE_FLAGS -join "`n"

        if ($currentFlags.Trim() -ne $expectedFlags.Trim()) {
            Set-Content -Path $ELECTRON_FLAGS_FILE -Value $expectedFlags -Encoding UTF8
            Write-Log "GPU 안정화 플래그 복구 (업데이트로 리셋되었을 수 있음)" "FIX"
            $fixCount++
        } else {
            Write-Log "GPU 안정화 플래그 정상" "OK"
        }
    }

    # 3. 설정 파일(JSON) 무결성 확인
    if (Test-Path $CLAUDE_DESKTOP_CONFIG) {
        try {
            $desktopConfig = Get-Content -Path $CLAUDE_DESKTOP_CONFIG -Raw | ConvertFrom-Json
            Write-Log "설정 파일 정상 (파싱 가능)" "OK"
        } catch {
            $backupName = "${CLAUDE_DESKTOP_CONFIG}.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Copy-Item -Path $CLAUDE_DESKTOP_CONFIG -Destination $backupName -ErrorAction SilentlyContinue
            # 손상된 설정 파일 재생성
            $newConfig = [PSCustomObject]@{ allowAutoUpdate = $true }
            $newConfig | ConvertTo-Json -Depth 10 | Set-Content -Path $CLAUDE_DESKTOP_CONFIG -Encoding UTF8
            Write-Log "손상된 설정 파일 백업 후 재생성: $backupName" "FIX"
            $fixCount++
        }
    }

    # 4. Session Storage 손상 감지
    $sessionDir = "$CLAUDE_CONFIG_DIR\Session Storage"
    if (Test-Path $sessionDir) {
        $corruptFiles = Get-ChildItem -Path $sessionDir -File -ErrorAction SilentlyContinue |
                        Where-Object { $_.Length -eq 0 }
        if ($corruptFiles.Count -gt 0) {
            Remove-Item -Path $sessionDir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "손상된 Session Storage 삭제 ($($corruptFiles.Count)개 빈 파일)" "FIX"
            $fixCount++
        }
    }

    # 5. Local Storage 손상 감지
    $localDir = "$CLAUDE_CONFIG_DIR\Local Storage"
    if (Test-Path $localDir) {
        $corruptLdb = Get-ChildItem -Path $localDir -Filter "*.ldb" -Recurse -ErrorAction SilentlyContinue |
                      Where-Object { $_.Length -eq 0 }
        if ($corruptLdb.Count -gt 0) {
            Remove-Item -Path $localDir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "손상된 Local Storage 삭제 ($($corruptLdb.Count)개 빈 파일)" "FIX"
            $fixCount++
        }
    }

    # 6. GPUCache 크기 이상 감지 (비정상적으로 큰 경우)
    $gpuCache = "$CLAUDE_CONFIG_DIR\GPUCache"
    if (Test-Path $gpuCache) {
        $gpuCacheSize = (Get-ChildItem -Path $gpuCache -Recurse -Force -ErrorAction SilentlyContinue |
                         Measure-Object -Property Length -Sum).Sum
        if ($gpuCacheSize -gt 500MB) {
            Remove-Item -Path $gpuCache -Recurse -Force -ErrorAction SilentlyContinue
            $sizeMB = [math]::Round($gpuCacheSize / 1MB)
            Write-Log "비정상적으로 큰 GPUCache 삭제 (${sizeMB}MB)" "FIX"
            $fixCount++
        }
    }

    # 7. 이전 버전 잔존 파일 정리
    $appVersionDirs = Get-ChildItem -Path "$env:LOCALAPPDATA\Claude" -Directory -Filter "app-*" -ErrorAction SilentlyContinue
    if ($appVersionDirs.Count -gt 1) {
        $latest = $appVersionDirs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        $oldDirs = $appVersionDirs | Where-Object { $_.FullName -ne $latest.FullName }
        foreach ($old in $oldDirs) {
            try {
                Remove-Item -Path $old.FullName -Recurse -Force -ErrorAction SilentlyContinue
                Write-Log "이전 버전 정리: $($old.Name)" "FIX"
                $fixCount++
            } catch {
                Write-Log "이전 버전 삭제 실패 (사용 중): $($old.Name)" "WARN"
            }
        }
    }

    # 8. 바로가기 보호 (GPU 플래그 유지)
    if ($needGpuFlags) {
        $shortcuts = @(
            "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Claude.lnk",
            "$env:USERPROFILE\Desktop\Claude.lnk",
            "$env:PUBLIC\Desktop\Claude.lnk"
        )

        $shell = New-Object -ComObject WScript.Shell -ErrorAction SilentlyContinue
        if ($shell) {
            foreach ($shortcutPath in $shortcuts) {
                if (Test-Path $shortcutPath) {
                    try {
                        $shortcut = $shell.CreateShortcut($shortcutPath)
                        if ($shortcut.Arguments -notmatch "disable-gpu") {
                            $shortcut.Arguments = "$($shortcut.Arguments) --disable-gpu --disable-gpu-compositing".Trim()
                            $shortcut.Save()
                            Write-Log "바로가기 GPU 플래그 복구: $(Split-Path $shortcutPath -Leaf)" "FIX"
                            $fixCount++
                        }
                    } catch {
                        # 무시
                    }
                }
            }
        }
    }

    if ($fixCount -gt 0) {
        Write-Log "총 ${fixCount}건 설정 복구 완료" "OK"
    } else {
        Write-Log "모든 안정성 설정 정상" "OK"
    }

    return $fixCount
}

# ══════════════════════════════════════════════════════════════
# 핵심 기능 2: 프로세스 감시 및 자동 복구
# ══════════════════════════════════════════════════════════════
function Watch-ClaudeProcess {
    Write-Log "Claude Desktop 프로세스 감시 시작" "INFO"

    $claudeExe = Find-ClaudeExe
    if (-not $claudeExe) {
        Write-Log "Claude Desktop 실행 파일을 찾을 수 없습니다" "ERROR"
        return
    }

    $config = Get-GuardianConfig
    $maxCrashesBeforeGpuDisable = 2
    $maxCrashesBeforeCacheClean = 3
    $maxCrashesBeforeFullReset = 5
    $watchIntervalSec = 10
    $crashWindowMinutes = 30  # 이 시간 내 크래시 횟수를 카운트
    $consecutiveCrashes = 0
    $lastSeenPid = 0
    $wasRunning = $false

    while ($true) {
        $claudeProcs = Get-Process -Name "Claude" -ErrorAction SilentlyContinue |
                       Where-Object { $_.Path -eq $claudeExe }

        if ($claudeProcs) {
            # Claude가 실행 중
            $mainProc = $claudeProcs | Sort-Object StartTime | Select-Object -First 1

            if (-not $wasRunning) {
                Write-Log "Claude Desktop 실행 감지 (PID: $($mainProc.Id))" "OK"
                $consecutiveCrashes = 0
            }

            $wasRunning = $true
            $lastSeenPid = $mainProc.Id

            # 메모리 사용량 모니터링 (비정상 감지)
            $memMB = [math]::Round($mainProc.WorkingSet64 / 1MB)
            if ($memMB -gt 2000) {
                Write-Log "Claude Desktop 메모리 사용량 과다: ${memMB}MB" "WARN"
            }

        } else {
            # Claude가 실행되지 않음
            if ($wasRunning) {
                # 이전에 실행 중이었으나 사라짐 = 크래시 감지
                $consecutiveCrashes++
                Write-Log "Claude Desktop 크래시 감지! (연속 ${consecutiveCrashes}회, 이전 PID: $lastSeenPid)" "ERROR"

                # 크래시 기록
                $history = Get-CrashHistory
                $crashEntry = @{
                    timestamp = (Get-Date).ToString("o")
                    pid = $lastSeenPid
                    consecutiveCount = $consecutiveCrashes
                }

                if ($history.crashes -is [Array]) {
                    $crashList = [System.Collections.ArrayList]@($history.crashes)
                } else {
                    $crashList = [System.Collections.ArrayList]::new()
                }
                $crashList.Add($crashEntry) | Out-Null

                # 최근 100건만 유지
                if ($crashList.Count -gt 100) {
                    $crashList = [System.Collections.ArrayList]@($crashList | Select-Object -Last 100)
                }

                $history.crashes = $crashList.ToArray()
                $history.totalCrashes = [int]$history.totalCrashes + 1
                Save-CrashHistory $history

                # 적응형 복구 전략
                if ($consecutiveCrashes -ge $maxCrashesBeforeFullReset) {
                    Write-Log "연속 크래시 ${consecutiveCrashes}회 - 전체 캐시 초기화 후 재시작" "FIX"
                    Start-Sleep -Seconds 3
                    Clear-AllCache
                    Protect-StabilitySettings
                    Start-Sleep -Seconds 2
                    Start-ClaudeSafe -ClaudeExe $claudeExe

                } elseif ($consecutiveCrashes -ge $maxCrashesBeforeCacheClean) {
                    Write-Log "연속 크래시 ${consecutiveCrashes}회 - 캐시 정리 후 재시작" "FIX"
                    Start-Sleep -Seconds 3
                    Clear-ProblematicCache
                    Protect-StabilitySettings
                    Start-Sleep -Seconds 2
                    Start-ClaudeSafe -ClaudeExe $claudeExe

                } elseif ($consecutiveCrashes -ge $maxCrashesBeforeGpuDisable) {
                    Write-Log "연속 크래시 ${consecutiveCrashes}회 - GPU 비활성화 후 재시작" "FIX"

                    # Guardian 설정에 GPU 비활성화 영구 기록
                    $cfg = Get-GuardianConfig
                    if (-not $cfg) {
                        $cfg = [PSCustomObject]@{
                            forceDisableGpu = $true
                            installedAt = (Get-Date).ToString("o")
                            version = $GUARDIAN_VERSION
                        }
                    } else {
                        $cfg | Add-Member -NotePropertyName "forceDisableGpu" -NotePropertyValue $true -Force
                    }
                    Save-GuardianConfig $cfg

                    Protect-StabilitySettings
                    Start-Sleep -Seconds 2
                    Start-ClaudeSafe -ClaudeExe $claudeExe

                } else {
                    Write-Log "크래시 후 안전 모드 재시작 시도" "FIX"
                    Start-Sleep -Seconds 5
                    Start-ClaudeSafe -ClaudeExe $claudeExe
                }
            }
            # Claude가 아직 시작되지 않은 경우 (사용자가 직접 실행하지 않음) -> 대기
            $wasRunning = $false
        }

        Start-Sleep -Seconds $watchIntervalSec
    }
}

function Start-ClaudeSafe {
    param([string]$ClaudeExe)

    if (-not $ClaudeExe -or -not (Test-Path $ClaudeExe)) {
        Write-Log "Claude 실행 파일 경로 유효하지 않음" "ERROR"
        return
    }

    $args = @()
    $config = Get-GuardianConfig
    $history = Get-CrashHistory

    # 크래시 이력이 있으면 안전 플래그 추가
    if (($config -and $config.forceDisableGpu) -or ($history.totalCrashes -ge 2)) {
        $args += "--disable-gpu"
        $args += "--disable-gpu-compositing"
        $args += "--disable-gpu-sandbox"
        $args += "--in-process-gpu"
    }

    $argString = $args -join " "
    Write-Log "Claude Desktop 시작: $ClaudeExe $argString" "INFO"

    try {
        if ($args.Count -gt 0) {
            Start-Process -FilePath $ClaudeExe -ArgumentList $args -ErrorAction Stop
        } else {
            Start-Process -FilePath $ClaudeExe -ErrorAction Stop
        }
        Write-Log "Claude Desktop 시작 성공" "OK"
    } catch {
        Write-Log "Claude Desktop 시작 실패: $_" "ERROR"
    }
}

function Clear-ProblematicCache {
    Write-Log "문제 가능성 있는 캐시 정리 중..." "INFO"

    # Claude 프로세스 종료
    Get-Process -Name "Claude*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    $problematic = @(
        "$env:APPDATA\Claude\GPUCache",
        "$env:APPDATA\Claude\DawnCache",
        "$env:APPDATA\Claude\DawnGraphiteCache",
        "$env:APPDATA\Claude\Code Cache"
    )

    foreach ($dir in $problematic) {
        if (Test-Path $dir) {
            Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "삭제: $dir" "FIX"
        }
    }
}

function Clear-AllCache {
    Write-Log "전체 캐시 초기화 중..." "INFO"

    # Claude 프로세스 종료
    Get-Process -Name "Claude*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3

    foreach ($dir in $CACHE_DIRS) {
        if (Test-Path $dir) {
            $sizeMB = [math]::Round((Get-ChildItem -Path $dir -Recurse -Force -ErrorAction SilentlyContinue |
                       Measure-Object -Property Length -Sum).Sum / 1MB, 1)
            Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "삭제: $dir (${sizeMB}MB)" "FIX"
        }
    }

    # Session Storage도 삭제
    $sessionDir = "$env:APPDATA\Claude\Session Storage"
    if (Test-Path $sessionDir) {
        Remove-Item -Path $sessionDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Session Storage 삭제" "FIX"
    }

    # Local Storage도 삭제
    $localDir = "$env:APPDATA\Claude\Local Storage"
    if (Test-Path $localDir) {
        Remove-Item -Path $localDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Local Storage 삭제 (재로그인 필요)" "FIX"
    }
}

# ══════════════════════════════════════════════════════════════
# 핵심 기능 3: Windows 스케줄 작업 등록 (영구화)
# ══════════════════════════════════════════════════════════════
function Install-Guardian {
    Write-Log "Guardian 설치 시작" "INFO"

    $scriptPath = $MyInvocation.ScriptName
    if (-not $scriptPath) {
        $scriptPath = $PSCommandPath
    }
    if (-not $scriptPath) {
        Write-Log "스크립트 경로를 결정할 수 없습니다. 수동으로 등록하세요." "ERROR"
        return
    }

    # Guardian 설정 생성
    $config = [PSCustomObject]@{
        version = $GUARDIAN_VERSION
        installedAt = (Get-Date).ToString("o")
        scriptPath = $scriptPath
        forceDisableGpu = $false
        autoWatch = $true
    }

    # 기존 크래시 이력이 있으면 GPU 비활성화 유지
    $history = Get-CrashHistory
    if ($history.totalCrashes -ge 2) {
        $config.forceDisableGpu = $true
        Write-Log "기존 크래시 이력 존재 - GPU 비활성화 유지" "WARN"
    }

    Save-GuardianConfig $config

    # 스케줄 작업 1: 로그인 시 설정 보호 실행
    $protectAction = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Protect -Silent"

    $protectTrigger = New-ScheduledTaskTrigger -AtLogOn

    $protectSettings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

    try {
        Unregister-ScheduledTask -TaskName "${GUARDIAN_NAME}_Protect" -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask `
            -TaskName "${GUARDIAN_NAME}_Protect" `
            -Action $protectAction `
            -Trigger $protectTrigger `
            -Settings $protectSettings `
            -Description "Claude Desktop 안정성 설정 보호 (로그인 시 자동 실행)" `
            -ErrorAction Stop | Out-Null
        Write-Log "스케줄 작업 등록: ${GUARDIAN_NAME}_Protect (로그인 시 설정 보호)" "OK"
    } catch {
        Write-Log "스케줄 작업 등록 실패 (관리자 권한 필요): $_" "WARN"

        # 대안: 시작 프로그램 폴더에 바로가기 생성
        $startupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ClaudeGuardian.lnk"
        try {
            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut($startupPath)
            $shortcut.TargetPath = "powershell.exe"
            $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Protect -Silent"
            $shortcut.WindowStyle = 7  # Minimized
            $shortcut.Description = "Claude Desktop Guardian"
            $shortcut.Save()
            Write-Log "대안: 시작 프로그램에 바로가기 등록: $startupPath" "OK"
        } catch {
            Write-Log "시작 프로그램 바로가기 생성도 실패: $_" "ERROR"
        }
    }

    # 스케줄 작업 2: 감시 프로세스 (백그라운드)
    $watchAction = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Watch -Silent"

    $watchTrigger = New-ScheduledTaskTrigger -AtLogOn
    # 5분 지연 후 시작 (시스템 안정화 대기)
    $watchTrigger.Delay = "PT5M"

    $watchSettings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 24) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5)

    try {
        Unregister-ScheduledTask -TaskName "${GUARDIAN_NAME}_Watch" -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask `
            -TaskName "${GUARDIAN_NAME}_Watch" `
            -Action $watchAction `
            -Trigger $watchTrigger `
            -Settings $watchSettings `
            -Description "Claude Desktop 프로세스 감시 및 자동 복구" `
            -ErrorAction Stop | Out-Null
        Write-Log "스케줄 작업 등록: ${GUARDIAN_NAME}_Watch (프로세스 감시)" "OK"
    } catch {
        Write-Log "감시 스케줄 작업 등록 실패: $_" "WARN"
    }

    # 최초 설정 보호 실행
    $fixCount = Protect-StabilitySettings

    # 안정 실행 배치 파일 생성
    Create-StableLauncher

    # 크래시 이력 초기화 (설치 시점부터 새로 카운트)
    $newHistory = @{
        crashes = @()
        totalCrashes = 0
        lastReset = (Get-Date).ToString("o")
        guardianVersion = $GUARDIAN_VERSION
    }
    Save-CrashHistory $newHistory

    Write-Log "" "INFO"
    Write-Log "============================================" "INFO"
    Write-Log "Guardian 설치 완료!" "OK"
    Write-Log "============================================" "INFO"
    Write-Log "- 로그인 시 자동으로 안정성 설정을 보호합니다" "INFO"
    Write-Log "- Claude 크래시 시 자동으로 안전 모드 재시작합니다" "INFO"
    Write-Log "- 업데이트 후 설정 리셋도 자동으로 복구합니다" "INFO"
    Write-Log "- 로그: $GUARDIAN_LOG_DIR" "INFO"
    Write-Log "- 제거: .\claude_desktop_guardian.ps1 -Uninstall" "INFO"
    Write-Log "============================================" "INFO"
}

function Uninstall-Guardian {
    Write-Log "Guardian 제거 시작" "INFO"

    # 스케줄 작업 제거
    Unregister-ScheduledTask -TaskName "${GUARDIAN_NAME}_Protect" -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName "${GUARDIAN_NAME}_Watch" -Confirm:$false -ErrorAction SilentlyContinue
    Write-Log "스케줄 작업 제거 완료" "OK"

    # 시작 프로그램 바로가기 제거
    $startupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ClaudeGuardian.lnk"
    if (Test-Path $startupPath) {
        Remove-Item -Path $startupPath -Force -ErrorAction SilentlyContinue
        Write-Log "시작 프로그램 바로가기 제거" "OK"
    }

    # Guardian 설정 파일은 유지 (로그 및 크래시 기록 보존)
    Write-Log "Guardian 제거 완료 (로그 및 기록은 보존됨)" "OK"
    Write-Log "로그/기록도 삭제하려면: Remove-Item -Recurse '$GUARDIAN_LOG_DIR'" "INFO"
}

function Create-StableLauncher {
    $launcherPath = "$env:USERPROFILE\Desktop\Claude_안정실행.bat"
    $content = @"
@echo off
chcp 65001 >nul
echo ============================================
echo  Claude Desktop 안정 실행 모드
echo  (Guardian Protected)
echo ============================================
echo.

REM 기존 Claude 프로세스 정리
taskkill /f /im "Claude.exe" >nul 2>&1
timeout /t 2 >nul

echo [1/3] 기존 프로세스 정리 완료
echo [2/3] GPU 하드웨어 가속 비활성화 모드
echo [3/3] Claude Desktop 시작 중...
echo.

if exist "%LOCALAPPDATA%\Programs\Claude\Claude.exe" (
    start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox --in-process-gpu
) else if exist "%PROGRAMFILES%\Claude\Claude.exe" (
    start "" "%PROGRAMFILES%\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox --in-process-gpu
) else (
    echo [오류] Claude Desktop을 찾을 수 없습니다.
    pause
    exit /b 1
)

echo Claude Desktop이 시작되었습니다.
timeout /t 3 >nul
"@

    Set-Content -Path $launcherPath -Value $content -Encoding UTF8
    Write-Log "안정 실행 바로가기 생성: $launcherPath" "OK"
}

# ══════════════════════════════════════════════════════════════
# 핵심 기능 4: 로그 정리 (오래된 로그 자동 삭제)
# ══════════════════════════════════════════════════════════════
function Clean-OldLogs {
    if (-not (Test-Path $GUARDIAN_LOG_DIR)) { return }

    $oldLogs = Get-ChildItem -Path $GUARDIAN_LOG_DIR -File -Filter "guardian_*.log" -ErrorAction SilentlyContinue |
               Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }

    foreach ($log in $oldLogs) {
        Remove-Item -Path $log.FullName -Force -ErrorAction SilentlyContinue
    }

    if ($oldLogs.Count -gt 0) {
        Write-Log "오래된 로그 $($oldLogs.Count)개 정리" "INFO"
    }
}

# ══════════════════════════════════════════════════════════════
# 메인 실행 로직
# ══════════════════════════════════════════════════════════════
Write-Banner
Clean-OldLogs

if ($Install) {
    Install-Guardian
} elseif ($Uninstall) {
    Uninstall-Guardian
} elseif ($Watch) {
    Write-Log "감시 모드 시작 (Ctrl+C로 종료)" "INFO"
    Protect-StabilitySettings
    Watch-ClaudeProcess
} elseif ($Protect) {
    Protect-StabilitySettings
} else {
    # 파라미터 없이 실행 시 안내
    if (-not $Silent) {
        Write-Host "  사용법:" -ForegroundColor White
        Write-Host ""
        Write-Host "    .\claude_desktop_guardian.ps1 -Install    # Guardian 설치 (권장)" -ForegroundColor Green
        Write-Host "    .\claude_desktop_guardian.ps1 -Watch      # 수동 감시 시작" -ForegroundColor Gray
        Write-Host "    .\claude_desktop_guardian.ps1 -Protect    # 설정 보호 1회 실행" -ForegroundColor Gray
        Write-Host "    .\claude_desktop_guardian.ps1 -Uninstall  # Guardian 제거" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  최초 사용 시 -Install을 실행하면:" -ForegroundColor White
        Write-Host "    - 로그인 시 자동으로 안정성 설정이 적용됩니다" -ForegroundColor Gray
        Write-Host "    - Claude 크래시 시 자동으로 안전 모드 재시작됩니다" -ForegroundColor Gray
        Write-Host "    - 앱 업데이트 후 설정이 리셋되어도 자동 복구됩니다" -ForegroundColor Gray
        Write-Host ""
    }
}
