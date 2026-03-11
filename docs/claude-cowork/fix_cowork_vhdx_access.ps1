#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Claude Cowork VM VHDX 액세스 거부(0x80070005) 오류 자동 수정 스크립트

.DESCRIPTION
    Hyper-V VM이 rootfs.vhdx 파일에 접근하지 못하는 문제를 해결합니다.
    주요 원인:
      1) Hyper-V VM Worker Process에 VHDX 파일 접근 권한 부족
      2) 한글 사용자 이름 경로의 Hyper-V 호환성 문제
      3) VHDX 파일이 다른 프로세스에 의해 잠겨 있는 경우

.NOTES
    반드시 "관리자 권한으로 실행"한 PowerShell에서 실행하세요.
    실행 방법: PowerShell(관리자) -> .\fix_cowork_vhdx_access.ps1

.PARAMETER SkipJunction
    한글 경로 Junction 생성을 건너뜁니다.

.PARAMETER Force
    확인 없이 강제 실행합니다.
#>

param(
    [switch]$SkipJunction,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step  { param($msg) Write-Host "`n[$((Get-Date).ToString('HH:mm:ss'))] " -NoNewline -ForegroundColor Cyan; Write-Host $msg -ForegroundColor White }
function Write-OK    { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "  [X] $msg" -ForegroundColor Red }
function Write-Info  { param($msg) Write-Host "  [i] $msg" -ForegroundColor Gray }

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Claude Cowork VM VHDX 액세스 오류 수정 도구" -ForegroundColor White
Write-Host "  오류 코드: 0x80070005 (액세스가 거부되었습니다)" -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Cyan

# ── Phase 0: 관리자 권한 확인 ──
Write-Step "Phase 0: 관리자 권한 확인"
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Err "관리자 권한이 필요합니다."
    Write-Info "PowerShell -> 마우스 오른쪽 클릭 -> '관리자 권한으로 실행'"
    exit 1
}
Write-OK "관리자 권한 확인됨"

# ── Phase 1: Hyper-V 서비스 확인 ──
Write-Step "Phase 1: Hyper-V 서비스 상태 확인"
$hvService = Get-Service -Name "vmms" -ErrorAction SilentlyContinue
if ($null -eq $hvService) {
    Write-Err "Hyper-V가 설치되어 있지 않습니다."
    Write-Info "설치 명령: dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart"
    Write-Info "설치 후 PC 재부팅이 필요합니다."
    exit 1
}
if ($hvService.Status -ne "Running") {
    Write-Warn "Hyper-V 서비스 중지 상태. 시작합니다..."
    Start-Service -Name "vmms"
    Start-Sleep -Seconds 2
}
Write-OK "Hyper-V 서비스 실행 중"

# ── Phase 2: VHDX 파일 탐색 ──
Write-Step "Phase 2: VHDX 파일 탐색"
$vhdxPaths = @()
$searchDirs = @("$env:APPDATA\Claude\vm_bundles", "$env:LOCALAPPDATA\Claude\vm_bundles")

foreach ($dir in $searchDirs) {
    if (Test-Path $dir) {
        $found = Get-ChildItem -Path $dir -Filter "*.vhdx" -Recurse -ErrorAction SilentlyContinue
        foreach ($f in $found) {
            $vhdxPaths += $f.FullName
            Write-Info "발견: $($f.FullName) ($([math]::Round($f.Length / 1GB, 2)) GB)"
        }
    }
}
if ($vhdxPaths.Count -eq 0) {
    Write-Err "VHDX 파일을 찾을 수 없습니다."
    Write-Info "Claude Desktop에서 Cowork 워크스페이스를 먼저 설치하세요."
    exit 1
}
Write-OK "$($vhdxPaths.Count)개의 VHDX 파일 발견"

# ── Phase 3: Claude 프로세스 종료 ──
Write-Step "Phase 3: Claude 프로세스 종료 (파일 잠금 해제)"
$claudeProcs = Get-Process -Name "Claude*" -ErrorAction SilentlyContinue
if ($claudeProcs) {
    Write-Warn "Claude 프로세스 $($claudeProcs.Count)개 종료 중..."
    $claudeProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-OK "종료 완료"
} else {
    Write-OK "실행 중인 Claude 프로세스 없음"
}

# 기존 cowork-vm 중지
$vm = Get-VM -Name "cowork-vm" -ErrorAction SilentlyContinue
if ($null -ne $vm -and $vm.State -ne "Off") {
    Write-Warn "cowork-vm 중지 중..."
    Stop-VM -Name "cowork-vm" -TurnOff -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-OK "VM 중지 완료"
}

# ── Phase 4: NTFS 권한 수정 (핵심) ──
Write-Step "Phase 4: VHDX 파일 NTFS 권한 수정 (핵심 수정)"

# Hyper-V VM Worker Process SID
$hvSid = New-Object System.Security.Principal.SecurityIdentifier("S-1-5-83-0")
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

foreach ($vhdxPath in $vhdxPaths) {
    Write-Info "처리: $vhdxPath"

    # 상위 디렉토리들에 ReadAndExecute 권한 부여
    $parentDir = Split-Path -Parent $vhdxPath
    $grandParentDir = Split-Path -Parent $parentDir

    foreach ($dir in @($grandParentDir, $parentDir)) {
        if (Test-Path $dir) {
            try {
                $acl = Get-Acl -Path $dir
                $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                    $hvSid, "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow"
                )
                $acl.AddAccessRule($rule)
                Set-Acl -Path $dir -AclObject $acl
            } catch {
                Write-Warn "디렉토리 권한 설정 실패: $dir - $($_.Exception.Message)"
            }
        }
    }

    # VHDX 파일에 Hyper-V Read 권한 부여
    try {
        $acl = Get-Acl -Path $vhdxPath
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $hvSid, "Read", "None", "None", "Allow"
        )
        $acl.AddAccessRule($rule)

        # 현재 사용자에게 FullControl 보장
        $rule2 = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $currentUser, "FullControl", "None", "None", "Allow"
        )
        $acl.AddAccessRule($rule2)

        Set-Acl -Path $vhdxPath -AclObject $acl
        Write-OK "권한 수정 완료: $vhdxPath"
    } catch {
        Write-Err "VHDX 권한 수정 실패: $($_.Exception.Message)"
    }
}

# ── Phase 5: 한글 경로 호환성 (Junction) ──
Write-Step "Phase 5: 한글 경로 호환성 확인"

$hasUnicodePath = $false
foreach ($p in $vhdxPaths) {
    if ($p -match '[^\x00-\x7F]') { $hasUnicodePath = $true; break }
}

if ($hasUnicodePath -and (-not $SkipJunction)) {
    Write-Warn "한글이 포함된 경로 감지됨 (예: C:\Users\이종원\...)"
    Write-Info "ASCII 전용 경로(C:\ClaudeVM)로 VM 번들을 이동하고 Junction을 생성합니다."

    $asciiBase = "C:\ClaudeVM"
    $asciiVmBundles = "$asciiBase\vm_bundles"
    $originalVmBundles = "$env:APPDATA\Claude\vm_bundles"

    if (Test-Path $originalVmBundles) {
        # ASCII 기본 디렉토리 생성
        if (-not (Test-Path $asciiBase)) {
            New-Item -ItemType Directory -Path $asciiBase -Force | Out-Null
        }

        # 기존 Junction 제거
        if (Test-Path $asciiVmBundles) {
            $item = Get-Item $asciiVmBundles -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                cmd /c "rmdir `"$asciiVmBundles`"" 2>$null
            }
        }

        # 원본이 Junction이 아닌 경우에만 이동
        $origItem = Get-Item $originalVmBundles -Force
        if (-not ($origItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            if (-not (Test-Path $asciiVmBundles)) {
                Write-Info "파일 이동 중 (용량이 크면 시간이 걸릴 수 있습니다)..."
                Move-Item -Path $originalVmBundles -Destination $asciiVmBundles -Force
                Write-OK "이동 완료: -> $asciiVmBundles"
            }

            # 원래 위치에 Junction 생성
            if (-not (Test-Path $originalVmBundles)) {
                cmd /c "mklink /J `"$originalVmBundles`" `"$asciiVmBundles`""
                if ($LASTEXITCODE -eq 0) {
                    Write-OK "Junction 생성: $originalVmBundles -> $asciiVmBundles"
                } else {
                    Write-Err "Junction 생성 실패. 수동 명령:"
                    Write-Info "  mklink /J `"$originalVmBundles`" `"$asciiVmBundles`""
                }
            }
        } else {
            Write-OK "이미 Junction이 설정되어 있습니다"
        }

        # ASCII 경로 VHDX에도 권한 부여
        if (Test-Path $asciiVmBundles) {
            $acl = Get-Acl -Path $asciiBase
            $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                $hvSid, "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow"
            )
            $acl.AddAccessRule($rule)
            Set-Acl -Path $asciiBase -AclObject $acl

            Get-ChildItem -Path $asciiVmBundles -Filter "*.vhdx" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
                $acl = Get-Acl -Path $_.FullName
                $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                    $hvSid, "Read", "None", "None", "Allow"
                )
                $acl.AddAccessRule($rule)
                Set-Acl -Path $_.FullName -AclObject $acl
            }
            Write-OK "ASCII 경로 권한 설정 완료"
        }
    }
} elseif ($hasUnicodePath) {
    Write-Warn "한글 경로 감지됨. -SkipJunction 으로 Junction 생성이 건너뛰어졌습니다."
} else {
    Write-OK "경로에 비ASCII 문자 없음. 추가 조치 불필요"
}

# ── Phase 6: 검증 ──
Write-Step "Phase 6: 수정 결과 검증"
$allGood = $true
foreach ($vhdxPath in $vhdxPaths) {
    if (Test-Path $vhdxPath) {
        $acl = Get-Acl -Path $vhdxPath
        $hvAccess = $acl.Access | Where-Object {
            $_.IdentityReference.Value -match "S-1-5-83-0" -or $_.IdentityReference.Value -match "Virtual Machines"
        }
        if ($hvAccess) { Write-OK "권한 확인됨: $vhdxPath" }
        else { Write-Warn "권한 미확인: $vhdxPath"; $allGood = $false }
    }
}

# ── 완료 ──
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "  모든 수정이 완료되었습니다!" -ForegroundColor Green
} else {
    Write-Host "  수정 완료 (일부 항목 수동 확인 필요)" -ForegroundColor Yellow
}
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor White
Write-Host "  1. Claude Desktop을 실행합니다" -ForegroundColor Gray
Write-Host "  2. Cowork 탭에서 워크스페이스를 시작합니다" -ForegroundColor Gray
Write-Host "  3. 문제가 지속되면 PC를 재부팅 후 다시 시도하세요" -ForegroundColor Gray
Write-Host ""
if ($hasUnicodePath -and (-not $SkipJunction)) {
    Write-Host "[참고] 한글 경로 해결:" -ForegroundColor Yellow
    Write-Host "  VM 번들 -> C:\ClaudeVM\vm_bundles (실제 파일)" -ForegroundColor Gray
    Write-Host "  원래 경로 -> Junction으로 연결 (Claude Desktop 호환)" -ForegroundColor Gray
    Write-Host ""
}
