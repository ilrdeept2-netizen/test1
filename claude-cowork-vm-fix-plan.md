# Claude Cowork "VM service not running" 해결 계획

**오류 메시지**: "Claude 작업 공간을 시작하지 못했습니다 — VM service not running. The service failed to start."
**환경**: Windows PC, Claude Desktop App, Cowork 탭
**날짜**: 2026-02-11

---

## 배경 분석

### Cowork Windows 버전 현황
- Cowork는 원래 **macOS 전용** 리서치 프리뷰 (2026년 1월 12일 출시)
- **Windows 지원은 2026년 2월 10일에 정식 출시** (바로 어제)
- Windows에서는 **WSL2 (Hyper-V 기반 가상화)**를 사용하여 VM 격리 환경 구성
- 출시 직후이므로 안정성 문제가 발생할 가능성이 높음

### "VM service not running" 오류 원인 분류

| 원인 | 가능성 | 설명 |
|---|---|---|
| WSL2/Hyper-V 미설치 또는 비활성 | **높음** | Windows에서 VM을 돌리려면 가상화 기능 필수 |
| BIOS에서 가상화 비활성 | **높음** | CPU 가상화(VT-x/AMD-V)가 꺼져있으면 VM 시작 불가 |
| VM 번들 파일 손상 | 중간 | 다운로드 중 손상되거나 이전 버전과 충돌 |
| 서버 측 배포 미완료 | 중간 | 어제 Windows 출시 직후라 VM 이미지 배포 중일 수 있음 |
| VPN/방화벽 간섭 | 낮음 | VM 네트워킹을 방해할 수 있음 |
| 메모리/디스크 부족 | 낮음 | VM 번들이 10GB+ 차지, RAM 8GB 이상 권장 |

---

## 해결 계획 (순서대로 진행)

### Phase 1: 가상화 환경 점검 (가장 중요)

#### 1-1. CPU 가상화 활성화 확인
```
작업 관리자(Ctrl+Shift+Esc) → 성능 탭 → CPU 선택
→ "가상화: 사용" 확인
```
- **"사용 안 함"으로 표시되는 경우**:
  1. PC 재부팅 → BIOS 진입 (보통 F2, Del, F10)
  2. Advanced → CPU Configuration (또는 Virtualization Technology)
  3. Intel VT-x 또는 AMD-V를 **Enabled**로 변경
  4. 저장 후 재부팅

#### 1-2. WSL2 설치 확인 및 설정
```powershell
# PowerShell을 관리자 권한으로 실행 후:

# WSL 설치 여부 확인
wsl --status

# 설치되어 있지 않으면 설치
wsl --install --no-distribution

# 이미 설치되어 있으면 최신 버전으로 업데이트
wsl --update
```

#### 1-3. Windows 기능 활성화 확인
```powershell
# PowerShell 관리자 권한으로 실행

# Hyper-V 활성화
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart

# Virtual Machine Platform 활성화
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Windows Subsystem for Linux 활성화
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```
- **반드시 재부팅 필요** (위 명령 실행 후)

#### 1-4. 재부팅 후 확인
```powershell
# WSL2가 기본 버전인지 확인
wsl --set-default-version 2

# 정상 동작 확인
wsl --status
```

---

### Phase 2: Claude Cowork VM 번들 초기화

#### 2-1. Claude Desktop 완전 종료
```
작업 관리자(Ctrl+Shift+Esc) → "Claude" 프로세스 모두 → 작업 끝내기
```
(백그라운드에 남아있는 프로세스 주의 — 알려진 버그 Issue #15368)

#### 2-2. VM 번들 및 캐시 삭제
```powershell
# 탐색기 주소창에 아래를 하나씩 붙여넣고 해당 폴더 삭제

# VM 번들 (10GB+ 용량 차지)
%APPDATA%\Claude\vm_bundles

# 앱 캐시
%APPDATA%\Claude\Cache
%APPDATA%\Claude\GPUCache
%APPDATA%\Claude\Session Storage

# Local 데이터
%LOCALAPPDATA%\Claude\vm_bundles
%LOCALAPPDATA%\Claude\Cache
```

#### 2-3. Claude Desktop 재실행
- 앱을 다시 실행하면 VM 번들을 새로 다운로드
- 인터넷 속도에 따라 10~30분 소요 가능 (VM 이미지 10GB+)
- 다운로드 완료 후 Cowork 탭에서 재시도

---

### Phase 3: 앱 완전 재설치 (Phase 2로 해결 안 될 경우)

#### 3-1. Claude Desktop 완전 제거
```
설정 → 앱 → Claude → 제거
```

#### 3-2. 잔여 데이터 완전 삭제
```powershell
# 다음 폴더를 모두 삭제
rmdir /s /q "%APPDATA%\Claude"
rmdir /s /q "%LOCALAPPDATA%\Claude"
rmdir /s /q "%LOCALAPPDATA%\Programs\Claude"
```

#### 3-3. PC 재부팅

#### 3-4. 최신 버전 설치
- https://claude.com/download 에서 최신 Windows 버전 다운로드
- 설치 후 로그인 → Cowork 탭 진입

---

### Phase 4: 네트워크/보안 소프트웨어 점검

#### 4-1. VPN 비활성화
- VPN 사용 중이면 완전 종료 (트레이에서 나가기)
- VPN이 WSL2 네트워킹을 방해하는 것이 알려진 문제 (Issue #18854)

#### 4-2. 방화벽 규칙 확인
```powershell
# Windows 방화벽에서 Claude 허용 확인
# 설정 → Windows 보안 → 방화벽 및 네트워크 보호 → 앱 방화벽 통과 허용
# → Claude Desktop이 "개인" 및 "공용" 모두 체크되어 있는지 확인
```

#### 4-3. 백신/보안 소프트웨어 일시 중지
- 일부 백신(V3, 알약 등)이 VM 프로세스를 차단할 수 있음
- 일시적으로 실시간 보호를 끄고 테스트

#### 4-4. DNS 변경
```
설정 → 네트워크 → 이더넷/Wi-Fi → DNS 서버 할당 → 수동
기본 DNS: 8.8.8.8
보조 DNS: 8.8.4.4
```

---

### Phase 5: 시스템 요구사항 재확인

#### 5-1. 최소 사양 충족 여부
| 항목 | 최소 요구 | 권장 |
|---|---|---|
| OS | Windows 11 21H2+ | Windows 11 최신 |
| RAM | 8GB | 16GB+ |
| 디스크 여유 | 15GB+ | 30GB+ |
| CPU | 가상화 지원 (VT-x/AMD-V) | - |

#### 5-2. Windows 버전 확인
```powershell
winver
# Windows 11 버전 21H2 이상이어야 함
# Windows 10은 지원되지 않을 수 있음
```

#### 5-3. 디스크 공간 확인
- VM 번들이 10GB 이상 차지
- C: 드라이브에 최소 15GB 여유 공간 필요

---

### Phase 6: 디버그 로그 수집 (위 모든 방법 실패 시)

#### 6-1. 로그 위치
```
%APPDATA%\Claude\logs\
```

#### 6-2. 로그 수집 후 버그 리포트
- https://github.com/anthropics/claude-code/issues 에서 새 이슈 생성
- 제목: "[BUG] Cowork VM service not running on Windows — service failed to start"
- 포함할 정보:
  - Claude Desktop 버전
  - Windows 버전 (winver 결과)
  - WSL2 상태 (wsl --status 결과)
  - 가상화 활성화 여부
  - 전체 로그 파일

---

### Phase 7: 대안 경로

VM 문제가 근본적으로 해결되지 않는 경우:

#### 7-1. 웹 버전으로 우회
- https://claude.ai 에서 대부분의 기능 사용 가능

#### 7-2. Open Cowork (오픈소스 대안)
- https://github.com/OpenCoworkAI/open-cowork
- WSL2 자동 감지, VM 격리 지원
- 공식 Cowork와 유사한 기능 제공

#### 7-3. Claude Code CLI 직접 사용
```powershell
# Claude Code는 터미널에서 직접 실행 가능
npm install -g @anthropic-ai/claude-code
claude
```

---

## 진행 우선순위 요약

```
[1순위] Phase 1 → 가상화/WSL2 확인 (대부분의 경우 여기서 해결)
   ↓ 안 되면
[2순위] Phase 2 → VM 번들 삭제 후 재다운로드
   ↓ 안 되면
[3순위] Phase 3 → 앱 완전 재설치
   ↓ 안 되면
[4순위] Phase 4 → 네트워크/보안 점검
   ↓ 안 되면
[5순위] Phase 5 → 시스템 사양 확인
   ↓ 안 되면
[6순위] Phase 6 → 로그 수집 후 Anthropic에 버그 리포트
   ↓ 급하면
[대안]  Phase 7 → 웹 버전 또는 대안 도구 사용
```

---

## Sources
- [Claude Help Center - Getting started with Cowork](https://support.claude.com/en/articles/13345190-getting-started-with-cowork)
- [GitHub Issue #24070 - VM fails to boot after auto-update](https://github.com/anthropics/claude-code/issues/24070)
- [GitHub Issue #22330 - VM fails to start missing libmnl](https://github.com/anthropics/claude-code/issues/22330)
- [GitHub Issue #23991 - Workspace setup RPC error](https://github.com/anthropics/claude-code/issues/23991)
- [GitHub Issue #15368 - Desktop app not exiting](https://github.com/anthropics/claude-code/issues/15368)
- [GitHub Issue #18854 - MITM proxy blocking API](https://github.com/anthropics/claude-code/issues/18854)
- [EONMSK - Cowork launches for Windows](https://www.eonmsk.com/2026/02/10/claude-cowork-launches-for-windows-users/)
- [Claude Code Troubleshooting Docs](https://code.claude.com/docs/en/troubleshooting)
- [Open Cowork - Open Source Alternative](https://github.com/OpenCoworkAI/open-cowork)
