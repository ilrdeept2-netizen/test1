---
title: "Claude Desktop 실행 즉시 종료 문제 해결 (Windows)"
date: 2026-02-10
updated: 2026-04-09
category: troubleshoot
tags: [claude-desktop, windows, troubleshoot, fix, crash]
status: active
summary: "Windows에서 Claude Desktop 실행 직후 종료되는 문제의 원인별 해결 방법"
related:
  - docs/claude-desktop/claude-desktop-outage-report-2026-02-10.md
  - docs/claude-desktop/CLAUDE_DESKTOP_크래시_근본해결.md
---

# Claude Desktop 실행 즉시 종료 문제 해결 가이드 (Windows)

## 문제 현상

Claude Desktop 앱을 설치 후 실행하면 바로 꺼지거나, "Claude Desktop failed to Launch" 오류 메시지가 표시되는 현상.
특히 Claude Cowork 기능 사용을 위해 설치한 경우 CoworkVMService 관련 충돌이 원인일 수 있음.

---

## 해결 방법 (순서대로 시도)

### 1단계: 기존 Claude 프로세스 완전 종료

백그라운드에 남아있는 Claude 프로세스가 충돌을 일으킬 수 있습니다.

1. `Ctrl + Shift + Esc`로 **작업 관리자** 열기
2. "Claude" 관련 프로세스 **모두** 종료 (보통 6~7개)
3. "CoworkVMService" 프로세스도 있으면 종료
4. Claude Desktop 재실행

---

### 2단계: 앱 캐시 및 데이터 초기화

PowerShell을 **관리자 권한**으로 실행한 후 다음 명령어 실행:

```powershell
# Claude 앱 데이터 삭제
Remove-Item -Recurse -Force "$env:APPDATA\Claude\*" -ErrorAction SilentlyContinue

# MSIX 패키지 캐시 삭제 (Cowork VM 번들 포함)
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Packages\Claude_pzs8sxjxfjjc\LocalCache\*" -ErrorAction SilentlyContinue
```

삭제 후 Claude Desktop 재실행.

---

### 3단계: CoworkVMService 충돌 해결

Claude Cowork 설치 시 등록되는 CoworkVMService가 충돌의 주요 원인입니다.

**관리자 권한 PowerShell**에서 실행:

```powershell
# 서비스 상태 확인
Get-Service -Name "CoworkVMService" -ErrorAction SilentlyContinue

# 서비스 중지
Stop-Service -Name "CoworkVMService" -Force -ErrorAction SilentlyContinue

# 서비스 삭제 시도
sc.exe delete CoworkVMService
```

만약 "Access is denied" 오류가 나오면 레지스트리에서 직접 삭제:

```powershell
# 레지스트리에서 서비스 직접 제거
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\CoworkVMService" /f
```

**PC 재부팅** 후 Claude Desktop 재실행.

---

### 4단계: 개발자 모드 및 사이드로딩 활성화

Windows 보안 정책이 앱 실행을 차단할 수 있습니다.

1. **설정** > **개인 정보 및 보안** > **개발자용** 으로 이동
2. **개발자 모드** 활성화
3. **설정** > **앱** > **고급 앱 설정** 으로 이동
4. **앱 사이드로딩** 허용

---

### 5단계: Hyper-V 및 가상화 확인 (Cowork 사용 시)

Claude Cowork는 가상 머신(VM)을 사용하므로 Hyper-V가 필요합니다.

> **참고**: Windows 11 Home에는 Hyper-V가 없습니다. 이 경우 Cowork 기능은 사용할 수 없지만, 기본 채팅 기능은 동작해야 합니다.

Windows 11 Pro/Enterprise 사용자:

1. **설정** > **앱** > **선택적 기능** > **Windows 기능 켜기/끄기**
2. 다음 항목 활성화:
   - Hyper-V
   - Virtual Machine Platform
   - Windows Hypervisor Platform
3. PC 재부팅

BIOS에서 Intel VT-x 또는 AMD-V 가상화가 활성화되어 있는지도 확인하세요.

---

### 6단계: PowerShell PATH 확인

설치 시 서명 검증 실패가 발생할 수 있습니다.

```powershell
# PowerShell 경로 확인
where.exe powershell.exe
```

결과가 없으면 시스템 PATH에 `C:\Windows\System32\WindowsPowerShell\v1.0\`을 추가하세요.

---

### 7단계: 완전 재설치

위 방법이 모두 안 되면 완전 재설치를 진행합니다.

1. **설정** > **앱** > **설치된 앱**에서 Claude Desktop 제거
2. 관리자 권한 PowerShell에서 잔여 데이터 삭제:

```powershell
# 앱 데이터 완전 삭제
Remove-Item -Recurse -Force "$env:APPDATA\Claude" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Packages\Claude_*" -ErrorAction SilentlyContinue

# CoworkVMService 제거
sc.exe delete CoworkVMService 2>$null
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\CoworkVMService" /f 2>$null

# VM 관련 파일 삭제
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\claude-code-vm" -ErrorAction SilentlyContinue
```

3. PC 재부팅
4. https://claude.com/download 에서 최신 버전 다운로드 후 재설치

---

## Windows 11 Home 사용자 참고사항

- Windows 11 Home에는 Hyper-V가 포함되어 있지 않아 **Cowork 기능을 사용할 수 없습니다**
- Claude Desktop의 기본 채팅 기능은 정상 작동해야 합니다
- Cowork가 필요하면 Windows 11 Pro 이상으로 업그레이드가 필요합니다
- 현재 Windows Cowork는 2026년 2월 10일에 출시된 초기 버전으로, 알려진 버그가 다수 존재합니다

---

## 여전히 해결되지 않는 경우

1. **Claude 상태 페이지** 확인: https://status.anthropic.com
2. **디버그 로그 수집**: Claude Desktop 메뉴 > Help > Troubleshooting > Show logs
3. **GitHub 이슈 등록**: https://github.com/anthropics/claude-code/issues
4. **Anthropic 지원팀 문의**: https://support.claude.com

---

## 참고 자료

- [Claude Desktop 설치 가이드](https://support.claude.com/en/articles/10065433-installing-claude-desktop)
- [Claude Code 문제 해결 문서](https://code.claude.com/docs/ko/troubleshooting)
- [GitHub Issue #25194 - Desktop fails to launch on Windows 11 Home](https://github.com/anthropics/claude-code/issues/25194)
- [GitHub Issue #25906 - Crash-loop on relaunch](https://github.com/anthropics/claude-code/issues/25906)
- [GitHub Issue #25136 - Cowork tab not showing on Windows](https://github.com/anthropics/claude-code/issues/25136)
