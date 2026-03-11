# Claude Desktop App Outage Report - 2026년 2월 10일

## 현재 상황 (한국 사용자 기준)

**증상**: Claude 데스크탑 앱에서 "작업 중(maintenance)" 공지만 표시되며, 아침부터 8시간 이상 정상 동작하지 않는 상태

### 공식 상태 vs 실제 사용자 체감

| 구분 | 내용 |
|---|---|
| **공식 상태** | status.claude.com 기준 "Operational" (정상) |
| **사용자 보고** | 지난 24시간 내 13~16건의 장애 보고 (StatusGator/IsDown) |
| **Down Detector** | 미국(14건), 스웨덴(10), 네덜란드(5), 프랑스(5), 영국(5), 독일(4), 브라질(3), 캐나다(2) 보고 |

**핵심 문제**: 공식 상태 페이지는 "정상"이라고 표시하지만, 실제로 다수의 사용자가 장애를 경험하고 있는 **"유령 장애(Silent Outage)"** 상태로 추정됩니다.

---

## 왜 한국 사용자가 특히 영향을 받는가?

### 1. 시간대 문제 (Time Zone Factor)
- Anthropic 본사는 미국 태평양 시간대(PT) 기준으로 운영
- 한국(KST)은 PT보다 **17시간 앞서** 있음
- 한국 오전 = 미국 전날 오후~저녁 → 미국 팀의 업무 외 시간에 장애 발생 시 대응 지연
- 한국 사용자의 아침(KST 09:00) = 미국 태평양 시간 오후 4시(전날) → 이전 인시던트(2/7 15:15 UTC)와 유사한 패턴

### 2. 리전별 인프라 차이
- 2026년 2월 1일부터 Anthropic은 `inference_geo` 파라미터로 데이터 레지던시 제어 도입
- 아시아 리전 사용자는 미국 리전 대비 라우팅 경로가 길어 장애 감지 및 복구 우선순위에서 밀릴 가능성
- 한국에 서울 사무소가 2026년 초 개설 예정이나, 인프라(추론 서버)가 아직 미국 중심

### 3. 최근 대규모 업데이트의 후폭풍
- **Opus 4.6 출시 (2/5~6)**: 신규 모델 배포 직후 안정화 기간
- **데스크탑 앱 업데이트 (2/6)**: Claude Code 통합, Infinite Chats, 메모리 기능 등 대규모 기능 추가
- **DXT 보안 취약점 발견 (2/9)**: CVSS 10.0 등급 제로클릭 취약점 → 긴급 패치 가능성

---

## 2월 장애 타임라인 (누적 패턴 분석)

```
2/1  ████░░░░░░░░ Opus 4.5 에러 (~20분)
2/3  ████████░░░░ API 500 에러 + SSO 장애 (내부 설정 변경 원인)
2/4  ██████████░░ Claude 모델 전반 장애 (2건, ~35분+55분)
2/5  ████████████████████ 대화 압축 기능 장애 (4시간 35분)
2/6  ████████░░░░ claude.ai/API/Claude Code 에러율 상승
2/7  ██████░░░░░░ Claude 모델 에러 상승 (30분)
2/8  ░░░░░░░░░░░░ (공식 보고 없음)
2/9  ░░░░░░░░░░░░ DXT 보안 취약점 보고 (CVSS 10.0)
2/10 ???????????????? ← 현재: 공식 "정상", 사용자 다수 장애 보고
```

**패턴**: 2/1부터 거의 매일 인시던트 발생 → 2/5 Opus 4.6 출시 전후로 장애 빈도/심각도 증가 → 2/8 이후 공식 보고는 줄었으나 사용자 체감 장애 지속

---

## "작업 중" 공지의 가능한 원인 분석

### 가설 1: 데스크탑 앱 강제 업데이트 배포 중
- 2/6에 대규모 데스크탑 앱 업데이트 배포
- 2/9 DXT 제로클릭 취약점(CVSS 10.0) 발견 → 긴급 보안 패치 배포 가능성 높음
- 앱이 업데이트를 다운로드/적용하는 동안 "작업 중" 표시될 수 있음
- **알려진 버그**: `claude update` 명령이 새 버전을 다운로드하지만 symlink를 업데이트하지 않아 구 버전에 고착되는 문제 (GitHub Issue #24117)

### 가설 2: 인증/세션 관련 장애
- 2/3에 SSO/매직 링크 로그인 장애 이력
- 데스크탑 앱 v1.1.1520에서 "Invalid authorization" 무한 루프 버그 보고 (GitHub Issue #22685, 2/2)
- 인증 토큰이 만료되었으나 갱신에 실패하여 앱이 "작업 중" 상태로 멈출 가능성

### 가설 3: 대화 압축(Compaction) 기능 후유증
- 2/5에 대화 압축 기능이 4시간 35분간 장애
- "Infinite Chats" 기능 도입으로 대화 압축 로직 변경
- 이전 대화 데이터가 새 압축 로직과 충돌하여 앱 로딩이 멈출 가능성
- 사용자 보고: "orange splat blinks forever", "no response, just spinning logo"

### 가설 4: 아시아 리전 특정 라우팅/CDN 문제
- 공식 상태 페이지에서 감지되지 않는 지역별 장애
- 한국발 트래픽 라우팅 경로의 특정 노드 문제
- 미국 중심 모니터링으로 아시아 리전 장애 미감지

---

## 즉시 시도할 수 있는 해결 방법

### 단계 1: 앱 강제 종료 및 캐시 삭제
```
# macOS
rm -rf ~/Library/Application\ Support/Claude/Cache
rm -rf ~/Library/Application\ Support/Claude/GPUCache

# Windows
rmdir /s /q %APPDATA%\Claude\Cache
rmdir /s /q %APPDATA%\Claude\GPUCache
```

### 단계 2: 앱 완전 삭제 후 재설치
- https://claude.com/download 에서 최신 버전 다운로드
- 기존 앱 데이터를 완전히 삭제한 후 재설치

### 단계 3: 네트워크 확인
- DNS를 Google DNS(8.8.8.8, 8.8.4.4) 또는 Cloudflare DNS(1.1.1.1)로 변경
- VPN 사용 시 미국 서버로 변경해서 테스트
- 라우터 재부팅

### 단계 4: 웹 버전으로 우회
- https://claude.ai 에서 동일 계정으로 접속 가능한지 확인
- 웹에서 작동한다면 데스크탑 앱 자체의 문제

### 단계 5: 로그 확인
```
# macOS 로그 위치
~/Library/Logs/Claude/

# Windows 로그 위치
%APPDATA%\Claude\logs\
```

---

## 90일간 장애 통계 요약

| 항목 | 수치 |
|---|---|
| 총 인시던트 | 66건 |
| 주요 장애 (Major) | 21건 |
| 소규모 장애 (Minor) | 45건 |
| 중간값 지속 시간 | 56분 |
| 평균 해결 시간 | 236분 (IsDown 기준) |

---

## 결론

2월 10일 현재 한국 사용자가 겪고 있는 8시간 이상의 데스크탑 앱 장애는 **공식 상태 페이지에 반영되지 않는 "유령 장애"**로 보입니다.

가장 유력한 원인은:
1. **2/9 DXT 보안 취약점(CVSS 10.0) 대응 긴급 패치** 배포 과정에서의 앱 업데이트 문제
2. **2/6 대규모 기능 업데이트** 이후 아시아 리전에서의 안정화 미완료
3. **인증 토큰 갱신 실패**로 인한 앱 무한 로딩 상태

Anthropic의 모니터링이 미국 중심으로 운영되고 있어, 한국 등 아시아 사용자의 장애가 공식 감지되지 않을 가능성이 높습니다. 서울 사무소 본격 가동과 아시아 리전 인프라 확충이 이루어지기 전까지 이런 패턴은 반복될 수 있습니다.

---

## Sources
- [Claude Status Page](https://status.claude.com/)
- [Claude Status - Incident History](https://status.claude.com/history)
- [StatusGator - Claude Status](https://statusgator.com/services/claude)
- [IsDown - Claude Status](https://isdown.app/status/claude-ai)
- [Entireweb - Claude Status](https://www.entireweb.com/status/claude)
- [GitHub Issue #20136 - Desktop app infinite loading](https://github.com/anthropics/claude-code/issues/20136)
- [GitHub Issue #22685 - Invalid authorization loop](https://github.com/anthropics/claude-code/issues/22685)
- [GitHub Issue #24117 - Update symlink bug](https://github.com/anthropics/claude-code/issues/24117)
- [Infosecurity - DXT Zero-Click Flaw](https://www.infosecurity-magazine.com/news/zeroclick-flaw-claude-dxt/)
- [AI Digester - Claude Code Outage](https://aidigester.org/en/major-claude-code-outage-developers-forced-to-take-a-coffee-break/)
- [Threads @hon_coding - Claude 불안정 보고](https://www.threads.com/@hon_coding/post/DL4Nyyeylt8/)
