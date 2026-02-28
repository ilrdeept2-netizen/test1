# Claude Desktop 실행 즉시 종료 — 순차 해결 계획

**작성일**: 2026-02-28
**증상**: Claude Desktop 앱 실행 → 즉시(1~2초 내) 또는 수초 내 강제 종료
**목표**: Claude Cowork 기능 정상 사용

---

## 전체 흐름도

```
[0단계] 서버 상태 확인 (내 문제인지 서버 문제인지 판별)
  ↓
[1단계] 좀비 프로세스 완전 종료
  ↓
[2단계] GPU 하드웨어 가속 비활성화 + 안전 모드 실행
  ↓ 안 되면
[3단계] 캐시/세션 데이터 선별 삭제
  ↓ 안 되면
[4단계] 딥 클린 — 앱 데이터 통째로 초기화
  ↓ 안 되면
[5단계] CoworkVM 서비스 충돌 제거
  ↓ 안 되면
[6단계] 완전 재설치 (앱 제거 → 잔여 삭제 → 재부팅 → 재설치)
  ↓ 안 되면
[7단계] 시스템 레벨 점검 (드라이버, 백신, Hyper-V)
  ↓ 안 되면
[8단계] Guardian 시스템으로 영구 자동 복구 설정
  ↓ 그래도 안 되면
[대안] 웹 버전(claude.ai) 사용 + 버그 리포트
```

---

## 0단계: 서버 상태 먼저 확인

내 PC 문제인지, Anthropic 서버 문제인지 먼저 구분합니다.

### 확인 방법

1. **웹 브라우저**에서 https://claude.ai 접속
2. 정상 동작하면 → **내 PC(데스크탑 앱) 문제** → 1단계로 진행
3. 웹도 안 되면 → **서버 문제** → 기다리기

### 서버 상태 확인 사이트

- https://status.anthropic.com (공식)
- https://downdetector.com/status/claude/ (사용자 보고 기반)

> **참고**: 공식 상태 페이지가 "정상"이어도 실제 장애가 있을 수 있습니다 (유령 장애).
> 웹 버전이 정상 동작하면 서버는 괜찮다고 판단합니다.

---

## 1단계: 좀비 프로세스 완전 종료

앱이 이미 백그라운드에서 비정상 실행 중이면 새 인스턴스가 충돌합니다.

### Windows

```powershell
# 1. 작업 관리자 열기: Ctrl + Shift + Esc
# 2. "Claude" 관련 프로세스 모두 찾아서 종료 (보통 6~7개)

# 또는 PowerShell/명령 프롬프트에서:
taskkill /f /im "Claude.exe" /t
taskkill /f /im "CoworkVMService.exe" /t 2>$null
```

### macOS

```bash
pkill -9 -f "Claude"
```

### 확인

```powershell
# Windows — Claude 프로세스가 남아있지 않은지 확인
Get-Process | Where-Object { $_.Name -like "*Claude*" }
```

**이후**: Claude Desktop 다시 실행해 봅니다.
- 정상 실행되면 → **해결 완료!**
- 여전히 꺼지면 → 2단계로

---

## 2단계: GPU 하드웨어 가속 비활성화 + 안전 모드 실행

**가장 흔한 원인 (약 40%)**. Electron 기반 앱에서 GPU 드라이버와 충돌이 발생합니다.

### 방법 A: 명령어로 직접 실행 (즉시 테스트)

```powershell
# Windows
start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox
```

```bash
# macOS
open -a "Claude" --args --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox
```

### 방법 B: 설정 파일로 영구 적용

```powershell
# Windows — electron-flags.conf 생성
Set-Content -Path "$env:APPDATA\Claude\electron-flags.conf" -Value @"
--disable-gpu
--disable-gpu-compositing
--disable-gpu-sandbox
--disable-software-rasterizer
"@
```

```bash
# macOS
cat > ~/Library/Application\ Support/Claude/electron-flags.conf << 'EOF'
--disable-gpu
--disable-gpu-compositing
--disable-gpu-sandbox
--disable-software-rasterizer
EOF
```

### 방법 C: 바로가기 수정 (Windows)

1. 바탕화면 Claude 아이콘 → **마우스 오른쪽** → **속성**
2. **대상(T)** 끝에 `--disable-gpu` 추가
3. 예: `"C:\...\Claude.exe" --disable-gpu`
4. 확인 → 바로가기로 실행

**이후**: 실행 테스트
- 정상 실행 → **해결!** (GPU 충돌이 원인이었음)
- 여전히 꺼짐 → 3단계로

---

## 3단계: 캐시/세션 데이터 선별 삭제

손상된 캐시가 시작 시 크래시를 유발합니다.

### Windows

```powershell
# 1. Claude 프로세스 종료 (1단계 반복)
taskkill /f /im "Claude.exe" /t

# 2. 캐시 디렉토리 삭제
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\GPUCache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Code Cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\DawnCache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Session Storage" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\blob_storage" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Service Worker" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Claude\Cache" -ErrorAction SilentlyContinue

# 3. GPU 비활성화와 함께 실행
start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu
```

### macOS

```bash
pkill -9 -f "Claude"

rm -rf ~/Library/Application\ Support/Claude/Cache
rm -rf ~/Library/Application\ Support/Claude/GPUCache
rm -rf ~/Library/Application\ Support/Claude/Code\ Cache
rm -rf ~/Library/Application\ Support/Claude/DawnCache
rm -rf ~/Library/Application\ Support/Claude/Session\ Storage
rm -rf ~/Library/Application\ Support/Claude/blob_storage
rm -rf ~/Library/Application\ Support/Claude/Service\ Worker

open -a "Claude" --args --disable-gpu
```

**이후**: 실행 테스트
- 정상 실행 → **해결!**
- 여전히 꺼짐 → 4단계로

---

## 4단계: 딥 클린 — 앱 데이터 통째로 초기화

3단계까지 안 되면 앱 데이터 전체가 손상된 상태입니다. **완전 초기화**합니다.

> **안심**: 대화 내역은 클라우드 서버에 저장되므로 삭제되지 않습니다.

### 자동 스크립트 (Windows, 권장)

```powershell
# 이 리포지토리의 스크립트 사용
.\fix_instant_crash_deepclean.ps1

# 확인 없이 즉시 실행
.\fix_instant_crash_deepclean.ps1 -SkipConfirm

# 설정 백업 후 실행
.\fix_instant_crash_deepclean.ps1 -BackupConfig
```

### 수동 (Windows)

```powershell
# 1. 프로세스 종료
taskkill /f /im "Claude.exe" /t

# 2. 앱 데이터 전체 삭제
Remove-Item -Recurse -Force "$env:APPDATA\Claude" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Claude" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\claude-updater" -ErrorAction SilentlyContinue

# 3. GPU 비활성화 설정 다시 생성 (폴더가 없으면 만들기)
New-Item -ItemType Directory -Path "$env:APPDATA\Claude" -Force | Out-Null
Set-Content -Path "$env:APPDATA\Claude\electron-flags.conf" -Value @"
--disable-gpu
--disable-gpu-compositing
--disable-gpu-sandbox
"@

# 4. 실행
start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu
```

### 수동 (macOS)

```bash
pkill -9 -f "Claude"

rm -rf ~/Library/Application\ Support/Claude
rm -rf ~/Library/Caches/Claude

# GPU 비활성화 설정 재생성
mkdir -p ~/Library/Application\ Support/Claude
cat > ~/Library/Application\ Support/Claude/electron-flags.conf << 'EOF'
--disable-gpu
--disable-gpu-compositing
--disable-gpu-sandbox
EOF

open -a "Claude" --args --disable-gpu
```

**이후**: 실행 테스트
- 정상 실행 → **해결!** (로그인 다시 필요, 대화 내역은 서버에서 복원됨)
- 여전히 꺼짐 → 5단계로

---

## 5단계: CoworkVM 서비스 충돌 제거

Claude Cowork 설치 시 등록되는 `CoworkVMService`가 앱 전체를 크래시시킬 수 있습니다.

### Windows (관리자 권한 PowerShell 필요)

```powershell
# 1. 서비스 상태 확인
Get-Service -Name "CoworkVMService" -ErrorAction SilentlyContinue

# 2. 서비스 중지
Stop-Service -Name "CoworkVMService" -Force -ErrorAction SilentlyContinue

# 3. 서비스 삭제
sc.exe delete CoworkVMService

# "Access is denied" 오류 시 레지스트리에서 직접 제거:
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\CoworkVMService" /f

# 4. VM 관련 파일 정리
Remove-Item -Recurse -Force "$env:APPDATA\Claude\vm_bundles" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\claude-code-vm" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Packages\Claude_pzs8sxjxfjjc\LocalCache\*" -ErrorAction SilentlyContinue

# 5. PC 재부팅 필수!
Restart-Computer
```

**재부팅 후**: Claude Desktop 실행 테스트
- 정상 → **해결!** (Cowork 기능은 나중에 앱 내에서 다시 활성화)
- 여전히 꺼짐 → 6단계로

---

## 6단계: 완전 재설치

앱 자체가 손상된 경우, 처음부터 다시 설치합니다.

### 절차

```
1. 앱 제거: 설정 > 앱 > 설치된 앱 > "Claude" 찾아서 제거

2. 잔여 데이터 완전 삭제 (관리자 PowerShell):
```

```powershell
Remove-Item -Recurse -Force "$env:APPDATA\Claude" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Claude" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\Claude" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\claude-updater" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\claude-code-vm" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Packages\Claude_*" -ErrorAction SilentlyContinue
sc.exe delete CoworkVMService 2>$null
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\CoworkVMService" /f 2>$null
```

```
3. PC 재부팅

4. https://claude.com/download 에서 최신 버전 다운로드

5. 설치 후, 바로 실행하지 말고 먼저 GPU 비활성화 설정:
```

```powershell
New-Item -ItemType Directory -Path "$env:APPDATA\Claude" -Force | Out-Null
Set-Content -Path "$env:APPDATA\Claude\electron-flags.conf" -Value @"
--disable-gpu
--disable-gpu-compositing
--disable-gpu-sandbox
"@
```

```
6. 이제 Claude Desktop 실행
```

**이후**: 실행 테스트
- 정상 → **해결!**
- 여전히 꺼짐 → 7단계로

---

## 7단계: 시스템 레벨 점검

앱이 아니라 시스템 환경 자체에 문제가 있을 수 있습니다.

### 7-A. GPU 드라이버 업데이트

1. `Win + R` → `dxdiag` → GPU 모델 확인
2. 제조사 사이트에서 최신 드라이버 설치:
   - Intel: https://www.intel.com/content/www/us/en/download-center
   - NVIDIA: https://www.nvidia.com/Download/index.aspx
   - AMD: https://www.amd.com/en/support

### 7-B. 백신/보안 소프트웨어 예외 등록

V3, 알약 등 한국 백신이 Electron 프로세스를 차단할 수 있습니다.

```
예외 등록 경로:
- %LOCALAPPDATA%\Programs\Claude\
- %APPDATA%\Claude\
- Claude.exe
```

```powershell
# Windows Defender 예외 등록 (관리자 PowerShell)
Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\Programs\Claude"
Add-MpPreference -ExclusionPath "$env:APPDATA\Claude"
```

### 7-C. Hyper-V 확인 (Cowork 사용 시)

Cowork는 Hyper-V 기반 VM을 사용합니다.

> **Windows 11 Home은 Hyper-V 미지원** → Cowork 사용 불가 (기본 채팅은 가능)

Windows 11 Pro/Enterprise:

1. 설정 > 앱 > 선택적 기능 > Windows 기능 켜기/끄기
2. 다음 항목 체크:
   - Hyper-V
   - Virtual Machine Platform
   - Windows Hypervisor Platform
3. PC 재부팅
4. BIOS에서 Intel VT-x / AMD-V 가상화 활성화 확인

### 7-D. 개발자 모드 활성화

```
설정 > 개인 정보 및 보안 > 개발자용 > 개발자 모드 ON
설정 > 앱 > 고급 앱 설정 > 앱 사이드로딩 허용
```

### 7-E. PowerShell PATH 확인

```powershell
where.exe powershell.exe
# 결과가 없으면 PATH에 추가: C:\Windows\System32\WindowsPowerShell\v1.0\
```

---

## 8단계: Guardian 시스템으로 영구 자동 복구

해결이 됐더라도 **업데이트 시 설정이 리셋**되어 크래시가 재발할 수 있습니다.
Guardian을 설치하면 시스템 시작 시 자동으로 안정성 설정을 복구합니다.

### Windows

```powershell
# 이 리포지토리에서:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\claude_desktop_guardian.ps1 -Install
```

### macOS

```bash
chmod +x claude_desktop_guardian.sh
./claude_desktop_guardian.sh install
```

### Guardian이 해주는 일

- 시스템 시작 시 GPU 비활성화 설정 자동 복구
- 업데이트로 리셋된 설정 자동 감지 및 재적용
- 크래시 감지 시 자동 안전 모드 재시작
- 손상된 캐시 자동 정리

---

## 대안: 웹 버전 사용

위 모든 단계를 거쳐도 해결되지 않으면, 데스크탑 앱 대신 웹 버전을 사용합니다.

- **URL**: https://claude.ai
- 동일한 계정으로 로그인하면 대화 내역 동일
- Cowork 기능도 웹에서 사용 가능

### 버그 리포트 제출

```powershell
# 로그 수집
explorer "$env:APPDATA\Claude\logs"

# 시스템 정보
systeminfo > system_info.txt
dxdiag /t dxdiag_output.txt
```

제출처: https://github.com/anthropics/claude-code/issues

포함할 정보:
- Claude Desktop 버전
- Windows 버전 (`winver`)
- GPU 정보 (`dxdiag`)
- 로그 파일 (`%APPDATA%\Claude\logs\`)
- 어느 단계까지 시도했는지

---

## 빠른 참조 — "지금 당장 실행하고 싶다"

시간이 없으면 아래 3줄만 실행하세요:

### Windows (PowerShell)

```powershell
taskkill /f /im "Claude.exe" /t
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Cache","$env:APPDATA\Claude\GPUCache","$env:APPDATA\Claude\Session Storage" -ErrorAction SilentlyContinue
start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox
```

### macOS (터미널)

```bash
pkill -9 -f Claude; rm -rf ~/Library/Application\ Support/Claude/{Cache,GPUCache,Session\ Storage}; open -a Claude --args --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox
```

---

## 관련 파일 (이 리포지토리)

| 파일 | 용도 |
|------|------|
| `fix_instant_crash_deepclean.ps1` | 4단계 자동 딥 클린 스크립트 |
| `fix_claude_desktop_crash.ps1` | 일회성 진단/수정 도구 |
| `fix_cowork_vhdx_access.ps1` | Cowork VM 권한 수정 |
| `claude_desktop_guardian.ps1` | Windows Guardian (영구 해결) |
| `claude_desktop_guardian.sh` | macOS Guardian (영구 해결) |
| `CLAUDE_DESKTOP_크래시_근본해결.md` | 근본 원인 분석 + Guardian 설명 |
| `CLAUDE_DESKTOP_CRASH_FIX_GUIDE.md` | 기존 7단계 가이드 |
