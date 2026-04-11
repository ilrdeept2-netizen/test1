# Claude Code 예약 작업(Scheduled Tasks) 기능 가이드

## 개요

Claude Code에 **예약 작업(Scheduled Tasks)** 기능이 출시되었습니다.
한 번 설정하면 Claude Code가 자동으로 반복 실행하며, 프롬프트 입력이나 수동 관리가 필요 없습니다.

## 핵심 개념

```
설정 한 번 → Claude Code 자동 실행 → 결과 확인
```

- **No Prompting**: 매번 명령을 입력할 필요 없음
- **No Reminders**: 알림을 설정하거나 기억할 필요 없음
- **No Babysitting**: 실행 과정을 감시할 필요 없음

## 자동화 가능한 작업

### 1. 일일 커밋 리뷰 (Daily Commit Reviews)
- 매일 자동으로 커밋 내역을 검토
- 코드 품질, 컨벤션 위반, 잠재적 버그 탐지
- 팀 전체의 커밋을 자동 분석하여 리포트 생성

### 2. 주간 의존성 감사 (Weekly Dependency Audits)
- 매주 프로젝트 의존성 패키지를 점검
- 보안 취약점이 있는 패키지 탐지
- 업데이트가 필요한 패키지 목록 제공
- `npm audit`, `pip audit` 등의 작업을 자동 수행

### 3. 에러 로그 스캔 (Error Log Scans)
- 서버/애플리케이션 로그를 주기적으로 분석
- 반복되는 에러 패턴 식별
- 심각도별 분류 및 우선순위 제안

### 4. PR 리뷰 (PR Reviews)
- 새로 생성된 Pull Request를 자동으로 리뷰
- 코드 스타일, 로직 오류, 성능 이슈 점검
- 리뷰 코멘트 자동 작성

### 5. 기타 반복 개발 작업
- 테스트 실행 및 결과 보고
- 코드 포맷팅/린팅 자동 적용
- 문서 업데이트 확인
- 빌드 상태 모니터링
- 데이터베이스 마이그레이션 상태 점검

## 활용 시나리오

### 시나리오 1: 야간 자동 워크플로우
```
[밤 동안 자동 실행]
1. 전체 테스트 스위트 실행
2. 실패한 테스트에 대한 원인 분석
3. 의존성 업데이트 확인
4. 아침에 결과 리포트 확인
```

### 시나리오 2: 지속적 코드 품질 관리
```
[매일 자동 실행]
1. 새로운 커밋의 코드 품질 분석
2. 코드 복잡도 메트릭 추적
3. 기술 부채 식별 및 추적
```

### 시나리오 3: 보안 모니터링
```
[매주 자동 실행]
1. 의존성 보안 취약점 스캔
2. 코드 내 하드코딩된 시크릿 탐지
3. 보안 업데이트 권고사항 제공
```

## 주요 장점

| 장점 | 설명 |
|------|------|
| **시간 절약** | 반복 작업을 자동화하여 개발에 집중 |
| **일관성** | 사람의 실수 없이 매번 동일한 기준으로 검토 |
| **24/7 운영** | 야간/주말에도 자동으로 작업 수행 |
| **조기 발견** | 문제를 빠르게 탐지하여 대응 시간 단축 |

## 참고 사항

- 개발자들이 이미 완전 자동화된 워크플로우를 야간에 실행하는 데모를 공유하고 있음
- 설정 후 사람의 개입 없이 작동하는 것이 핵심 특징
- 반복적이고 정형화된 개발 업무에 특히 적합

---

## 이 레포 적용안 (ilrdeept2-netizen/test1)

아래 3건은 이 레포에 바로 등록해서 쓸 수 있도록 설정값과 전체 프롬프트를 묶어 둔 카탈로그입니다.
Claude Code 웹에서 **New Scheduled Job → Repository / Schedule / Prompt** 3칸에 그대로 붙여 넣으면 됩니다.

이 레포는 이미 다음을 GitHub Actions로 자동화하고 있으므로 **중복 등록하지 말 것**:
- `ai_news_digest.yml` — 매일 AI 뉴스 다이제스트 수집/이슈 생성
- `knowledge_index.yml` — `master` 푸시 시 `docs/KNOWLEDGE_INDEX.md` 자동 갱신

아래 작업들은 단순 크론으로는 하기 어려운, **자연어 판단/요약/이슈 코멘트 작성**이 필요한 것만 골랐습니다.

---

### 작업 1. 주간 지식DB 건강검진

| 항목 | 값 |
|------|----|
| **Repository** | `ilrdeept2-netizen/test1` |
| **Schedule** | 매주 월요일 09:00 KST (UTC 기준 일요일 00:00, cron `0 0 * * 1`) |
| **목적** | `docs/` 지식 DB의 메타데이터 일관성, 링크 무결성, 태그 누락 점검 |

**프롬프트:**

```
당신은 이 레포(ilrdeept2-netizen/test1)의 docs/ 지식 DB 관리자입니다.
docs/_meta/STANDARDS.md에 정의된 YAML frontmatter 표준에 따라
전체 docs/ 트리를 건강검진하고, 결과를 GitHub 이슈로 리포트하세요.

점검 항목:
1. Frontmatter 필드 누락
   - 필수 필드(title, date, category, tags, status, summary)가 빠진 문서
   - category가 STANDARDS.md의 카테고리 목록에 없는 값
   - status가 draft/active/archived 중 하나가 아닌 문서
2. 태그 위생
   - tags가 3개 미만이거나 7개 초과인 문서
   - STANDARDS.md 태그 풀에 없는 새 태그를 쓰는 문서 (이름 제시)
3. 링크 무결성
   - 마크다운 내부 링크(relative path)가 실제 파일을 가리키지 않는 경우
   - related 필드에 적힌 경로가 존재하지 않는 경우
4. 중복/유사 문서 탐지
   - 제목 또는 summary 유사도가 높은 문서 쌍 (리뷰 대상으로만 제안)
5. 양방향 related 누락
   - A가 B를 related로 가리키는데 B에는 A가 없는 경우

출력 형식:
- 이슈 제목: "🩺 주간 지식DB 건강검진 — YYYY-MM-DD"
- 라벨: knowledge-db, automated, health-check
- 본문: 위 5개 항목별로 표로 정리. 각 항목 행에는
  파일 경로, 문제, 제안 수정안을 포함.
- 문제가 0건이면 이슈를 만들지 말고 로그에만 "이상 없음" 기록.

주의:
- 코드 수정이나 PR은 만들지 말 것. 리포트 이슈만 생성.
- docs/_meta/ 내부 문서와 docs/KNOWLEDGE_INDEX.md는 점검 대상에서 제외.
- docs/personal/ 문서는 private으로 간주, 내용 인용 금지 (경로만 노출).
```

---

### 작업 2. 주간 의존성 보안 감사

| 항목 | 값 |
|------|----|
| **Repository** | `ilrdeept2-netizen/test1` |
| **Schedule** | 매주 월요일 10:00 KST (cron `0 1 * * 1` UTC) |
| **목적** | `requirements.txt`의 취약 패키지와 업그레이드 후보 식별 |

**프롬프트:**

```
당신은 이 레포(ilrdeept2-netizen/test1)의 Python 의존성 보안 감사자입니다.
requirements.txt를 주간 단위로 감사하고 결과를 이슈로 리포트하세요.

수행 절차:
1. requirements.txt를 읽어 모든 패키지 + 최소 버전을 파싱.
   (주석 처리된 패키지는 스킵, 이유만 언급)
2. 각 패키지에 대해 다음을 확인:
   a. pip install + pip-audit 실행, 알려진 CVE 탐지
      (pip-audit이 설치되어 있지 않으면 설치 후 실행)
   b. PyPI에서 현재 최신 버전 확인
   c. requirements.txt에 적힌 최소 버전과의 차이(major/minor/patch)
3. 각 취약점에 대해 심각도(Critical/High/Medium/Low)와
   영향 범위(이 레포에서 해당 모듈을 실제 사용하는지)를 판단.
   - patent-tools/, tools/pdf-converter/, tools/ai-news-digest/ 중
     어디서 쓰이는지 grep으로 빠르게 확인.

출력 형식:
- 이슈 제목: "🔐 주간 의존성 보안 감사 — YYYY-MM-DD"
- 라벨: security, dependencies, automated
- 본문 구조:
  ## 1. 취약점 요약
  | 패키지 | 현재 최소버전 | CVE | 심각도 | 이 레포 영향 |
  ## 2. 업그레이드 후보 (CVE 없음)
  | 패키지 | 현재 | 최신 | major 변경 여부 |
  ## 3. 권고 조치
  - 즉시 올릴 것 (Critical/High)
  - 검토 후 올릴 것 (Medium/Low)
  - 스킵 권장 (사용되지 않는 모듈)

주의:
- 직접 requirements.txt를 수정하거나 PR을 만들지 말 것. 리포트만.
- 취약점이 0건이고 major 업그레이드 후보도 0건이면 이슈 생성 생략.
- Python 3.11 환경 기준으로 판단.
```

---

### 작업 3. 월간 오래된 문서 발굴

| 항목 | 값 |
|------|----|
| **Repository** | `ilrdeept2-netizen/test1` |
| **Schedule** | 매월 1일 09:00 KST (cron `0 0 1 * *` UTC) |
| **목적** | 90일 이상 미수정 문서의 유효성 재검토, archive/update/삭제 제안 |

**프롬프트:**

```
당신은 이 레포(ilrdeept2-netizen/test1)의 지식 DB 큐레이터입니다.
docs/ 아래에서 "오래된 문서"를 발굴하고 어떻게 할지 제안하는 이슈를 만드세요.

발굴 기준:
- git log로 각 docs/**/*.md의 마지막 커밋 날짜를 확인
- 마지막 커밋이 오늘 기준 90일 이상 지난 문서만 대상
- docs/_meta/, docs/KNOWLEDGE_INDEX.md, docs/personal/ 는 제외
- frontmatter의 status가 이미 archived인 문서도 제외

각 대상 문서에 대해 판단:
1. 문서 카테고리와 주제를 읽는다
2. 현재도 유효한 정보인지 빠르게 평가:
   - Claude/LLM 생태계 변화 반영 필요? (모델명, 기능 변화 등)
   - 가리키는 외부 링크/플러그인이 아직 존재?
   - 더 최신 문서가 docs/에 추가되어 중복이 된 상태?
3. 셋 중 하나로 제안:
   a. KEEP: 여전히 유효, 아무 조치 없음 (왜 유효한지 한 줄)
   b. UPDATE: 부분 갱신 필요 (어느 섹션을 왜 고쳐야 하는지)
   c. ARCHIVE: status를 archived로 내릴 것 (이유)
   d. MERGE: 다른 문서로 통합 제안 (대상 문서 경로)

출력 형식:
- 이슈 제목: "🗂️ 월간 오래된 문서 재평가 — YYYY-MM"
- 라벨: knowledge-db, curation, automated
- 본문:
  | 문서 | 마지막 수정 | 판정 | 이유/제안 |
  - KEEP 판정은 별도 표에 묶어서 간단히
  - UPDATE/ARCHIVE/MERGE 판정은 이유를 2~3줄로 구체적으로

주의:
- 어떤 문서도 직접 수정/이동/삭제하지 말 것. 판정 리포트만 생성.
- 판단이 애매한 문서는 KEEP으로 기본값, 이유에 "재검토 필요" 표시.
- 대상 문서가 0건이면 이슈 생성 생략.
```

---

### 등록 체크리스트

- [ ] Claude Code 웹 → Scheduled Jobs → New
- [ ] Repository: `ilrdeept2-netizen/test1` 연결 (아직 안 했다면 권한 부여)
- [ ] 위 3건을 각각 schedule + prompt 복붙해서 생성
- [ ] 첫 실행 후 생성되는 이슈의 품질을 확인하고, 필요하면 프롬프트를 이 문서에서 수정 → 재등록
- [ ] 각 작업에 라벨(`automated`, `health-check`, `security`, `curation`)이 실제로 레포에 존재하는지 확인, 없으면 먼저 생성

---

*작성일: 2026-03-09*
*이 레포 적용안 추가: 2026-04-11*
*Claude Code Scheduled Tasks 기능 소개 및 활용 가이드*
