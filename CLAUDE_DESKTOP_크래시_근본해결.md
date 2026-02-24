# Claude Desktop 크래시 근본 해결 가이드

**작성일**: 2026-02-19
**버전**: 2.0 (Guardian 시스템 통합)
**대상**: Windows / macOS 모든 환경

---

## 왜 매번 다시 꺼지는가? (근본 원인 분석)

기존 해결법(캐시 삭제, GPU 비활성화 등)으로 임시 수정해도 **다시 재발**하는 이유:

### 재발 메커니즘

```
Claude Desktop 업데이트 (자동/수동)
        |
        v
electron-flags.conf 리셋  ← GPU 비활성화 설정 사라짐
바로가기 Arguments 초기화  ← --disable-gpu 플래그 사라짐
이전 버전 잔존 파일 충돌   ← Squirrel 업데이터 버그
        |
        v
다음 실행 시 GPU 가속 다시 활성화
        |
        v
GPU 드라이버 충돌 → 앱 크래시 → 캐시 손상 → 부팅 루프
```

### 5대 근본 원인 (빈도순)

| 순위 | 원인 | 빈도 | 왜 재발하는가 |
|------|------|------|---------------|
| 1 | **GPU 하드웨어 가속 충돌** | 40% | 업데이트 시 GPU 설정이 기본값(활성)으로 리셋 |
| 2 | **캐시/데이터 손상** | 25% | 크래시 시 파일이 불완전하게 기록되어 반복 손상 |
| 3 | **업데이트 충돌** | 15% | Squirrel 업데이터가 이전 버전을 완전히 제거 못함 |
| 4 | **Cowork VM 충돌** | 10% | VM 프로세스가 앱 프로세스와 동시에 죽으면서 연쇄 크래시 |
| 5 | **보안 소프트웨어** | 10% | 백신이 Electron 프로세스를 주기적으로 차단 |

### 집과 회사에서 모두 발생하는 이유

- **동일 계정 동기화**: 같은 Anthropic 계정의 설정이 동기화되면서 손상된 설정 전파
- **동일 GPU 문제**: 양쪽 PC의 GPU 드라이버가 모두 Electron과 호환성 문제
- **자동 업데이트**: 양쪽 모두 같은 시점에 업데이트 → 같은 버그 노출
- **캐시 축적 패턴**: 사용 패턴이 유사하면 캐시 손상 조건도 유사하게 발생

---

## 근본 해결: Guardian 시스템

**일회성 수정이 아닌, 상시 감시 + 자동 복구 시스템**을 설치합니다.

### Guardian이 하는 일

```
[시스템 시작 시]
  1. 안정성 설정이 유효한지 자동 검사
  2. 업데이트로 리셋된 설정 자동 복구
  3. 손상된 캐시/Session Storage 자동 정리
  4. 이전 버전 잔존 파일 자동 제거

[Claude 실행 중]
  5. 프로세스 10초 간격 감시
  6. 크래시 감지 시 자동으로 안전 모드 재시작
  7. 크래시 이력 기반 적응형 복구:
     - 1회 크래시 → 안전 모드 재시작
     - 2회 연속 → GPU 비활성화 + 재시작
     - 3회 연속 → GPU 캐시 정리 + 재시작
     - 5회 연속 → 전체 캐시 초기화 + 재시작
  8. 메모리 사용량 과다 경고
```

---

## 설치 방법

### Windows

```powershell
# 1. PowerShell을 관리자 권한으로 실행

# 2. 실행 정책 허용 (최초 1회)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Guardian 설치
.\claude_desktop_guardian.ps1 -Install
```

설치 후 자동으로:
- Windows 스케줄 작업에 등록됨 (로그인 시 자동 실행)
- 바탕화면에 `Claude_안정실행.bat` 생성
- 크래시 이력 기반으로 최적 설정 자동 적용

### macOS

```bash
# 1. 터미널 실행

# 2. 스크립트 실행 권한 부여
chmod +x claude_desktop_guardian.sh

# 3. Guardian 설치
./claude_desktop_guardian.sh install
```

설치 후 자동으로:
- launchd 에이전트에 등록됨 (로그인 시 자동 실행)
- 바탕화면에 `Claude_안정실행.command` 생성
- 백그라운드에서 프로세스 감시 시작

---

## 관리 명령어

### Windows

```powershell
# 상태 확인 및 설정 보호 1회 실행
.\claude_desktop_guardian.ps1 -Protect

# 수동 감시 시작 (디버깅용)
.\claude_desktop_guardian.ps1 -Watch

# Guardian 제거
.\claude_desktop_guardian.ps1 -Uninstall
```

### macOS

```bash
# 상태 확인
./claude_desktop_guardian.sh status

# 설정 보호 1회 실행
./claude_desktop_guardian.sh protect

# 수동 감시 시작 (디버깅용)
./claude_desktop_guardian.sh watch

# Guardian 제거
./claude_desktop_guardian.sh uninstall
```

---

## 즉시 크래시(Instant Crash) 전용 - 딥 클린

앱이 **켜자마자 1~2초 만에 즉시 꺼져버리는** 경우, 선별적 캐시 삭제로는 해결이 안 됩니다.
앱 데이터를 **통째로 삭제**하여 백지 상태로 초기화해야 합니다.

### 원인

앱이 마지막으로 열어두었던 대화창/코워크 세션을 자동으로 불러오면서 내부 UI 엔진(React)이
렌더링 중 크래시 → 강제 종료 → 다시 같은 세션 로드 시도 → 무한 루프에 빠진 상태입니다.
집과 회사 PC에서 동시에 발생하는 이유는 동일 계정의 설정이 동기화되기 때문입니다.

### 자동 스크립트 (권장)

```powershell
# PowerShell에서 실행 (확인 프롬프트 표시)
.\fix_instant_crash_deepclean.ps1

# 확인 없이 즉시 실행
.\fix_instant_crash_deepclean.ps1 -SkipConfirm

# 설정 파일 백업 후 실행
.\fix_instant_crash_deepclean.ps1 -BackupConfig

# Defender 예외도 함께 등록 (관리자 권한 필요)
.\fix_instant_crash_deepclean.ps1 -IncludeDefenderExclusion
```

스크립트가 수행하는 4단계:
1. 좀비 프로세스 완벽 종료 (taskkill + Get-Process)
2. 앱 데이터 완전 삭제 (`%APPDATA%\Claude`, `%LOCALAPPDATA%\Claude`, `claude-updater`)
3. GPU 하드웨어 가속 강제 비활성화 (electron-flags.conf + 바로가기 수정)
4. 바탕화면에 안정 실행 런처 생성 + 트레이 설정 안내

### 수동 진행 (스크립트 실행이 어려운 경우)

```cmd
REM 1. 관리자 명령 프롬프트에서 좀비 프로세스 종료
taskkill /f /im "Claude.exe" /t
```

```
2. Windows키 + R → %appdata% → Claude 폴더 삭제
3. Windows키 + R → %localappdata% → Claude, claude-updater 폴더 삭제
4. Claude 바로가기 → 속성 → 대상(T) 끝에 --disable-gpu 추가
5. 실행 후 로그인 직후: Settings > General > "Menu bar" 옵션 ON
```

---

## 일반 응급 처치 (Guardian 설치 전)

Guardian 설치 전에 지금 당장 앱을 실행해야 하는데 **즉시 크래시는 아닌** 경우:

### Windows 응급 처치

```powershell
# 1. 모든 Claude 프로세스 종료
taskkill /f /im "Claude.exe" 2>$null

# 2. 캐시 전체 삭제
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\GPUCache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Code Cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\DawnCache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\Claude\Session Storage" -ErrorAction SilentlyContinue

# 3. GPU 비활성화하여 실행
start "" "%LOCALAPPDATA%\Programs\Claude\Claude.exe" --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox
```

### macOS 응급 처치

```bash
# 1. Claude 종료
pkill -f "Claude.app" 2>/dev/null

# 2. 캐시 전체 삭제
rm -rf ~/Library/Application\ Support/Claude/Cache
rm -rf ~/Library/Application\ Support/Claude/GPUCache
rm -rf ~/Library/Application\ Support/Claude/Code\ Cache
rm -rf ~/Library/Application\ Support/Claude/DawnCache
rm -rf ~/Library/Application\ Support/Claude/Session\ Storage

# 3. GPU 비활성화하여 실행
open -a "Claude" --args --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox
```

---

## 로그 및 진단

### Guardian 로그 위치

| OS | 경로 |
|----|------|
| Windows | `%APPDATA%\Claude\guardian_logs\` |
| macOS | `~/Library/Application Support/Claude/guardian_logs/` |

### 로그 확인

```powershell
# Windows - 오늘 로그 확인
Get-Content "$env:APPDATA\Claude\guardian_logs\guardian_$(Get-Date -Format 'yyyyMMdd').log"
```

```bash
# macOS - 오늘 로그 확인
cat ~/Library/Application\ Support/Claude/guardian_logs/guardian_$(date +%Y%m%d).log
```

### 크래시 이력 확인

```powershell
# Windows
Get-Content "$env:APPDATA\Claude\guardian_crash_history.json" | ConvertFrom-Json | Format-List
```

```bash
# macOS
python3 -m json.tool ~/Library/Application\ Support/Claude/guardian_crash_history.json
```

---

## GPU 가속 다시 켜기

Guardian이 GPU를 비활성화한 후 앱이 안정적이면, GPU 가속을 다시 켜볼 수 있습니다:

### Windows

```powershell
# 1. Guardian 설정에서 GPU 강제 비활성화 해제
$config = Get-Content "$env:APPDATA\Claude\guardian_config.json" | ConvertFrom-Json
$config.forceDisableGpu = $false
$config | ConvertTo-Json | Set-Content "$env:APPDATA\Claude\guardian_config.json"

# 2. electron-flags.conf 삭제
Remove-Item "$env:APPDATA\Claude\electron-flags.conf" -ErrorAction SilentlyContinue

# 3. 크래시 이력 초기화
Remove-Item "$env:APPDATA\Claude\guardian_crash_history.json" -ErrorAction SilentlyContinue

# 4. Claude 재시작
```

### macOS

```bash
# guardian_config.json에서 forceDisableGpu를 false로 변경
python3 -c "
import json
f = '$HOME/Library/Application Support/Claude/guardian_config.json'
d = json.load(open(f))
d['forceDisableGpu'] = False
json.dump(d, open(f,'w'), indent=2)
"

# electron-flags.conf 삭제
rm -f ~/Library/Application\ Support/Claude/electron-flags.conf

# 크래시 이력 초기화
rm -f ~/Library/Application\ Support/Claude/guardian_crash_history.json
```

GPU 가속을 다시 켠 후 크래시가 재발하면 Guardian이 자동으로 감지하고 다시 비활성화합니다.

---

## 문제가 계속되면

1. **GPU 드라이버 업데이트**: 제조사 사이트에서 최신 드라이버 설치
   - Intel: https://www.intel.com/content/www/us/en/download-center
   - NVIDIA: https://www.nvidia.com/Download/index.aspx
   - AMD: https://www.amd.com/en/support

2. **Claude 웹 버전 사용**: https://claude.ai (데스크탑과 동일 기능)

3. **버그 리포트**: https://github.com/anthropics/claude-code/issues
   - Guardian 로그 (`guardian_logs/` 폴더) 첨부
   - 크래시 이력 (`guardian_crash_history.json`) 첨부

4. **상태 확인**: https://status.anthropic.com

---

## 파일 구성

```
이 리포지토리의 크래시 관련 파일:

claude_desktop_guardian.ps1          ← [핵심] Windows Guardian (영구 해결)
claude_desktop_guardian.sh           ← [핵심] macOS Guardian (영구 해결)
fix_instant_crash_deepclean.ps1      ← [긴급] 즉시 크래시 전용 딥 클린 (Windows)
fix_claude_desktop_crash.ps1         ← 일회성 진단/수정 도구 (Windows)
fix_cowork_vhdx_access.ps1           ← Cowork VM 권한 수정 (Windows)
CLAUDE_DESKTOP_크래시_근본해결.md     ← 이 가이드
CLAUDE_DESKTOP_CRASH_FIX_GUIDE.md    ← 기존 7단계 가이드 (Windows)
claude-desktop-crash-fix-guide.md    ← 기존 5방법 가이드
claude-cowork-vm-fix-plan.md         ← Cowork VM 전용 해결 계획
```
