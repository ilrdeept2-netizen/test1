#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Claude Cowork VirtioFS/Plan9 마운트 오류 자동 수정 스크립트

.DESCRIPTION
    에러: RPC error -1: failed to ensure virtiofs mount: Plan9 mount failed: bad address
    원인: Windows Hypervisor Platform 미활성화, WSL2 미업데이트, VM 번들 손상 등

    이 스크립트가 수행하는 작업:
      1) Windows 가상화 기능 3종 확인 및 활성화
      2) WSL2 업데이트
      3) Claude 프로세스 및 Cowork VM 정리
      4) VM 번들 초기화 (선택)
      5) .wslconfig 최적화 (선택)
      6) Projected File System 활성화 (선택)

.NOTES
    반드시 "관리자 권한으로 실행"한 PowerShell에서 실행하세요.
    실행 방법: PowerShell(관리자) -> .\fix_cowork_virtiofs_mount.ps1

.PARAMETER ResetVM
    VM 번들을 삭제하고 새로 다운로드하게 합니다.

.PARAMETER SkipReboot
    자동 재부팅을 건너뜁니다 (수동 재부팅 필요).

.PARAMETER OptimizeWSL
    .wslconfig 파일을 최적화합니다.
#>

param(
    [switch]$ResetVM,
    [switch]$SkipReboot,
    [switch]$OptimizeWSL
)

$ErrorActionPreference = "Continue"

# ── 유틸리티 함수 ──
function Write-Step  { param($msg) Write-Host "`n[$((Get-Date).ToString('HH:mm:ss'))] " -NoNewline -ForegroundColor Cyan; Write-Host $msg -ForegroundColor White }
function Write-OK    { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "  [X] $msg" -ForegroundColor Red }
function Write-Info  { param($msg) Write-Host "  [i] $msg" -ForegroundColor Gray }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Claude Cowork VirtioFS/Plan9 마운트 오류 수정 도구" -ForegroundColor White
Write-Host "  에러: RPC error -1: Plan9 mount failed: bad address" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan

$needsReboot = $false

# ══════════════════════════════════════════════════════════
# Phase 1: 관리자 권한 확인
# ══════════════════════════════════════════════════════════
Write-Step "Phase 1: 관리자 권한 확인"
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Err "관리자 권한이 필요합니다."
    Write-Info "PowerShell -> 마우스 오른쪽 클릭 -> '관리자 권한으로 실행'"
    exit 1
}
Write-OK "관리자 권한 확인됨"

# ══════════════════════════════════════════════════════════
# Phase 2: Windows 가상화 기능 3종 확인 및 활성화 (핵심)
# ══════════════════════════════════════════════════════════
Write-Step "Phase 2: Windows 가상화 기능 확인 (VirtioFS 필수 조건)"

$features = @(
    @{ Name = "HypervisorPlatform";      Display = "Windows Hypervisor Platform" },
    @{ Name = "VirtualMachinePlatform";   Display = "Virtual Machine Platform" },
    @{ Name = "Microsoft-Hyper-V-All";    Display = "Hyper-V" }
)

foreach ($feat in $features) {
    $state = Get-WindowsOptionalFeature -Online -FeatureName $feat.Name -ErrorAction SilentlyContinue

    if ($null -eq $state) {
        Write-Warn "$($feat.Display): 이 Windows 에디션에서 사용할 수 없음"
        # Windows Home에서는 Hyper-V가 없을 수 있음
        if ($feat.Name -eq "Microsoft-Hyper-V-All") {
            Write-Info "Windows Home 에디션은 Hyper-V 대신 VirtualMachinePlatform을 사용합니다."
        }
    } elseif ($state.State -eq "Enabled") {
        Write-OK "$($feat.Display): 활성화됨"
    } else {
        Write-Warn "$($feat.Display): 비활성화 → 활성화합니다..."
        try {
            Enable-WindowsOptionalFeature -Online -FeatureName $feat.Name -All -NoRestart -ErrorAction Stop | Out-Null
            Write-OK "$($feat.Display): 활성화 완료 (재부팅 필요)"
            $needsReboot = $true
        } catch {
            Write-Err "$($feat.Display) 활성화 실패: $($_.Exception.Message)"
        }
    }
}

# Projected File System (시간 경과 후 에러 방지에 도움)
$projFS = Get-WindowsOptionalFeature -Online -FeatureName "Client-ProjFS" -ErrorAction SilentlyContinue
if ($null -ne $projFS -and $projFS.State -ne "Enabled") {
    Write-Info "Projected File System 활성화 (VirtioFS 안정성 향상)..."
    try {
        Enable-WindowsOptionalFeature -Online -FeatureName "Client-ProjFS" -All -NoRestart -ErrorAction Stop | Out-Null
        Write-OK "Projected File System: 활성화 완료"
        $needsReboot = $true
    } catch {
        Write-Warn "Projected File System 활성화 실패 (선택사항이므로 계속 진행)"
    }
} elseif ($null -ne $projFS) {
    Write-OK "Projected File System: 이미 활성화됨"
}

# ══════════════════════════════════════════════════════════
# Phase 3: CPU 가상화 확인
# ══════════════════════════════════════════════════════════
Write-Step "Phase 3: CPU 가상화 지원 확인"

$cpuVirt = (Get-CimInstance -ClassName Win32_Processor).VirtualizationFirmwareEnabled
if ($cpuVirt -eq $true) {
    Write-OK "CPU 가상화 (VT-x/AMD-V): BIOS에서 활성화됨"
} elseif ($cpuVirt -eq $false) {
    Write-Err "CPU 가상화가 BIOS에서 비활성화되어 있습니다!"
    Write-Info "해결: PC 재부팅 -> BIOS 진입 (F2/Del/F10) -> CPU Virtualization -> Enabled"
    Write-Info "이 설정을 켜지 않으면 Cowork VM이 절대 실행되지 않습니다."
} else {
    Write-Warn "CPU 가상화 상태를 확인할 수 없습니다. 작업 관리자 -> 성능 -> CPU에서 확인하세요."
}

# ══════════════════════════════════════════════════════════
# Phase 4: WSL2 업데이트
# ══════════════════════════════════════════════════════════
Write-Step "Phase 4: WSL2 업데이트 (VirtioFS 드라이버 포함)"

try {
    $wslStatus = wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "WSL2 설치 확인됨"
        Write-Info "WSL 업데이트 실행 중..."
        $updateResult = wsl --update 2>&1
        Write-OK "WSL2 업데이트 완료"

        # 기본 버전을 WSL2로 설정
        wsl --set-default-version 2 2>&1 | Out-Null
        Write-OK "WSL 기본 버전: 2"
    } else {
        Write-Warn "WSL이 설치되어 있지 않습니다. 설치합니다..."
        wsl --install --no-distribution 2>&1 | Out-Null
        Write-OK "WSL2 설치 완료 (재부팅 필요)"
        $needsReboot = $true
    }
} catch {
    Write-Warn "WSL 업데이트 중 경고: $($_.Exception.Message)"
}

# ══════════════════════════════════════════════════════════
# Phase 5: Claude 프로세스 및 VM 정리
# ══════════════════════════════════════════════════════════
Write-Step "Phase 5: Claude 프로세스 및 Cowork VM 정리"

# Claude 프로세스 종료
$claudeProcs = Get-Process -Name "Claude*" -ErrorAction SilentlyContinue
if ($claudeProcs) {
    Write-Info "Claude 프로세스 $($claudeProcs.Count)개 종료 중..."
    $claudeProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-OK "Claude 프로세스 종료 완료"
} else {
    Write-OK "실행 중인 Claude 프로세스 없음"
}

# Cowork VM 정리
$vm = Get-VM -Name "cowork-vm" -ErrorAction SilentlyContinue
if ($null -ne $vm) {
    Write-Info "기존 cowork-vm 발견. 정리 중..."
    if ($vm.State -ne "Off") {
        Stop-VM -Name "cowork-vm" -TurnOff -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
    }
    Remove-VM -Name "cowork-vm" -Force -ErrorAction SilentlyContinue
    Write-OK "cowork-vm 제거 완료"
} else {
    Write-OK "기존 cowork-vm 없음"
}

# VM 소켓/캐시 정리
Remove-Item -Path "$env:TEMP\claude-vm-*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:APPDATA\Claude\vm_state" -Recurse -Force -ErrorAction SilentlyContinue
Write-OK "VM 캐시 정리 완료"

# ══════════════════════════════════════════════════════════
# Phase 6: VM 번들 초기화 (선택)
# ══════════════════════════════════════════════════════════
Write-Step "Phase 6: VM 번들 상태 확인"

$vmBundleDirs = @(
    "$env:APPDATA\Claude\vm_bundles",
    "$env:LOCALAPPDATA\Claude\vm_bundles"
)

$bundleExists = $false
foreach ($dir in $vmBundleDirs) {
    if (Test-Path $dir) {
        $size = (Get-ChildItem -Path $dir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $sizeGB = [math]::Round($size / 1GB, 2)
        Write-Info "발견: $dir ($sizeGB GB)"
        $bundleExists = $true
    }
}

if ($ResetVM -and $bundleExists) {
    Write-Warn "VM 번들을 삭제합니다 (Claude Desktop 재실행 시 자동 재다운로드)..."
    foreach ($dir in $vmBundleDirs) {
        if (Test-Path $dir) {
            Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
            Write-OK "삭제: $dir"
        }
    }
    Write-Info "Claude Desktop 재실행 시 VM 번들이 새로 다운로드됩니다 (10~30분 소요)"
} elseif ($bundleExists) {
    Write-Info "VM 번들 초기화가 필요하면 -ResetVM 옵션으로 다시 실행하세요."
} else {
    Write-Warn "VM 번들이 없습니다. Claude Desktop 재실행 시 자동 다운로드됩니다."
}

# ══════════════════════════════════════════════════════════
# Phase 7: .wslconfig 최적화 (선택)
# ══════════════════════════════════════════════════════════
Write-Step "Phase 7: .wslconfig 확인"

$wslConfigPath = "$env:USERPROFILE\.wslconfig"

if ($OptimizeWSL) {
    Write-Info ".wslconfig 최적화 적용 중..."

    # 기존 파일 백업
    if (Test-Path $wslConfigPath) {
        Copy-Item -Path $wslConfigPath -Destination "$wslConfigPath.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')" -Force
        Write-OK "기존 .wslconfig 백업 완료"
    }

    $totalRAM = [math]::Round((Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
    $wslMemory = [math]::Max(4, [math]::Floor($totalRAM / 2))

    $wslConfig = @"
[wsl2]
memory=${wslMemory}GB
processors=4
swap=4GB
localhostForwarding=true
"@

    Set-Content -Path $wslConfigPath -Value $wslConfig -Encoding UTF8
    Write-OK ".wslconfig 최적화 완료 (VM 메모리: ${wslMemory}GB / 전체 RAM: ${totalRAM}GB)"
} else {
    if (Test-Path $wslConfigPath) {
        Write-OK ".wslconfig 파일 존재"
        Write-Info "최적화하려면 -OptimizeWSL 옵션으로 다시 실행하세요."
    } else {
        Write-Info ".wslconfig 파일 없음. -OptimizeWSL 옵션으로 생성 가능."
    }
}

# ══════════════════════════════════════════════════════════
# Phase 8: VPN/보안 소프트웨어 점검
# ══════════════════════════════════════════════════════════
Write-Step "Phase 8: VPN/보안 소프트웨어 점검"

# 알려진 VPN 프로세스 확인
$vpnProcesses = @("ExpressVPN*", "NordVPN*", "Surfshark*", "ProtonVPN*", "openvpn*", "wireguard*", "Cloudflare*")
$foundVPN = $false
foreach ($vpn in $vpnProcesses) {
    $proc = Get-Process -Name $vpn -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Warn "VPN 감지: $($proc.Name) — Cowork 사용 시 VPN을 종료하는 것이 권장됩니다."
        $foundVPN = $true
    }
}
if (-not $foundVPN) {
    Write-OK "알려진 VPN 프로세스 없음"
}

# 알려진 백신 프로세스 확인
$avProcesses = @("V3*", "ALYac*", "AYAgent*", "AhnLab*")
$foundAV = $false
foreach ($av in $avProcesses) {
    $proc = Get-Process -Name $av -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Warn "국산 백신 감지: $($proc.Name) — VM 간섭 가능성 있음. 실시간 보호 일시 중지 후 테스트 권장."
        $foundAV = $true
    }
}
if (-not $foundAV) {
    Write-OK "알려진 간섭 백신 프로세스 없음"
}

# ══════════════════════════════════════════════════════════
# Phase 9: 시스템 정보 요약
# ══════════════════════════════════════════════════════════
Write-Step "Phase 9: 시스템 정보 요약"

$os = Get-CimInstance -ClassName Win32_OperatingSystem
$cpu = Get-CimInstance -ClassName Win32_Processor | Select-Object -First 1
$totalRAM = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
$freeRAM = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
$cDrive = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeSpace = [math]::Round($cDrive.FreeSpace / 1GB, 1)

Write-Info "OS: $($os.Caption) ($($os.Version))"
Write-Info "CPU: $($cpu.Name)"
Write-Info "RAM: ${freeRAM}GB 여유 / ${totalRAM}GB 전체"
Write-Info "C: 드라이브: ${freeSpace}GB 여유"

if ($totalRAM -lt 8) {
    Write-Warn "RAM이 8GB 미만입니다. Cowork VM 실행에 부족할 수 있습니다."
}
if ($freeSpace -lt 15) {
    Write-Warn "C: 드라이브 여유 공간이 15GB 미만입니다. VM 번들 저장에 부족할 수 있습니다."
}

# ══════════════════════════════════════════════════════════
# 완료
# ══════════════════════════════════════════════════════════
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

if ($needsReboot) {
    Write-Host "  Windows 기능이 변경되었습니다. 재부팅이 필요합니다!" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    if (-not $SkipReboot) {
        Write-Host "  10초 후 자동 재부팅됩니다. 취소: Ctrl+C" -ForegroundColor Red
        Write-Host ""
        for ($i = 10; $i -ge 1; $i--) {
            Write-Host "  재부팅까지 ${i}초..." -ForegroundColor Yellow
            Start-Sleep -Seconds 1
        }
        Restart-Computer -Force
    } else {
        Write-Host "  -SkipReboot 옵션으로 자동 재부팅이 건너뛰어졌습니다." -ForegroundColor Yellow
        Write-Host "  반드시 수동으로 재부팅한 후 Claude Desktop을 실행하세요." -ForegroundColor Yellow
    }
} else {
    Write-Host "  모든 점검이 완료되었습니다!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "다음 단계:" -ForegroundColor White
Write-Host "  1. $(if($needsReboot){'PC 재부팅 후 '}else{''})Claude Desktop을 실행합니다" -ForegroundColor Gray
Write-Host "  2. Cowork 탭에서 워크스페이스를 시작합니다" -ForegroundColor Gray
Write-Host "  3. 마켓플레이스에서 플러그인 설치를 테스트합니다" -ForegroundColor Gray
Write-Host ""
Write-Host "추가 옵션:" -ForegroundColor White
Write-Host "  .\fix_cowork_virtiofs_mount.ps1 -ResetVM         # VM 번들 초기화" -ForegroundColor Gray
Write-Host "  .\fix_cowork_virtiofs_mount.ps1 -OptimizeWSL     # .wslconfig 최적화" -ForegroundColor Gray
Write-Host "  .\fix_cowork_virtiofs_mount.ps1 -SkipReboot      # 자동 재부팅 안 함" -ForegroundColor Gray
Write-Host "  .\fix_cowork_virtiofs_mount.ps1 -ResetVM -OptimizeWSL  # 전체 초기화" -ForegroundColor Gray
Write-Host ""
Write-Host "문제가 지속되면:" -ForegroundColor White
Write-Host "  https://github.com/anthropics/claude-code/issues/26554" -ForegroundColor Gray
Write-Host ""
