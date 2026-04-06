# LLM WIKI — Antigravity AG 도입 가이드

> Karpathy의 LLM WIKI 개념을 Google Antigravity(AG) 환경에 적용하는 단계별 가이드

---

## 개념 이해

### LLM WIKI가 필요한 이유

AG는 세션이 닫히면 대화 컨텍스트가 초기화된다.  
Claude Opus나 Gemini 3.1 Pro를 써도, 어제 결정한 아키텍처, 해결한 오류, 발명자 미팅 내용은 다음 세션에 없다.

**LLM WIKI = 세션 간 기억을 유지하는 구조화된 외부 메모리**

핵심 원칙:
- 모든 대화를 넣지 않는다 (토큰 낭비)
- 기준을 정하고 선별된 내용만 기록
- Cohere Reranking처럼 — 현재 작업과 관련된 섹션만 로드

---

## 1단계: WIKI 디렉토리 구조 설계

AG 프로젝트 루트에 `wiki/` 디렉토리를 생성한다.

```
프로젝트_루트/
├── .context/
│   └── WIKI_LOAD.md        ← AG 세션 시작 시 자동 주입 (짧게)
├── wiki/
│   ├── INDEX.md            ← 전체 WIKI 맵 (무엇이 어디에)
│   ├── decisions.md        ← 주요 결정사항 (왜 이 방향을 선택했나)
│   ├── architecture.md     ← 시스템 구조, 컴포넌트 역할
│   ├── errors.md           ← 해결된 오류 + 해결책
│   ├── patterns.md         ← 반복 사용하는 접근법/템플릿
│   └── context_YYYYMMDD.md ← 날짜별 현재 작업 스냅샷
└── (기존 프로젝트 파일들)
```

---

## 2단계: WIKI_LOAD.md 작성 (AG 시스템 프롬프트 역할)

AG의 "Project Instructions" 또는 Custom Instructions에 붙여넣는 핵심 파일.  
**300토큰 이내**로 유지한다.

```markdown
# 프로젝트 컨텍스트

## 이 세션 시작 전 반드시 읽을 것
- wiki/decisions.md — 확정된 설계 결정 목록
- wiki/errors.md — 재발하면 안 되는 오류 목록

## 현재 작업 상태
wiki/context_YYYYMMDD.md 참조

## WIKI 업데이트 기준
세션 종료 전 다음 중 하나라도 해당하면 wiki/에 기록:
- [ ] 아키텍처/구조 결정을 내렸다
- [ ] 오류를 해결했다 (원인 + 해결책)
- [ ] 반복 패턴을 발견했다
- [ ] 도메인 지식이 확인됐다 (특허 요건, API 동작 등)
- [ ] 사람(나)이 승인한 사항이 있다
```

---

## 3단계: AG에 WIKI 연결하는 방법

### AG Project Instructions 설정

1. AG 워크스페이스에서 `Settings` → `Project Instructions` 열기
2. 다음 내용을 붙여넣기:

```
세션 시작 시: wiki/INDEX.md를 읽어 현재 프로젝트 상태를 파악하라.
세션 진행 중: 아래 WIKI 업데이트 기준에 해당하는 내용이 생기면 즉시 wiki/에 기록하라.
세션 종료 전: wiki/context_오늘날짜.md를 최신 상태로 업데이트하라.

WIKI 업데이트 기준 (이것만 기록):
1. 설계 결정 → decisions.md
2. 오류 해결 → errors.md (오류명, 원인, 해결책, 재발방지)
3. 반복 패턴 → patterns.md
4. 현재 작업 스냅샷 → context_YYYYMMDD.md
```

### Anti-API 경유 사용 시 (시스템 프롬프트 주입)

Anti-API를 통해 모바일에서 AG에 접근하는 경우:

```json
// config.json에 system_prompt 추가
{
  "system_prompt": "세션 시작 시 wiki/INDEX.md를 읽어라. WIKI 업데이트 기준: 설계결정→decisions.md, 오류해결→errors.md, 현재상태→context_오늘날짜.md",
  "accounts": [...]
}
```

---

## 4단계: WIKI 기록 기준 (Cohere Reranking 원칙 적용)

### 넣는 것 (선별 기준)

| 카테고리 | 예시 | 저장 위치 |
|----------|------|-----------|
| 아키텍처 결정 | "청구항 파서는 regex 대신 LLM으로 결정" | decisions.md |
| 오류 해결 | "sgmllib3k 설치 실패 → sgmllib 직접 설치" | errors.md |
| 반복 패턴 | "HLT 변환은 항상 UTF-8-sig 인코딩" | patterns.md |
| 도메인 지식 | "한국 특허청 OA 응답 기한 3개월" | patterns.md |
| 사람 승인 사항 | "발명자가 청구항 2개 삭제 승인" | context_날짜.md |

### 넣지 않는 것

- 단순 코드 생성 내용 (코드 자체가 기록)
- 임시 디버깅 대화 ("이거 왜 안 돼?")
- 이미 코드/문서에 반영된 내용
- 단발성 질의응답

---

## 5단계: 날짜별 컨텍스트 스냅샷 형식

`wiki/context_20260406.md` 예시:

```markdown
# 작업 컨텍스트 스냅샷 — 2026-04-06

## 현재 작업
- [ ] 특허 명세서 HLT 변환 모듈 리팩토링
- [x] OA 의견서 초안 완료 (삼성 건)

## 다음 세션에서 시작할 것
1. patent_format_converter.py의 claim_parser() 수정
2. 발명자 미팅 결과 반영 (decisions.md에 추가됨)

## 주의사항
- 현재 테스트 환경: Python 3.11, Windows 11
- HWP 파일은 olefile로만 처리 (python-hwp 사용 금지 — errors.md 참조)

## 미결 질문
- API rate limit 초과 시 fallback 모델은 Gemini Flash로 할지 결정 필요
```

---

## 6단계: Phone Connect 환경에서 WIKI 활용

모바일(Phone Connect)로 AG를 모니터링하는 경우:

```
[데스크톱 AG]                        [모바일 Phone Connect]
     │                                        │
     ├─ 세션 시작 → WIKI 자동 로드 ─────→ 진행 상황 확인
     │                                        │
     ├─ 작업 중 결정 사항 → WIKI 기록 ──→ 실시간 확인
     │                                        │
     └─ 세션 종료 전 → context 업데이트 ─→ 다음 날 모바일에서 확인
```

---

## 7단계: 운영 루틴

### 세션 시작 체크리스트

```
□ AG Project Instructions에 WIKI 로드 지시가 있는지 확인
□ wiki/context_오늘날짜.md 존재 여부 확인
□ 어제 작업이 있었다면 어제 context 파일 확인
```

### 주간 WIKI 정리 (토요일 10분)

```
□ decisions.md — 중복/폐기된 결정 제거
□ errors.md — 해결 완료된 오류 "✅ 해결" 표시
□ patterns.md — 3회 이상 사용된 패턴만 유지
□ context_*.md — 2주 이상 된 파일은 archive/ 이동
```

---

## 실전 예시: 특허 업무에서의 WIKI 흐름

```
[AG 세션 1 — 특허 명세서 작성]
  발명자 미팅 후 핵심 청구항 확정
  → decisions.md에 "청구항 1: 방법 발명, 청구항 5: 장치 발명 확정"

[AG 세션 2 — 다음 날]
  세션 시작 → wiki/decisions.md 자동 로드
  → "어제 청구항 확정됐구나" 컨텍스트 복원
  → 이어서 명세서 작성 시작 (처음부터 설명 불필요)

[AG 세션 3 — OA 대응]
  오류 발생: HWP 파일 파싱 실패
  해결 후 → errors.md에 기록
  → 다음에 같은 오류 발생 시 즉시 참조
```

---

## 요약

| 단계 | 작업 | 소요 시간 |
|------|------|-----------|
| 1 | wiki/ 디렉토리 구조 생성 | 5분 |
| 2 | WIKI_LOAD.md 작성 | 10분 |
| 3 | AG Project Instructions에 연결 | 5분 |
| 4 | 기준 내재화 (뭘 넣을지) | 운영하며 체득 |
| 5 | 날짜별 context 스냅샷 습관화 | 세션당 3분 |
| 6 | 주간 정리 루틴 | 주 1회 10분 |

> **핵심:** WIKI는 "모든 것을 기억하는 시스템"이 아니다.  
> "다음 세션의 나에게 꼭 필요한 것"만 남기는 큐레이션 시스템이다.
