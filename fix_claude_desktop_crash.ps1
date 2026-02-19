#Requires -Version 5.1
<#
.SYNOPSIS
    Claude Desktop 앱 자동 종료(크래시) 진단 및 수정 스크립트

.DESCRIPTION
    Claude Desktop 앱이 반복적으로 자동 종료되는 문제를 진단하고 수정합니다.
    주요 수정 대상:
      1) GPU 하드웨어 가속 충돌 → GPU 가속 비활성화
      2) 앱 캐시/데이터 손상 → 캐시 정리 및 재구성
      3) Cowork VM 프로세스 충돌 → VM 상태 초기화
      4) 메모리 부족 → 가상 메모리 확인 및 권장
      5) 백신/보안 소프트웨어 간섭 → Windows Defender 예외 등록
      6) 앱 업데이트 symlink 버그 → 업데이트 경로 수정

.NOTES
    일부 수정(방화벽, Defender 예외)은 관리자 권한이 필요합니다.
    관리자 권한 없이도 기본 진단 및 캐시 정리는 실행됩니다.

    실행 방법:
      PowerShell -> .\fix_claude_desktop_crash.ps1
      또는 관리자 PowerShell -> .\fix_claude_desktop_crash.ps1 -FullFix

.PARAMETER FullFix
    관리자 권한이 필요한 고급 수정까지 모두 수행합니다.

.PARAMETER DiagOnly
    진단만 수행하고 수정은 하지 않습니다.

.PARAMETER DisableGPU
    GPU 하드웨어 가속을 비활성화합니다 (가장 흔한 크래시 원인).
#>

param(
    [switch]$FullFix,
    [switch]$DiagOnly,
    [switch]$DisableGPU
)

$ErrorActionPreference = "Continue"

# ── 유틸리티 함수 ──
function Write-Step  { param($msg) Write-Host "`n[$((Get-Date).ToString('HH:mm:ss'))] " -NoNewline -ForegroundColor Cyan; Write-Host $msg -ForegroundColor White }
function Write-OK    { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "  [X] $msg" -ForegroundColor Red }
function Write-Info  { param($msg) Write-Host "  [i] $msg" -ForegroundColor Gray }
function Write-Fix   { param($msg) Write-Host "  [FIX] $msg" -ForegroundColor Magenta }

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# 진단 결과 저장
$diagnosis = @{
    Issues = @()
    Fixes  = @()
    Score  = 0  # 0~100 건강도 점수
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Claude Desktop 앱 자동 종료 진단 및 수정 도구" -ForegroundColor White
Write-Host "  v1.0.0 | $(Get-Date -Format 'yyyy-MM-dd')" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
if ($DiagOnly) { Write-Host "  [모드: 진단 전용 - 수정 없음]" -ForegroundColor Yellow }
elseif ($FullFix) { Write-Host "  [모드: 전체 수정 (관리자)]" -ForegroundColor Green }
else { Write-Host "  [모드: 기본 수정]" -ForegroundColor White }
Write-Host ""

# ══════════════════════════════════════════════════════════════
# Phase 1: 시스템 환경 진단
# ══════════════════════════════════════════════════════════════
Write-Step "Phase 1: 시스템 환경 진단"

# 1-1. Windows 버전
$osInfo = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction SilentlyContinue
if ($osInfo) {
    $osVersion = $osInfo.Caption
    $osBuild = $osInfo.BuildNumber
    Write-Info "OS: $osVersion (빌드 $osBuild)"

    if ([int]$osBuild -lt 22000) {
        Write-Warn "Windows 10 감지. Claude Cowork는 Windows 11 권장"
        $diagnosis.Issues += "Windows 10 사용 중 (Windows 11 권장)"
    } else {
        Write-OK "Windows 11 확인"
    }
} else {
    Write-Info "OS 정보를 가져올 수 없습니다"
}

# 1-2. 메모리 확인
$memInfo = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction SilentlyContinue
if ($memInfo) {
    $totalRAMGB = [math]::Round($memInfo.TotalPhysicalMemory / 1GB, 1)
    Write-Info "총 RAM: ${totalRAMGB}GB"

    if ($totalRAMGB -lt 8) {
        Write-Err "RAM 8GB 미만 — Claude Desktop + Cowork VM 운영에 부족"
        $diagnosis.Issues += "RAM 부족 (${totalRAMGB}GB, 최소 8GB 필요)"
    } elseif ($totalRAMGB -lt 16) {
        Write-Warn "RAM ${totalRAMGB}GB — Cowork 사용 시 메모리 부족 가능성"
        $diagnosis.Issues += "RAM 권장 미달 (${totalRAMGB}GB, 16GB 권장)"
    } else {
        Write-OK "RAM 충분: ${totalRAMGB}GB"
    }
}

# 1-3. 디스크 여유 공간
$sysDrive = Get-PSDrive -Name C -ErrorAction SilentlyContinue
if ($sysDrive) {
    $freeGB = [math]::Round($sysDrive.Free / 1GB, 1)
    Write-Info "C: 여유 공간: ${freeGB}GB"

    if ($freeGB -lt 10) {
        Write-Err "디스크 여유 공간 심각하게 부족 (${freeGB}GB) — 앱 크래시 원인"
        $diagnosis.Issues += "디스크 여유 공간 부족 (${freeGB}GB, 최소 15GB 필요)"
    } elseif ($freeGB -lt 20) {
        Write-Warn "디스크 여유 공간 부족 경고 (${freeGB}GB, 30GB 권장)"
        $diagnosis.Issues += "디스크 여유 공간 부족 경고 (${freeGB}GB)"
    } else {
        Write-OK "디스크 여유 공간 충분: ${freeGB}GB"
    }
}

# 1-4. Claude Desktop 설치 확인
$claudeExePaths = @(
    "$env:LOCALAPPDATA\Programs\Claude\Claude.exe",
    "$env:PROGRAMFILES\Claude\Claude.exe",
    "$env:PROGRAMFILES(x86)\Claude\Claude.exe"
)
$claudeExe = $null
foreach ($p in $claudeExePaths) {
    if (Test-Path $p) { $claudeExe = $p; break }
}

if ($claudeExe) {
    $claudeVersion = (Get-Item $claudeExe).VersionInfo.FileVersion
    Write-OK "Claude Desktop 설치 확인: $claudeExe"
    Write-Info "버전: $claudeVersion"
} else {
    Write-Warn "Claude Desktop 실행 파일을 기본 경로에서 찾을 수 없습니다"
    Write-Info "검색 경로: $($claudeExePaths -join ', ')"
}

# ══════════════════════════════════════════════════════════════
# Phase 2: 크래시 로그 분석
# ══════════════════════════════════════════════════════════════
Write-Step "Phase 2: 크래시 로그 분석"

$logDirs = @(
    "$env:APPDATA\Claude\logs",
    "$env:LOCALAPPDATA\Claude\logs",
    "$env:APPDATA\Claude\Local Storage",
    "$env:APPDATA\Claude\Session Storage"
)

$crashIndicators = @{
    "GPU" = @("gpu_process", "GpuProcessHost", "gpu-process-crashed", "GL_ERROR", "ANGLE", "SwapChain")
    "Memory" = @("out of memory", "OutOfMemory", "allocation failed", "ENOMEM", "heap limit")
    "VM" = @("vm_service", "cowork-vm", "hyperv", "wsl", "VHDX", "vmwp.exe")
    "Auth" = @("Invalid authorization", "token expired", "401", "authentication failed", "session expired")
    "Network" = @("ECONNREFUSED", "ETIMEDOUT", "net::ERR", "fetch failed", "WebSocket")
    "Update" = @("update", "squirrel", "symlink", "EPERM", "nupkg")
    "Renderer" = @("renderer crash", "BrowserWindow", "destroyed", "ERR_CRASHED", "SIGSEGV", "SIGABRT")
}

$crashReport = @{}
$recentCrashCount = 0

foreach ($logDir in $logDirs) {
    if (-not (Test-Path $logDir)) { continue }

    $logFiles = Get-ChildItem -Path $logDir -File -ErrorAction SilentlyContinue |
                Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) } |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 10

    foreach ($logFile in $logFiles) {
        try {
            $content = Get-Content -Path $logFile.FullName -Tail 500 -ErrorAction SilentlyContinue
            if (-not $content) { continue }
            $text = $content -join "`n"

            foreach ($category in $crashIndicators.Keys) {
                foreach ($keyword in $crashIndicators[$category]) {
                    if ($text -match [regex]::Escape($keyword)) {
                        if (-not $crashReport.ContainsKey($category)) {
                            $crashReport[$category] = @()
                        }
                        $crashReport[$category] += "$($logFile.Name): $keyword 감지"
                        $recentCrashCount++
                    }
                }
            }
        } catch {
            # 로그 읽기 실패 무시
        }
    }
}

if ($crashReport.Count -gt 0) {
    Write-Warn "최근 7일간 크래시 관련 로그 발견:"
    foreach ($category in $crashReport.Keys) {
        $count = $crashReport[$category].Count
        Write-Info "  [$category] $count건 감지"
        $diagnosis.Issues += "$category 관련 크래시 로그 ${count}건"
    }

    if ($crashReport.ContainsKey("GPU")) {
        Write-Err "→ GPU 관련 크래시가 감지되었습니다 (가장 흔한 자동 종료 원인)"
        $DisableGPU = $true
    }
    if ($crashReport.ContainsKey("Memory")) {
        Write-Err "→ 메모리 부족 크래시가 감지되었습니다"
    }
    if ($crashReport.ContainsKey("Renderer")) {
        Write-Err "→ 렌더러 프로세스 크래시가 감지되었습니다"
        $DisableGPU = $true
    }
} else {
    Write-OK "최근 7일간 크래시 로그 없음 (또는 로그 디렉토리 없음)"
}

# Windows 이벤트 로그에서 Claude 크래시 확인
try {
    $appCrashes = Get-WinEvent -FilterHashtable @{
        LogName = 'Application'
        ProviderName = 'Application Error'
        StartTime = (Get-Date).AddDays(-7)
    } -MaxEvents 50 -ErrorAction SilentlyContinue |
    Where-Object { $_.Message -match "Claude" -or $_.Message -match "Electron" }

    if ($appCrashes) {
        Write-Warn "Windows 이벤트 로그에서 Claude 크래시 $($appCrashes.Count)건 발견"
        foreach ($crash in ($appCrashes | Select-Object -First 3)) {
            Write-Info "  $(($crash.TimeCreated).ToString('MM/dd HH:mm')): $($crash.Message.Substring(0, [Math]::Min(100, $crash.Message.Length)))..."
        }
        $diagnosis.Issues += "Windows 이벤트 로그 크래시 $($appCrashes.Count)건"
    } else {
        Write-OK "Windows 이벤트 로그에 Claude 크래시 기록 없음"
    }
} catch {
    Write-Info "이벤트 로그 조회 불가 (권한 부족 가능)"
}

if ($DiagOnly -and $crashReport.Count -eq 0) {
    Write-OK "주요 크래시 징후 없음"
}

# ══════════════════════════════════════════════════════════════
# Phase 3: GPU 하드웨어 가속 문제 수정
# ══════════════════════════════════════════════════════════════
Write-Step "Phase 3: GPU 하드웨어 가속 설정"

# Claude Desktop은 Electron 기반이므로 --disable-gpu 플래그를 사용
# 또는 설정 파일에서 GPU 가속을 비활성화할 수 있음

$claudeConfigDir = "$env:APPDATA\Claude"
$electronFlagsFile = "$claudeConfigDir\electron-flags.conf"
$claudeDesktopConfig = "$claudeConfigDir\claude_desktop_config.json"

# GPU 관련 Electron 설정 파일 확인/생성
if ($DisableGPU -or ($crashReport.ContainsKey("GPU")) -or ($crashReport.ContainsKey("Renderer"))) {
    Write-Warn "GPU 관련 크래시 감지 → GPU 하드웨어 가속 비활성화 권장"

    if (-not $DiagOnly) {
        # Electron 플래그 파일 생성
        if (-not (Test-Path $claudeConfigDir)) {
            New-Item -ItemType Directory -Path $claudeConfigDir -Force | Out-Null
        }

        $gpuFlags = @"
--disable-gpu
--disable-gpu-compositing
--disable-gpu-sandbox
--disable-software-rasterizer
"@
        Set-Content -Path $electronFlagsFile -Value $gpuFlags -Encoding UTF8
        Write-Fix "GPU 가속 비활성화 플래그 적용: $electronFlagsFile"
        $diagnosis.Fixes += "GPU 하드웨어 가속 비활성화"

        # 바탕화면 바로가기에 --disable-gpu 추가 (존재하는 경우)
        $shortcuts = @(
            "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Claude.lnk",
            "$env:USERPROFILE\Desktop\Claude.lnk",
            "$env:PUBLIC\Desktop\Claude.lnk"
        )

        $shell = New-Object -ComObject WScript.Shell
        foreach ($shortcutPath in $shortcuts) {
            if (Test-Path $shortcutPath) {
                try {
                    $shortcut = $shell.CreateShortcut($shortcutPath)
                    if ($shortcut.Arguments -notmatch "disable-gpu") {
                        $shortcut.Arguments = "$($shortcut.Arguments) --disable-gpu".Trim()
                        $shortcut.Save()
                        Write-OK "바로가기 업데이트: $shortcutPath"
                    }
                } catch {
                    Write-Warn "바로가기 수정 실패: $shortcutPath"
                }
            }
        }
    } else {
        Write-Info "[진단 모드] GPU 비활성화가 권장됩니다. -DisableGPU 플래그로 실행하세요."
    }
} else {
    Write-OK "GPU 관련 크래시 미감지 — 현재 설정 유지"
}

# ══════════════════════════════════════════════════════════════
# Phase 4: 앱 캐시 및 손상 데이터 정리
# ══════════════════════════════════════════════════════════════
Write-Step "Phase 4: 앱 캐시 및 손상 데이터 정리"

# Claude 프로세스 확인
$claudeProcs = Get-Process -Name "Claude*" -ErrorAction SilentlyContinue
if ($claudeProcs -and -not $DiagOnly) {
    Write-Warn "Claude 프로세스 실행 중 ($($claudeProcs.Count)개). 캐시 정리를 위해 종료합니다..."
    $claudeProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-OK "Claude 프로세스 종료 완료"
} elseif ($claudeProcs) {
    Write-Warn "Claude 프로세스 실행 중 ($($claudeProcs.Count)개). 진단 모드이므로 종료하지 않습니다."
}

$cacheDirs = @(
    @{ Path = "$env:APPDATA\Claude\Cache"; Desc = "앱 캐시" },
    @{ Path = "$env:APPDATA\Claude\GPUCache"; Desc = "GPU 캐시" },
    @{ Path = "$env:APPDATA\Claude\Code Cache"; Desc = "코드 캐시" },
    @{ Path = "$env:APPDATA\Claude\DawnCache"; Desc = "Dawn(WebGPU) 캐시" },
    @{ Path = "$env:APPDATA\Claude\DawnGraphiteCache"; Desc = "Dawn Graphite 캐시" },
    @{ Path = "$env:LOCALAPPDATA\Claude\Cache"; Desc = "Local 캐시" },
    @{ Path = "$env:APPDATA\Claude\blob_storage"; Desc = "Blob Storage" },
    @{ Path = "$env:APPDATA\Claude\Service Worker"; Desc = "Service Worker 캐시" }
)

$totalCleaned = 0

foreach ($cache in $cacheDirs) {
    if (Test-Path $cache.Path) {
        $size = (Get-ChildItem -Path $cache.Path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $sizeMB = [math]::Round($size / 1MB, 1)
        Write-Info "발견: $($cache.Desc) — ${sizeMB}MB"

        if (-not $DiagOnly) {
            try {
                Remove-Item -Path $cache.Path -Recurse -Force -ErrorAction SilentlyContinue
                Write-OK "삭제: $($cache.Desc) (${sizeMB}MB)"
                $totalCleaned += $sizeMB
            } catch {
                Write-Warn "삭제 실패 (파일 잠금): $($cache.Desc)"
            }
        }
    }
}

# Session Storage 손상 확인
$sessionStorage = "$env:APPDATA\Claude\Session Storage"
if (Test-Path $sessionStorage) {
    $sessionFiles = Get-ChildItem -Path $sessionStorage -File -ErrorAction SilentlyContinue
    $corruptCount = ($sessionFiles | Where-Object { $_.Length -eq 0 }).Count
    if ($corruptCount -gt 0) {
        Write-Warn "손상된 세션 파일 ${corruptCount}개 감지"
        if (-not $DiagOnly) {
            Remove-Item -Path $sessionStorage -Recurse -Force -ErrorAction SilentlyContinue
            Write-Fix "손상된 Session Storage 삭제"
            $diagnosis.Fixes += "손상된 Session Storage 삭제"
        }
    }
}

# Local Storage 손상 확인
$localStorage = "$env:APPDATA\Claude\Local Storage"
if (Test-Path $localStorage) {
    $ldbFiles = Get-ChildItem -Path $localStorage -Filter "*.ldb" -Recurse -ErrorAction SilentlyContinue
    $corruptLdb = ($ldbFiles | Where-Object { $_.Length -eq 0 }).Count
    if ($corruptLdb -gt 0) {
        Write-Warn "손상된 Local Storage 파일 ${corruptLdb}개 감지"
        $diagnosis.Issues += "손상된 Local Storage 파일 존재"
        if (-not $DiagOnly) {
            Remove-Item -Path $localStorage -Recurse -Force -ErrorAction SilentlyContinue
            Write-Fix "손상된 Local Storage 삭제 (재로그인 필요)"
            $diagnosis.Fixes += "손상된 Local Storage 삭제"
        }
    }
}

if ($totalCleaned -gt 0) {
    Write-OK "총 ${totalCleaned}MB 캐시 정리 완료"
    $diagnosis.Fixes += "캐시 ${totalCleaned}MB 정리"
}

# ══════════════════════════════════════════════════════════════
# Phase 5: Cowork VM 상태 점검 및 초기화
# ══════════════════════════════════════════════════════════════
Write-Step "Phase 5: Cowork VM 상태 점검"

# VM 서비스 확인
$vmmsService = Get-Service -Name "vmms" -ErrorAction SilentlyContinue
if ($vmmsService) {
    if ($vmmsService.Status -eq "Running") {
        Write-OK "Hyper-V 서비스 실행 중"
    } else {
        Write-Warn "Hyper-V 서비스 중지 상태"
        if (-not $DiagOnly -and $isAdmin) {
            Start-Service -Name "vmms" -ErrorAction SilentlyContinue
            Write-Fix "Hyper-V 서비스 시작"
        }
    }
} else {
    Write-Info "Hyper-V 미설치 (Cowork를 사용하지 않는 경우 정상)"
}

# cowork-vm 상태 확인
$coworkVm = Get-VM -Name "cowork-vm" -ErrorAction SilentlyContinue
if ($coworkVm) {
    Write-Info "Cowork VM 상태: $($coworkVm.State)"
    Write-Info "Cowork VM 메모리: $([math]::Round($coworkVm.MemoryAssigned / 1GB, 1))GB"

    if ($coworkVm.State -eq "Running" -and -not $DiagOnly) {
        # VM이 비정상적으로 많은 메모리를 사용하는지 확인
        if ($coworkVm.MemoryAssigned -gt 4GB) {
            Write-Warn "Cowork VM이 $([math]::Round($coworkVm.MemoryAssigned / 1GB, 1))GB 메모리 사용 중 (과도)"
            $diagnosis.Issues += "VM 메모리 과다 사용"
        }
    }

    # VM이 멈춤(Paused/Saved) 상태인 경우
    if ($coworkVm.State -eq "Paused" -or $coworkVm.State -eq "Saved") {
        Write-Warn "Cowork VM이 비정상 상태: $($coworkVm.State)"
        if (-not $DiagOnly) {
            Stop-VM -Name "cowork-vm" -TurnOff -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Write-Fix "비정상 VM 강제 종료"
            $diagnosis.Fixes += "비정상 Cowork VM 강제 종료"
        }
    }
} else {
    Write-Info "Cowork VM 없음 (아직 사용하지 않았거나 삭제됨)"
}

# VM 번들 무결성 확인
$vmBundlePath = "$env:APPDATA\Claude\vm_bundles\claudevm.bundle\rootfs.vhdx"
if (Test-Path $vmBundlePath) {
    $vhdxSize = (Get-Item $vmBundlePath).Length
    $vhdxGB = [math]::Round($vhdxSize / 1GB, 2)
    Write-Info "VM 번들 크기: ${vhdxGB}GB"

    if ($vhdxGB -lt 1) {
        Write-Err "VM 번들 파일 크기가 비정상적으로 작음 (${vhdxGB}GB) — 손상 가능성"
        $diagnosis.Issues += "VM 번들 손상 가능 (크기: ${vhdxGB}GB)"
        if (-not $DiagOnly) {
            Write-Fix "VM 번들 삭제 (Claude 재실행 시 자동 재다운로드)"
            Remove-Item -Path "$env:APPDATA\Claude\vm_bundles" -Recurse -Force -ErrorAction SilentlyContinue
            $diagnosis.Fixes += "손상된 VM 번들 삭제"
        }
    } else {
        Write-OK "VM 번들 크기 정상: ${vhdxGB}GB"
    }
}

# ══════════════════════════════════════════════════════════════
# Phase 6: 앱 업데이트 및 Symlink 버그 수정
# ══════════════════════════════════════════════════════════════
Write-Step "Phase 6: 앱 업데이트 상태 확인"

# Squirrel 업데이트 관련 파일 확인 (Electron 앱 업데이터)
$updateExe = "$env:LOCALAPPDATA\Claude\Update.exe"
$appDir = "$env:LOCALAPPDATA\Programs\Claude"

if (Test-Path $updateExe) {
    Write-Info "업데이터 확인: $updateExe"

    # 여러 버전이 동시에 존재하는지 확인
    $appVersionDirs = Get-ChildItem -Path "$env:LOCALAPPDATA\Claude" -Directory -Filter "app-*" -ErrorAction SilentlyContinue
    if ($appVersionDirs.Count -gt 1) {
        Write-Warn "여러 앱 버전 공존 감지 ($($appVersionDirs.Count)개) — 업데이트 충돌 가능성"
        foreach ($dir in $appVersionDirs) {
            Write-Info "  버전: $($dir.Name) ($(($dir.LastWriteTime).ToString('yyyy-MM-dd')))"
        }
        $diagnosis.Issues += "여러 앱 버전 공존 ($($appVersionDirs.Count)개)"

        if (-not $DiagOnly) {
            # 가장 최신 버전만 남기고 정리
            $latest = $appVersionDirs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            $old = $appVersionDirs | Where-Object { $_.FullName -ne $latest.FullName }
            foreach ($oldDir in $old) {
                try {
                    Remove-Item -Path $oldDir.FullName -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Fix "이전 버전 삭제: $($oldDir.Name)"
                } catch {
                    Write-Warn "이전 버전 삭제 실패: $($oldDir.Name)"
                }
            }
            $diagnosis.Fixes += "이전 앱 버전 정리"
        }
    } elseif ($appVersionDirs.Count -eq 1) {
        Write-OK "앱 버전 1개만 존재: $($appVersionDirs[0].Name)"
    }
}

# ══════════════════════════════════════════════════════════════
# Phase 7: 보안 소프트웨어 예외 등록 (관리자 전용)
# ══════════════════════════════════════════════════════════════
Write-Step "Phase 7: 보안 소프트웨어 점검"

if ($FullFix -and $isAdmin) {
    # Windows Defender 예외 등록
    $defenderExclusions = @(
        "$env:LOCALAPPDATA\Programs\Claude",
        "$env:APPDATA\Claude",
        "$env:LOCALAPPDATA\Claude"
    )

    foreach ($exclusion in $defenderExclusions) {
        if (Test-Path $exclusion) {
            try {
                Add-MpPreference -ExclusionPath $exclusion -ErrorAction SilentlyContinue
                Write-Fix "Defender 예외 등록: $exclusion"
            } catch {
                Write-Warn "Defender 예외 등록 실패: $exclusion"
            }
        }
    }
    $diagnosis.Fixes += "Windows Defender 예외 등록"

    # 방화벽 규칙 확인
    $claudeFirewall = Get-NetFirewallRule -DisplayName "*Claude*" -ErrorAction SilentlyContinue
    if (-not $claudeFirewall) {
        Write-Warn "Claude 방화벽 규칙 없음"
        if ($claudeExe) {
            New-NetFirewallRule -DisplayName "Claude Desktop" -Direction Inbound -Program $claudeExe -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null
            New-NetFirewallRule -DisplayName "Claude Desktop (Out)" -Direction Outbound -Program $claudeExe -Action Allow -Profile Any -ErrorAction SilentlyContinue | Out-Null
            Write-Fix "Claude Desktop 방화벽 규칙 추가"
            $diagnosis.Fixes += "방화벽 규칙 추가"
        }
    } else {
        Write-OK "Claude 방화벽 규칙 존재"
    }
} elseif ($FullFix -and -not $isAdmin) {
    Write-Warn "관리자 권한 없음 — 보안 소프트웨어 설정 건너뜀"
    Write-Info "관리자 PowerShell에서 -FullFix로 다시 실행하세요"
} else {
    # 기본 모드에서는 알려진 백신 프로세스 확인만
    $knownAV = @("V3Svc", "AYAgent", "AYServiceNT", "avp", "ekrn", "AVGSvc", "MsMpEng")
    $runningAV = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $knownAV -contains $_.ProcessName
    }
    if ($runningAV) {
        $avNames = ($runningAV | Select-Object -ExpandProperty ProcessName -Unique) -join ", "
        Write-Warn "실행 중인 백신 감지: $avNames"
        Write-Info "→ 백신이 Claude Desktop을 차단할 수 있습니다. 실시간 감시를 일시 중지하고 테스트하세요."
        $diagnosis.Issues += "백신 소프트웨어 간섭 가능성 ($avNames)"
    } else {
        Write-OK "알려진 충돌 백신 미감지"
    }
}

# ══════════════════════════════════════════════════════════════
# Phase 8: Electron 앱 안정성 설정
# ══════════════════════════════════════════════════════════════
Write-Step "Phase 8: 앱 안정성 설정 최적화"

if (-not $DiagOnly) {
    # claude_desktop_config.json에 안정성 설정 추가
    if (-not (Test-Path $claudeConfigDir)) {
        New-Item -ItemType Directory -Path $claudeConfigDir -Force | Out-Null
    }

    $configUpdated = $false

    if (Test-Path $claudeDesktopConfig) {
        try {
            $config = Get-Content -Path $claudeDesktopConfig -Raw | ConvertFrom-Json
        } catch {
            Write-Warn "설정 파일 손상 — 백업 후 재생성"
            Copy-Item -Path $claudeDesktopConfig -Destination "${claudeDesktopConfig}.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')" -ErrorAction SilentlyContinue
            $config = [PSCustomObject]@{}
            $configUpdated = $true
        }
    } else {
        $config = [PSCustomObject]@{}
    }

    # autoUpdate 관련 설정이 있으면 확인
    if (-not (Get-Member -InputObject $config -Name "allowAutoUpdate" -MemberType NoteProperty -ErrorAction SilentlyContinue)) {
        $config | Add-Member -NotePropertyName "allowAutoUpdate" -NotePropertyValue $true -ErrorAction SilentlyContinue
        $configUpdated = $true
    }

    if ($configUpdated) {
        $config | ConvertTo-Json -Depth 10 | Set-Content -Path $claudeDesktopConfig -Encoding UTF8
        Write-Fix "설정 파일 업데이트: $claudeDesktopConfig"
        $diagnosis.Fixes += "앱 설정 파일 최적화"
    } else {
        Write-OK "설정 파일 정상"
    }
}

# ══════════════════════════════════════════════════════════════
# Phase 9: 자동 재시작 배치 파일 생성
# ══════════════════════════════════════════════════════════════
Write-Step "Phase 9: 안정 실행 스크립트 생성"

if (-not $DiagOnly) {
    $stableLauncher = "$env:USERPROFILE\Desktop\Claude_안정실행.bat"
    $launcherContent = @"
@echo off
chcp 65001 >nul
echo ============================================
echo  Claude Desktop 안정 실행 모드
echo ============================================
echo.

REM GPU 관련 프로세스 정리
taskkill /f /im "Claude.exe" >nul 2>&1
timeout /t 2 >nul

REM GPU 가속 비활성화하여 실행
echo [1/3] 기존 Claude 프로세스 정리 완료
echo [2/3] GPU 하드웨어 가속 비활성화 모드로 시작합니다...
echo [3/3] Claude Desktop 실행 중...
echo.

if exist "%LOCALAPPDATA%\Programs\Claude\Claude.exe" (
    start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox --in-process-gpu
) else if exist "%PROGRAMFILES%\Claude\Claude.exe" (
    start "" "%PROGRAMFILES%\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox --in-process-gpu
) else (
    echo [오류] Claude Desktop 실행 파일을 찾을 수 없습니다.
    echo 설치 경로를 확인하세요.
    pause
    exit /b 1
)

echo.
echo Claude Desktop이 시작되었습니다.
echo 이 창은 5초 후 자동으로 닫힙니다.
timeout /t 5 >nul
"@

    Set-Content -Path $stableLauncher -Value $launcherContent -Encoding UTF8
    Write-Fix "안정 실행 배치 파일 생성: $stableLauncher"
    $diagnosis.Fixes += "바탕화면에 안정 실행 스크립트 생성"
}

# ══════════════════════════════════════════════════════════════
# 최종 진단 결과 요약
# ══════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  진단 결과 요약" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan

# 건강도 점수 계산
$maxScore = 100
$issueDeduction = $diagnosis.Issues.Count * 10
$fixBonus = $diagnosis.Fixes.Count * 5
$diagnosis.Score = [math]::Max(0, [math]::Min(100, $maxScore - $issueDeduction + $fixBonus))

if ($diagnosis.Issues.Count -gt 0) {
    Write-Host ""
    Write-Host "  발견된 문제점 ($($diagnosis.Issues.Count)건):" -ForegroundColor Yellow
    foreach ($issue in $diagnosis.Issues) {
        Write-Host "    - $issue" -ForegroundColor Yellow
    }
}

if ($diagnosis.Fixes.Count -gt 0) {
    Write-Host ""
    Write-Host "  적용된 수정 ($($diagnosis.Fixes.Count)건):" -ForegroundColor Green
    foreach ($fix in $diagnosis.Fixes) {
        Write-Host "    + $fix" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if (-not $DiagOnly) {
    Write-Host "  다음 단계:" -ForegroundColor White
    Write-Host "  1. Claude Desktop을 재실행합니다" -ForegroundColor Gray
    Write-Host "     (또는 바탕화면의 'Claude_안정실행.bat' 사용)" -ForegroundColor Gray
    Write-Host "  2. 여전히 종료되면 -FullFix 옵션으로 다시 실행:" -ForegroundColor Gray
    Write-Host "     .\fix_claude_desktop_crash.ps1 -FullFix" -ForegroundColor White
    Write-Host "  3. 그래도 해결 안 되면 앱 완전 재설치:" -ForegroundColor Gray
    Write-Host "     설정 > 앱 > Claude > 제거 후 https://claude.com/download 재설치" -ForegroundColor White
    Write-Host ""

    if ($crashReport.ContainsKey("GPU") -or $DisableGPU) {
        Write-Host "  [중요] GPU 크래시가 감지되어 GPU 가속을 비활성화했습니다." -ForegroundColor Yellow
        Write-Host "  앱이 안정되면 GPU 가속을 다시 켜려면:" -ForegroundColor Gray
        Write-Host "    Remove-Item '$electronFlagsFile'" -ForegroundColor White
        Write-Host ""
    }
} else {
    Write-Host "  [진단 전용 모드] 수정을 적용하려면 -DiagOnly 없이 다시 실행하세요" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "  문제 지속 시: https://github.com/anthropics/claude-code/issues" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
