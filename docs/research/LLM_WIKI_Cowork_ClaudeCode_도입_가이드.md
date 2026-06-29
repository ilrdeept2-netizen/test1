# LLM WIKI — Claude Cowork / Claude Code(Web) 도입 가이드

> Karpathy의 LLM WIKI 개념을 Claude Cowork 및 Claude Code 웹 환경에 적용하는 단계별 가이드

---

## 개념 이해

### Claude Code가 컨텍스트를 잃는 방식

Claude Code는 대화가 길어지면 **자동 압축(auto-summarization)** 을 수행한다.  
이 과정에서:
- 초기 결정 사항이 증발
- 이전 오류 해결 맥락이 포맷
- 도메인 지식이 뭉뚱그려짐
- 세션 재시작 시 완전 초기화

**LLM WIKI = Claude Code가 매 세션/압축 이후에도 잃으면 안 되는 것들을 보존하는 구조**

### Cohere Reranking처럼 동작하게

모든 내용을 CLAUDE.md에 다 넣으면 오히려 토큰 낭비 + 노이즈.  
Cohere의 선택적 재랭킹처럼:
- 현재 태스크와 관련된 wiki 섹션만 로드
- 나머지는 파일로 존재하지만 컨텍스트에는 없음
- 필요 시 "wiki/errors.md 읽어봐" 로 호출

---

## 시스템 구조 (Claude Code 환경)

```
프로젝트_루트/
├── CLAUDE.md               ← 핵심 진입점 (짧게 유지, wiki 참조)
├── wiki/
│   ├── INDEX.md            ← WIKI 전체 맵
│   ├── decisions.md        ← 확정된 설계/업무 결정
│   ├── errors.md           ← 해결된 오류 DB
│   ├── patterns.md         ← 반복 패턴 / 규칙
│   ├── domain.md           ← 도메인 지식 (특허, 법률 등)
│   └── snapshots/
│       └── YYYYMMDD.md     ← 날짜별 작업 스냅샷
└── .claude/
    ├── settings.json       ← 훅 설정
    └── hooks/
        ├── session-start.sh    ← 세션 시작 시 WIKI 로드
        └── pre-compact.sh      ← 압축 전 스냅샷 저장
```

---

## 1단계: CLAUDE.md를 WIKI 게이트웨이로 재설계

### 기존 CLAUDE.md (잘못된 방식)
```markdown
# 프로젝트 정보
이 프로젝트는 특허 명세서를 자동으로 변환합니다.
Python 3.11을 사용합니다.
HWP 파일은 olefile로 처리합니다.
오류 1: sgmllib3k 설치 실패 → ...
오류 2: HWP 파싱 시...
(이하 500줄...)
```

### WIKI 방식 CLAUDE.md (올바른 방식)
```markdown
# 프로젝트: 특허 업무 자동화 도구

## 즉시 읽을 것 (이 세션에서 반드시)
- wiki/INDEX.md — 현재 프로젝트 상태 파악
- wiki/snapshots/최신날짜.md — 이전 작업 이어받기

## 필요 시 읽을 것 (태스크별)
- 오류 발생 시: wiki/errors.md
- 구조 논의 시: wiki/decisions.md + wiki/domain.md
- 패턴 적용 시: wiki/patterns.md

## WIKI 업데이트 기준 (선별 원칙)
넣는 것: 설계결정, 오류해결, 반복패턴, 도메인지식, 사람 승인 사항
넣지 않는 것: 단순 코드 생성, 임시 디버깅, 이미 코드에 반영된 것
```

---

## 2단계: wiki/ 파일 초기 구성

### wiki/INDEX.md
```markdown
# WIKI 인덱스

## 현재 상태 (2026-04-06 기준)
- 진행 중: patent_format_converter.py 리팩토링
- 완료: OA 의견서 자동화 v1
- 대기: 도면 생성 모듈

## 파일 구성
| 파일 | 내용 | 마지막 업데이트 |
|------|------|----------------|
| decisions.md | 설계 결정 7건 | 2026-04-05 |
| errors.md | 해결 오류 12건 | 2026-04-04 |
| patterns.md | 반복 패턴 8건 | 2026-04-03 |
| domain.md | 특허/법률 지식 | 2026-03-20 |
| snapshots/20260406.md | 오늘 작업 상태 | 오늘 업데이트 예정 |

## 미결 사항
- [ ] HWP 파서 메모리 누수 원인 미확인
- [ ] API fallback 모델 결정 필요 (Gemini Flash vs Sonnet)
```

### wiki/errors.md (형식 예시)
```markdown
# 해결된 오류 DB

## E-001: sgmllib3k 설치 실패
- **발생 환경:** Python 3.11, pip 24.x
- **오류 메시지:** `Failed building wheel for sgmllib3k`
- **원인:** Python 3.11에서 sgmllib 제거됨
- **해결:** `pip install sgmllib3k --no-build-isolation` 또는 requirements.txt에서 제거
- **재발방지:** session-start.sh에서 sgmllib3k 대신 html.parser 사용 확인

## E-002: HWP 파일 파싱 시 인코딩 오류
- **발생:** olefile로 HWP 읽을 때 CP949 디코딩 실패
- **해결:** `errors='ignore'` 옵션 추가
- **코드:** `content.decode('cp949', errors='ignore')`
```

### wiki/decisions.md (형식 예시)
```markdown
# 설계 결정 사항

## D-001: 청구항 파서 구현 방식
- **결정일:** 2026-03-15
- **결정:** regex 대신 LLM(Claude Haiku) 사용
- **이유:** 비정형 청구항 구조 처리 불가 (regex 한계 확인)
- **검토자:** 사용자 직접 승인
- **영향 파일:** patent_format_converter.py:claim_parser()

## D-002: HWP 처리 라이브러리
- **결정:** python-hwp 사용 금지, olefile 전용
- **이유:** python-hwp가 한글 2022 파일 포맷 미지원
- **날짜:** 2026-03-20
```

---

## 3단계: 훅 설정 (자동화)

### .claude/hooks/session-start.sh

```bash
#!/bin/bash
# 세션 시작 시 WIKI 상태 확인

WIKI_DIR="$CLAUDE_PROJECT_DIR/wiki"

if [ -d "$WIKI_DIR" ]; then
    echo "=== WIKI 로드 ==="
    echo "wiki/INDEX.md를 읽어 현재 프로젝트 상태를 파악하세요."
    
    # 오늘 스냅샷 없으면 알림
    TODAY=$(date +%Y%m%d)
    if [ ! -f "$WIKI_DIR/snapshots/$TODAY.md" ]; then
        echo "⚠ 오늘 스냅샷 없음. 세션 종료 전 wiki/snapshots/$TODAY.md 생성 필요."
    fi
fi
```

### .claude/settings.json (훅 등록)
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"
          }
        ]
      }
    ]
  }
}
```

---

## 4단계: 압축(Compact) 이벤트 대응

Claude Code가 자동 압축을 수행하기 전 컨텍스트 보존 방법.

### 방법 A: 수동 스냅샷 (권장)
긴 작업 전에 직접 요청:

```
지금까지 결정한 것과 현재 상태를 wiki/snapshots/오늘날짜.md에 저장해줘.
형식: 현재 작업, 결정사항, 미결 질문, 다음 세션 시작점
```

### 방법 B: 압축 감지 후 복구
압축 이후 대화가 단절됐다고 느껴지면:

```
wiki/INDEX.md와 wiki/snapshots/최신날짜.md를 읽고
현재 작업 맥락을 복원해줘.
```

### 방법 C: 정기 체크포인트
매 30분 또는 큰 작업 단위 완료 시:

```
방금 결정한 것 / 해결한 것이 WIKI 업데이트 기준에 해당하는지 확인하고
해당되면 wiki/에 기록해줘.
```

---

## 5단계: Cowork 환경 특화 설정

### Claude Cowork Skills로 WIKI 명령 등록

`.claude/skills/wiki-update.md` 생성:

```markdown
---
name: wiki-update
description: 현재 세션에서 WIKI에 기록할 내용을 정리하고 저장
---

## 실행 내용
1. 이 세션에서 발생한 설계 결정, 오류 해결, 패턴을 정리
2. WIKI 업데이트 기준에 해당하는 것만 선별
3. 해당 wiki/ 파일에 추가
4. wiki/INDEX.md의 마지막 업데이트 날짜 갱신
5. 오늘 스냅샷 업데이트
```

이후 사용법:
```
/wiki-update
```

### Claude Cowork Multi-Agent 시나리오

팀 환경에서 WIKI를 공유 지식 베이스로 활용:

```
[에이전트 1: 특허 작성]    [에이전트 2: 선행기술 조사]
        │                           │
        └─── wiki/domain.md ────────┘  ← 공유 도메인 지식
        └─── wiki/decisions.md ─────┘  ← 확정된 결정 공유
```

---

## 6단계: 태스크 앱 연동 시나리오

Claude Code를 태스크 관리와 연동하는 경우.

### GitHub Issues + WIKI 연동

```
[GitHub Issue #42: HWP 파서 개선]
        ↓
[Claude Code 세션]
  - wiki/errors.md의 E-002 참조
  - 해결 후 wiki/errors.md 업데이트
  - wiki/decisions.md에 D-010 추가
        ↓
[Issue 닫기 + wiki 업데이트 완료]
```

### 작업 상태를 WIKI와 동기화

세션 종료 전 루틴 프롬프트:

```
작업 완료 체크리스트:
1. 오늘 해결한 오류가 있으면 wiki/errors.md에 추가
2. 설계 결정이 있으면 wiki/decisions.md에 추가
3. wiki/snapshots/오늘날짜.md 생성:
   - 완료한 것
   - 다음에 할 것
   - 미결 질문
4. wiki/INDEX.md 현황 업데이트
```

---

## 운영 원칙 요약

### 토큰 절약 공식

```
CLAUDE.md 크기 목표: 100줄 이하 (게이트웨이 역할만)
wiki/ 총 크기: 제한 없음 (필요할 때만 로드)
세션당 로드: INDEX.md + 오늘 snapshot + 필요한 1-2개 파일
```

### WIKI 업데이트 5원칙 (Cohere 선택 원칙)

1. **관련성**: 현재 및 미래 세션에 실제로 필요한가?
2. **재사용성**: 이 패턴/해결책이 다시 쓰일 가능성이 있는가?
3. **비가역성**: 코드에서 찾기 어려운 맥락인가?
4. **결정성**: 사람이 승인한 판단인가?
5. **희소성**: 이미 코드/문서에 없는 정보인가?

5개 중 2개 이상 → WIKI에 기록  
1개 이하 → 기록하지 않음

---

## 자주 묻는 질문

**Q: CLAUDE.md와 wiki/의 차이?**  
CLAUDE.md = 항상 로드되는 최소 컨텍스트 (100줄 이하)  
wiki/ = 필요 시 호출하는 상세 지식 베이스 (크기 제한 없음)

**Q: 압축이 발생했는지 어떻게 알아?**  
대화 흐름이 끊기거나, 이전에 결정한 것을 Claude가 모를 때 발생.  
감지되면 즉시: `wiki/snapshots/최신날짜.md 읽어줘`

**Q: 팀원과 WIKI를 공유할 때 충돌은?**  
wiki/ 디렉토리를 git으로 관리. 각 파일을 섹션 단위로 분리하면 충돌 최소화.

**Q: 얼마나 자주 정리해야 하나?**  
주 1회 10분. decisions/errors/patterns에서 오래된 것, 중복된 것 제거.

---

## 도입 체크리스트

```
□ CLAUDE.md를 100줄 이하 게이트웨이로 리라이트
□ wiki/ 디렉토리 생성 (INDEX, decisions, errors, patterns, domain)
□ .claude/hooks/session-start.sh 설정
□ .claude/settings.json에 SessionStart 훅 등록
□ 첫 번째 스냅샷 wiki/snapshots/오늘날짜.md 생성
□ /wiki-update 스킬 등록 (선택)
□ 팀 환경이면 wiki/ git 트래킹 설정
```
