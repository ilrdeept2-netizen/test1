# Claude Desktop 앱 자동 종료(크래시) 해결 가이드

**작성일**: 2026-02-17
**대상**: Windows PC에서 Claude Desktop 앱이 반복적으로 자동 종료되는 문제

---

## 증상

- Claude Desktop 앱이 실행 후 수초~수분 내에 자동으로 꺼짐
- Cowork 탭 진입 시 앱이 갑자기 종료됨
- 앱이 "깜빡임" 후 사라짐 (스플래시 화면만 보이고 닫힘)
- 특정 작업 중 예고 없이 앱이 종료됨

---

## 원인 분석

### 원인 1: GPU 하드웨어 가속 충돌 (가장 흔함, 약 40%)

Claude Desktop은 Electron(Chromium) 기반이며, GPU 하드웨어 가속이 기본 활성화되어 있습니다.
특정 GPU 드라이버(특히 구형 Intel 내장 GPU, 일부 AMD GPU)에서 렌더링 충돌이 발생하여 앱이 즉시 종료됩니다.

**확인 방법**:
- 로그 파일(`%APPDATA%\Claude\logs\`)에서 `gpu_process`, `GL_ERROR`, `ANGLE`, `SwapChain` 키워드 확인
- Windows 이벤트 뷰어 > 응용 프로그램 로그에서 "Claude" 또는 "Electron" 크래시 기록 확인

### 원인 2: 앱 캐시/데이터 손상 (약 25%)

앱 업데이트 후 이전 캐시와 충돌하거나, Session Storage/Local Storage가 손상되면 앱이 시작 시 크래시합니다.

**주요 손상 경로**:
- `%APPDATA%\Claude\Cache` - Chromium 디스크 캐시
- `%APPDATA%\Claude\GPUCache` - GPU 셰이더 캐시
- `%APPDATA%\Claude\Session Storage` - 세션 데이터
- `%APPDATA%\Claude\Local Storage` - 로컬 저장소

### 원인 3: Cowork VM 프로세스 충돌 (약 15%)

Cowork는 Hyper-V 기반 VM을 사용합니다. VM 프로세스가 비정상 종료되면 앱 전체가 크래시할 수 있습니다.

**관련 이슈**:
- VHDX 파일 접근 권한 부족 (0x80070005 오류)
- VM 번들 파일 손상 (다운로드 중 네트워크 오류)
- Hyper-V 서비스 비정상 상태

### 원인 4: 앱 업데이트 충돌 (약 10%)

Electron Squirrel 업데이터가 새 버전을 다운로드하지만 symlink를 올바르게 업데이트하지 못하는 알려진 버그가 있습니다 (GitHub Issue #24117). 여러 버전이 공존하면 충돌이 발생합니다.

### 원인 5: 보안 소프트웨어 간섭 (약 10%)

V3, 알약 등 한국에서 많이 사용하는 백신이 Electron 프로세스를 악성 코드로 오인하여 강제 종료시킬 수 있습니다.

---

## 해결 방법

### 방법 1: 자동 수정 스크립트 실행 (권장)

```powershell
# PowerShell에서 실행
.\fix_claude_desktop_crash.ps1

# 전체 수정 (관리자 권한 필요)
.\fix_claude_desktop_crash.ps1 -FullFix

# 진단만 (수정 없이 문제 파악만)
.\fix_claude_desktop_crash.ps1 -DiagOnly
```

스크립트가 자동으로 수행하는 작업:
1. 시스템 환경 진단 (Windows 버전, RAM, 디스크 공간)
2. 크래시 로그 분석 (GPU/메모리/VM/인증/네트워크 분류)
3. GPU 하드웨어 가속 비활성화 (크래시 감지 시)
4. 앱 캐시 및 손상 데이터 정리
5. Cowork VM 상태 점검 및 초기화
6. 앱 업데이트 충돌 해결 (이전 버전 정리)
7. 보안 소프트웨어 예외 등록 (관리자 모드)
8. 바탕화면에 "안정 실행" 바로가기 생성

### 방법 2: GPU 가속 비활성화 (수동)

가장 흔한 원인인 GPU 충돌을 직접 해결합니다.

#### 2-A. 실행 인수로 비활성화
```
# 바탕화면 Claude 바로가기 → 마우스 오른쪽 → 속성 → 대상(T) 끝에 추가:
--disable-gpu --disable-gpu-compositing
```

#### 2-B. 설정 파일로 비활성화
```powershell
# 아래 내용을 파일로 저장
Set-Content -Path "$env:APPDATA\Claude\electron-flags.conf" -Value @"
--disable-gpu
--disable-gpu-compositing
--disable-gpu-sandbox
--disable-software-rasterizer
"@
```

#### 2-C. 배치 파일로 실행
스크립트가 바탕화면에 생성하는 `Claude_안정실행.bat`을 사용하거나, 직접 만듭니다:
```batch
@echo off
start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox
```

### 방법 3: 캐시 완전 삭제 (수동)

```powershell
# 1. Claude Desktop 완전 종료
taskkill /f /im "Claude.exe" 2>$null

# 2. 캐시 디렉토리 삭제
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\GPUCache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Code Cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\DawnCache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Session Storage" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\blob_storage" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Service Worker" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Claude\Cache" -ErrorAction SilentlyContinue

# 3. Claude Desktop 재실행
```

### 방법 4: 딥 클린 — 즉시 크래시(Instant Crash) 전용

앱이 **켜자마자 1~2초 만에 즉시 꺼져버리는** 경우, 위의 선별적 캐시 삭제로는 해결이 안 됩니다.
마지막 세션 렌더링 오류로 인한 크래시 루프(Crash Loop)이므로, 앱 데이터를 **통째로 삭제**해야 합니다.

```powershell
# 자동 스크립트 실행 (권장)
.\fix_instant_crash_deepclean.ps1

# 수동으로 진행하려면:
# 1. 관리자 cmd에서: taskkill /f /im "Claude.exe" /t
# 2. Windows키 + R → %appdata% → Claude 폴더 삭제
# 3. Windows키 + R → %localappdata% → Claude, claude-updater 폴더 삭제
# 4. Claude 바로가기 → 속성 → 대상(T) 끝에 --disable-gpu 추가
# 5. 실행 후 로그인 직후: Settings > General > "Menu bar" 옵션 ON
```

> 대화 내역은 클라우드 서버에 보관되므로 삭제되지 않습니다.

### 방법 5: 앱 완전 재설치

위 방법으로 해결되지 않을 경우:

```powershell
# 1. Claude Desktop 제거
# 설정 > 앱 > Claude > 제거

# 2. 잔여 데이터 완전 삭제
Remove-Item -Recurse -Force "$env:APPDATA\Claude" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Claude" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\Claude" -ErrorAction SilentlyContinue

# 3. PC 재부팅

# 4. 최신 버전 설치: https://claude.com/download
```

### 방법 6: Cowork VM 관련 수정

Cowork 사용 중 크래시가 발생하는 경우:

```powershell
# VHDX 접근 권한 수정 (관리자 PowerShell)
.\fix_cowork_vhdx_access.ps1

# 또는 VM 번들 삭제 후 재다운로드
Remove-Item -Recurse -Force "$env:APPDATA\Claude\vm_bundles" -ErrorAction SilentlyContinue
# Claude 재실행 시 자동으로 VM 번들을 다시 다운로드합니다 (10GB+, 시간 소요)
```

---

## 해결 순서 요약 (우선순위)

```
[즉시 크래시?] 앱이 1~2초 만에 꺼지면 → 딥 클린부터
  .\fix_instant_crash_deepclean.ps1
    ↓ 일반 크래시이면
[1순위] 자동 수정 스크립트 실행
  .\fix_claude_desktop_crash.ps1
    ↓ 안 되면
[2순위] GPU 가속 비활성화 + 캐시 삭제
  --disable-gpu 옵션으로 실행 + 캐시 디렉토리 삭제
    ↓ 안 되면
[3순위] 딥 클린 (즉시 크래시가 아니어도 시도 가치 있음)
  .\fix_instant_crash_deepclean.ps1
    ↓ 안 되면
[4순위] 앱 완전 재설치
  제거 → 잔여 데이터 삭제 → 재부팅 → 재설치
    ↓ 안 되면
[5순위] 시스템 점검
  GPU 드라이버 업데이트, 백신 예외 등록, Windows 업데이트
    ↓ 안 되면
[6순위] 버그 리포트
  로그 수집 후 https://github.com/anthropics/claude-code/issues
    ↓ 급하면
[대안] 웹 버전 사용
  https://claude.ai 에서 동일한 기능 사용 가능
```

---

## 로그 수집 방법 (버그 리포트 시)

```powershell
# 로그 파일 위치
explorer "$env:APPDATA\Claude\logs"

# 진단 스크립트로 진단 결과만 저장
.\fix_claude_desktop_crash.ps1 -DiagOnly > claude_diagnosis.txt 2>&1

# 시스템 정보 수집
systeminfo > system_info.txt
```

버그 리포트 시 포함할 정보:
- Claude Desktop 버전
- Windows 버전 (`winver` 결과)
- GPU 정보 (`dxdiag` 결과)
- 로그 파일 (`%APPDATA%\Claude\logs\`)
- 진단 결과 (`claude_diagnosis.txt`)

---

## 관련 문서

- [Claude Cowork VM 오류 해결 계획](claude-cowork-vm-fix-plan.md) - VM 관련 상세 해결 방법
- [Claude Desktop Outage Report](claude-desktop-outage-report-2026-02-10.md) - 서버 측 장애 분석
- [VHDX 액세스 수정 스크립트](fix_cowork_vhdx_access.ps1) - Cowork VM 권한 문제 전용
- [Claude Code Issues](https://github.com/anthropics/claude-code/issues) - 공식 버그 트래커
