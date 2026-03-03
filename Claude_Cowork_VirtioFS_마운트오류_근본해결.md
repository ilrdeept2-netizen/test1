# Claude Cowork VirtioFS/Plan9 마운트 오류 근본 해결 가이드

**에러 메시지**: `RPC error -1: failed to ensure virtiofs mount: Plan9 mount failed: bad address`
**환경**: Windows 11, Claude Desktop Cowork
**최종 업데이트**: 2026-03-03

---

## 에러 분석

### 무슨 에러인가?

Claude Cowork는 Windows에서 **경량 Linux VM**을 실행하고, 호스트(Windows)와 게스트(VM) 간 파일을 공유하기 위해 **VirtioFS (Plan9/9P 프로토콜)** 를 사용합니다.

```
Windows (호스트)                    Linux VM (게스트)
┌──────────────┐                  ┌──────────────┐
│  사용자 파일   │ ── VirtioFS ──→ │  /mnt/host   │
│  C:\Users\... │    (Plan9)      │  마운트 포인트  │
└──────────────┘                  └──────────────┘
        ↑
     여기서 "bad address" 발생
     = 마운트 주소를 찾을 수 없음
```

**"bad address"** = VM이 호스트 파일 시스템을 마운트하려 했으나, **Windows Hypervisor Platform이 비활성** 이거나 **리소스 누수**로 인해 마운트 주소가 유효하지 않은 상태.

### 마운트 프로세스 상세

`sandbox-helper` 프로세스가 마운트를 관리하며, 두 프로토콜을 순차적으로 시도합니다:
1. **VirtioFS** (우선) → 실패 시
2. **Plan9** (폴백) → 둘 다 실패하면 `bad address` 에러 발생

### 이 에러가 발생하는 6가지 근본 원인

| # | 원인 | 증상 | 발생 빈도 |
|---|------|------|-----------|
| 1 | **`HypervisorPlatform` 미활성화** | Cowork 시작하자마자 에러 | ★★★★★ |
| 2 | **손상된 VM 상태/캐시** | VM 크래시, 절전모드, 강제종료 후 에러 | ★★★★☆ |
| 3 | **OneDrive 동기화 폴더** | 프로젝트가 OneDrive 경로에 있을 때 | ★★★☆☆ |
| 4 | **NAT 네트워크 충돌** | VPN이 `172.16.0.0/24` 대역 사용 시 | ★★★☆☆ |
| 5 | **Windows 특수 폴더** | Downloads, Documents 등에서 작업 시 | ★★☆☆☆ |
| 6 | **VirtioFS 리소스 누수** | 45분~1시간 사용 후 갑자기 에러 (Anthropic 버그) | ★★☆☆☆ |

---

## 근본 해결 (순서대로 진행)

### Step 1: Windows Hypervisor Platform 확인 및 활성화 (가장 중요)

**PowerShell을 관리자 권한으로 실행**하고:

```powershell
# 현재 상태 확인
Get-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform
Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
```

3개 모두 `State: Enabled`여야 합니다. 하나라도 `Disabled`면:

```powershell
# 누락된 기능 활성화
Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -All -NoRestart
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All -NoRestart

# 반드시 재부팅
Restart-Computer
```

> **핵심**: 많은 사용자가 `Hyper-V`와 `VirtualMachinePlatform`만 켜고 `HypervisorPlatform`은 빠뜨립니다.
> VirtioFS가 정상 작동하려면 **3개 모두** 활성화되어야 합니다.

### Step 2: WSL2 최신 버전 업데이트

```powershell
# WSL 업데이트 (커널 + VirtioFS 드라이버 포함)
wsl --update

# 기본 버전을 WSL2로 설정
wsl --set-default-version 2

# WSL 상태 확인
wsl --status
```

WSL2 커널에 VirtioFS 드라이버가 포함되어 있어, 업데이트만으로도 마운트 안정성이 크게 개선됩니다.

### Step 3: Cowork VM 완전 초기화

```powershell
# 1) Claude Desktop 완전 종료
Get-Process -Name "Claude*" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# 2) 기존 cowork-vm 삭제 (있으면)
$vm = Get-VM -Name "cowork-vm" -ErrorAction SilentlyContinue
if ($vm) {
    Stop-VM -Name "cowork-vm" -TurnOff -Force -ErrorAction SilentlyContinue
    Remove-VM -Name "cowork-vm" -Force -ErrorAction SilentlyContinue
}

# 3) VM 번들 삭제 (새로 다운로드하게 함)
Remove-Item -Path "$env:APPDATA\Claude\vm_bundles" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:LOCALAPPDATA\Claude\vm_bundles" -Recurse -Force -ErrorAction SilentlyContinue

# 4) VM 소켓/캐시 정리
Remove-Item -Path "$env:APPDATA\Claude\vm_state" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:TEMP\claude-vm-*" -Recurse -Force -ErrorAction SilentlyContinue

# 5) Claude Desktop 재실행 → VM 번들 자동 재다운로드
```

### Step 4: OneDrive/특수 폴더 회피

OneDrive 동기화 폴더와 Windows 특수 폴더(Downloads, Documents, Desktop)에서는 VirtioFS 마운트가 실패합니다.

```
❌ 사용 금지 경로:
- C:\Users\이름\OneDrive\...         (OneDrive 클라우드 파일 API 충돌)
- C:\Users\이름\Downloads\...        (Windows Known Folder 잠금)
- C:\Users\이름\Documents\...        (Windows Known Folder 잠금)
- C:\Users\이름\Desktop\...          (Windows Known Folder 잠금)

✅ 권장 경로:
- C:\Users\이름\Projects\...         (일반 로컬 폴더)
- C:\dev\...                         (ASCII 경로, 짧고 안전)
- D:\workspace\...                   (별도 드라이브)
```

### Step 5: VPN/NAT 충돌 해결

Cowork는 내부 NAT에 `172.16.0.0/24` 대역을 사용합니다. VPN이 같은 대역을 쓰면 충돌합니다.

```powershell
# 1) VPN 완전 종료 (트레이에서 Exit) 후 테스트

# 2) 충돌하는 NAT 네트워크 재생성 (관리자 PowerShell)
Get-HnsNetwork | Where-Object { $_.Name -eq "cowork-vm-nat" } | Remove-HnsNetwork

# 3) DNS 수동 설정 (VM 네트워크 어댑터)
Set-DnsClientServerAddress -InterfaceAlias "vEthernet (cowork-vm-nat)" -ServerAddresses ("8.8.8.8","8.8.4.4")
```

V3, 알약 등 국산 백신의 실시간 보호도 VM 프로세스를 차단할 수 있으니 일시 중지 후 테스트하세요.

### Step 6: 메모리/리소스 여유 확보 (시간 경과 후 에러 방지)

```
✅ 확인 사항:
- RAM 16GB 이상 권장 (VM이 약 4GB 사용)
- C: 드라이브 여유 공간 20GB 이상
- 불필요한 프로그램 종료 후 Cowork 사용
- 작업 관리자에서 "Vmmem" 프로세스 메모리 사용량 모니터링
```

---

## 자동 수정 스크립트

> `fix_cowork_virtiofs_mount.ps1` 스크립트를 제공합니다.

```powershell
# 관리자 권한 PowerShell에서 실행:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\fix_cowork_virtiofs_mount.ps1
```

---

## "시간 경과 후 에러" (45분~1시간 후 크래시) 대처법

이 패턴은 **VirtioFS 리소스 누수**가 원인으로, Anthropic 측 수정이 필요한 알려진 버그입니다.

### 임시 대처법

1. **에러 발생 시 Cowork 탭 닫고 다시 열기** (가장 간단)
2. **주기적으로 VM 재시작**:
   - Cowork 설정 → 워크스페이스 재시작
3. **.wslconfig로 메모리 제한 완화**:

```ini
# %USERPROFILE%\.wslconfig 파일 생성/수정
[wsl2]
memory=8GB
processors=4
swap=4GB
```

4. **Projected File System 활성화** (일부 사용자에게 효과):

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Client-ProjFS -All -NoRestart
Restart-Computer
```

---

## 마켓플레이스 로딩 실패 해결

마켓플레이스 에러도 동일한 VirtioFS 마운트 실패가 원인입니다.

```
에러: "마켓플레이스를 불러오지 못했습니다"
원인: VM 파일 시스템 마운트 실패 → 플러그인 목록 조회 불가
해결: 위 Step 1~4 진행 후 → Cowork 재시작 → 마켓플레이스 재접근
```

플러그인 설치 시에도 같은 에러가 발생하면:
1. Cowork 워크스페이스 재시작
2. 재시작 직후(마운트가 안정적일 때) 바로 플러그인 설치

---

## 해결 우선순위 요약

```
[1순위] Step 1: HypervisorPlatform 활성화 + 재부팅
         → 대부분의 "시작 시 에러" 해결
   ↓ 안 되면
[2순위] Step 2: WSL2 업데이트
         → VirtioFS 드라이버 최신화
   ↓ 안 되면
[3순위] Step 3: VM 번들 완전 초기화
         → 손상된 VM 이미지/캐시 교체
   ↓ 안 되면
[4순위] Step 4: OneDrive/특수 폴더 회피
         → 프로젝트를 일반 로컬 폴더로 이동
   ↓ 안 되면
[5순위] Step 5: VPN/NAT/백신 확인
         → 네트워크 충돌 및 소켓 간섭 제거
   ↓ 시간 경과 후 에러면
[별도]   .wslconfig 튜닝 + Projected File System 활성화
         → 리소스 누수 완화 (근본 해결은 Anthropic 패치 대기)
```

## 빠른 임시 해결 (당장 급할 때)

위 단계를 밟기 전에 빠르게 시도해볼 수 있는 방법:

```powershell
# 1) Cowork VM 서비스 재시작 (관리자 PowerShell)
taskkill /F /IM Claude.exe 2>$null
net stop CoworkVMService 2>$null
Remove-Item -Path "$env:TEMP\claude*" -Recurse -Force -ErrorAction SilentlyContinue
net start CoworkVMService 2>$null

# 2) Claude Desktop 재실행
```

이것만으로도 손상된 마운트 캐시가 정리되어 에러가 해결되는 경우가 많습니다.

---

## 관련 GitHub Issues

| Issue | 설명 | 상태 |
|-------|------|------|
| [#26554](https://github.com/anthropics/claude-code/issues/26554) | VirtioFS/Plan9 mount fails: bad address | Open |
| [#27576](https://github.com/anthropics/claude-code/issues/27576) | VirtioFS mount failure after ~1 hour | Open |
| [#26873](https://github.com/anthropics/claude-code/issues/26873) | Win 11 Home + Team plan: Plan9 mount failed | Open |
| [#26994](https://github.com/anthropics/claude-code/issues/26994) | Plugin install fails with same RPC error | Open |
| [#29848](https://github.com/anthropics/claude-code/issues/29848) | Cowork completely unusable on Windows | Open |

---

## Sources

- [GitHub Issue #26554 - VirtioFS/Plan9 mount fails](https://github.com/anthropics/claude-code/issues/26554)
- [GitHub Issue #29848 - Cowork completely unusable on Windows](https://github.com/anthropics/claude-code/issues/29848)
- [GitHub Issue #27576 - VirtioFS mount failure after ~1 hour](https://github.com/anthropics/claude-code/issues/27576)
- [GitHub Issue #26873 - Win 11 Home + Team plan failure](https://github.com/anthropics/claude-code/issues/26873)
- [GitHub Issue #25293 - OneDrive-synced folders fail](https://github.com/anthropics/claude-code/issues/25293)
- [GitHub Issue #25235 - Downloads folder fails to mount](https://github.com/anthropics/claude-code/issues/25235)
- [Mobile01 - Claude Cowork VM 오류 해결 경험 공유](https://www.mobile01.com/topicdetail.php?f=14&t=7229575)
- [Jonas Kamsker - Broken by Default: Claude Cowork on Windows](https://blog.kamsker.at/blog/cowork-windows-broken/)
- [Elliot Segler - Fixing Claude Cowork's Network Conflict on Windows](https://www.elliotsegler.com/fixing-claude-coworks-network-conflict-on-windows.html)
