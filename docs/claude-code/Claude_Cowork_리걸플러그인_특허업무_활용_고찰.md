# Claude Cowork 리걸 플러그인 및 특허업무 활용 방안 고찰

> 작성일: 2026-03-12
> 목적: Claude Cowork의 Legal 플러그인을 포함한 주요 플러그인의 기능을 정리하고, 특허업무에의 실질적 활용 방안을 고찰한다.

---

## 1부: Claude Cowork 리걸(Legal) 플러그인 개요

### 1.1 출시 배경

2026년 1월 12일, Anthropic은 **Claude Cowork**를 출시했다. 이는 Claude Code와 동일한 기반 위에 만들어진 자율형 데스크톱 에이전트로, 로컬 파일을 직접 읽고 편집할 수 있다.

2026년 2월 2일, Anthropic은 **Legal 플러그인**을 공식 출시했다. 이는 파운데이션 모델 회사가 법률 워크플로우 제품을 자사 플랫폼에 직접 탑재한 최초 사례로, 기존 법률 기술(LegalTech) 벤더에 API만 제공하던 방식과 근본적으로 다른 접근이다.

### 1.2 시장 반응

Legal 플러그인 발표 직후 법률 정보 서비스 기업들의 주가가 급락했다:
- Thomson Reuters: **-16%**
- Wolters Kluwer: **-10%**
- LegalZoom: **-23.7%**

이는 파운데이션 모델이 법률 업무를 직접 수행할 수 있다는 시장의 인식 변화를 반영한다.

### 1.3 가격 및 접근

- Claude Pro($20/월) 및 Team 구독에 **무료 포함**
- 별도 설치 없이 Claude Cowork 내에서 활성화

---

## 2부: Legal 플러그인의 핵심 기능

### 2.1 주요 슬래시 커맨드

| 명령어 | 기능 | 상세 |
|--------|------|------|
| `/review-contract` | **계약서 검토** | 업로드된 계약서의 핵심 조항, 잠재적 위험, 비정상 조항, 누락 표준 조항을 분석·플래깅 |
| `/triage-nda` | **NDA 분류** | NDA를 표준/공격적/비표준으로 분류, 핵심 조항 식별 및 이상 요소 플래깅 |
| `/vendor-check` | **벤더 계약 점검** | 책임 한도, 면책, 보험, 데이터 보호, 해지권 등 표준 보호 조항 체크리스트 평가 |
| `/brief` | **브리핑 생성** | 일일 브리핑, 주제 리서치, 사건 대응 브리핑 등 맥락적 요약 생성 |
| `/respond` | **정형 응답 생성** | 정보주체 요청(DSAR), 디스커버리 홀드 등 공통 문의에 대한 템플릿 기반 응답 |

### 2.2 계약서 분석 기능 상세

- **신호등 시스템**: 조항별 위험도를 3단계로 표시
  - 🟢 **녹색** (OK): 표준적이고 수용 가능한 조항
  - 🟡 **황색** (주의): 리스크가 있으나 협상 가능한 조항
  - 🔴 **적색** (위험): 즉시 주의가 필요한 위험 조항
- **협상 플레이북 연동**: 조직의 자체 협상 기준(playbook)에 따라 분석 기준을 커스터마이즈
- **레드라인 제안**: 회사 정책에 맞는 수정안 자동 생성
- **전체 맥락 분석**: 개별 조항이 아닌 계약서 전체 맥락에서 조항 간 상호작용 분석

### 2.3 Pramata 확장(Extension)

Pramata는 Claude Cowork Legal 플러그인용 Extension을 제공하여, 기업이 보유한 **기존 계약서 데이터베이스**의 맥락을 Claude의 분석에 추가한다. 이를 통해:
- 기존 거래 관계 맥락을 반영한 계약서 검토
- 플레이북 기반 분석
- 템플릿 기반 초안 작성

### 2.4 기술적 본질과 한계

Legal 플러그인은 본질적으로 **정교하게 작성된 시스템 프롬프트(~200줄의 마크다운)**이며, 법률 AI 플랫폼이 아니다.

**한계:**
- 검증 레이어(verification layer) 없음
- 반환각(anti-hallucination) 파이프라인 없음
- 관할권별(jurisdiction-specific) 로직 없음
- 특허 분석 기능은 **현재 미포함**
- Anthropic은 "조언(advice)"이 아닌 "보조(assistance)"임을 명시하며, 면허 있는 변호사의 검토를 권고

---

## 3부: Claude Code/Cowork의 플러그인 확장 체계

### 3.1 확장 방식 종류

Claude Code는 다음 5가지 방식으로 기능을 확장할 수 있다:

| 확장 방식 | 난이도 | 범위 | 최적 용도 |
|-----------|--------|------|-----------|
| **Skills** (커스텀 슬래시 커맨드) | 쉬움 | 개인→팀 | 반복적 워크플로우 자동화 |
| **MCP 서버** | 중간 | 개인→프로젝트 | 외부 도구/DB 연동 |
| **Hooks** (이벤트 훅) | 중간 | 개인→프로젝트 | 이벤트 기반 자동화 |
| **Plugins** (패키지) | 높음 | 팀→커뮤니티 | 배포 가능한 확장 번들 |
| **Subagents** (커스텀 에이전트) | 높음 | 개인→프로젝트 | 복잡한 전문 워크플로우 |

### 3.2 MCP(Model Context Protocol) 서버

MCP는 AI와 외부 시스템 간 양방향 연결을 위한 오픈 표준이다. 현재 1,000개 이상의 MCP 서버가 생태계에 존재한다.

**연결 방식:**
```bash
# HTTP (원격 서버, 권장)
claude mcp add --transport http notion https://mcp.notion.com/mcp

# Stdio (로컬 프로세스)
claude mcp add --transport stdio db -- npx -y @bytebase/dbhub --dsn "postgresql://..."
```

**특허업무 관련 주요 MCP 서버:**
- **SQLite MCP**: 특허 데이터베이스(예: PatentLLM의 173만 건 merged_patents.db) 직접 조회
- **GitHub MCP**: 특허 관련 코드/문서 저장소 연동
- **Notion MCP**: 특허 업무 관리 보드 연동
- **Slack MCP**: 발명자/담당자 간 커뮤니케이션 자동화

### 3.3 Skills (커스텀 슬래시 커맨드)

`.claude/skills/` 디렉토리에 SKILL.md 파일을 생성하여 커스텀 명령어를 만들 수 있다.

```yaml
---
name: patent-review
description: 특허 명세서 검토 및 기재불비 점검
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
---

업로드된 특허 명세서를 검토하고 다음 항목을 점검해줘:
1. 필수 섹션(기술분야, 배경기술, 해결과제, 발명의 효과 등) 포함 여부
2. 청구항과 상세한 설명 간 불일치
3. 도면 번호 누락 또는 불일치
4. 용어 통일성
...
```

### 3.4 Plugins (패키지형 확장)

플러그인은 Skills, Hooks, MCP 서버, 에이전트를 하나의 패키지로 묶어 배포할 수 있는 형태이다.

```
patent-plugin/
├── .claude-plugin/
│   └── plugin.json           # 매니페스트
├── skills/
│   ├── patent-review/SKILL.md
│   ├── prior-art-search/SKILL.md
│   └── oa-response/SKILL.md
├── agents/
│   └── patent-analyst/agent.md
├── hooks/
│   └── hooks.json
└── .mcp.json                 # KIPRIS API MCP 연동
```

---

## 4부: 특허업무 활용 방안 — 실질적 고찰

### 4.1 Legal 플러그인의 특허업무 적용 가능성

현재 Legal 플러그인은 **계약서 검토, NDA 분류, 벤더 점검** 등 기업법무(in-house counsel) 워크플로우에 초점이 맞춰져 있으며, **특허 분석 기능은 포함되어 있지 않다.**

그러나 Legal 플러그인의 접근 방식에서 특허업무에 차용할 수 있는 패턴이 있다:

| Legal 플러그인 패턴 | 특허업무 적용 | 구현 방안 |
|---------------------|-------------|-----------|
| 계약서 신호등 시스템 (녹/황/적) | **청구항 강도 평가** — 각 청구항의 권리범위 강도를 시각적으로 표시 | 커스텀 Skill 개발 |
| 플레이북 기반 분석 | **심사기준 기반 명세서 점검** — KIPO 심사기준을 플레이북으로 설정 | 커스텀 Skill + 레퍼런스 파일 |
| 레드라인 제안 | **보정안 자동 생성** — OA 거절이유 대비 보정 제안 | 커스텀 Skill 개발 |
| NDA 분류 | **특허 문서 분류** — 출원서/보정서/의견서/심판청구서 자동 분류 | 커스텀 Skill 개발 |
| Pramata Extension | **KIPRIS 연동** — 기존 선행기술 DB 맥락 반영 | MCP 서버 개발 |

### 4.2 특허업무별 구체적 활용 시나리오

#### 시나리오 A: 명세서 작성 단계

```
현재 가능한 것 (기존 도구 조합):
├── patent_specification_guide.md  → AI 프롬프트로 명세서 초안 작성
├── patent_search_app.py           → 선행기술 자동 조사
└── Claude Code Agent Teams       → 병렬 작업 (선행조사 + 청구항 + 도면)

Legal 플러그인 패턴을 차용하여 추가 가능한 것:
├── /check-specification  → 명세서 기재불비 자동 점검 (신호등 시스템)
├── /review-claims        → 청구항 권리범위 분석 및 강도 평가
└── /compare-prior-art    → 선행기술 대비 진보성 시각적 비교
```

#### 시나리오 B: OA(의견제출통지서) 대응 단계

```
Legal 플러그인의 /review-contract 패턴 차용:

/review-oa 명령 구상:
1. OA 문서 업로드
2. 거절이유 유형 자동 분류 (신규성/진보성/기재불비/산업상이용가능성)
3. 인용발명 대비 본 발명 차이점 자동 분석
4. 보정 방향 제안 (녹/황/적으로 보정 난이도 표시)
   🟢 단순 보정으로 극복 가능
   🟡 실질적 보정 필요하나 극복 가능성 있음
   🔴 보정으로 극복 곤란 — 분할출원/포기 검토 필요
5. 보정 청구항 초안 + 의견서 초안 자동 생성
```

#### 시나리오 C: 특허 포트폴리오 관리

```
Legal 플러그인의 /vendor-check 패턴 차용:

/portfolio-check 명령 구상:
1. 특허 포트폴리오 목록(스프레드시트/DB) 연동 (MCP)
2. 각 특허별 상태 자동 점검:
   - 연차료 납부 기한
   - 해외출원 기한(우선권 12개월)
   - 심사청구 기한(3년)
   - OA 응답 기한
3. 기한 임박 건 자동 알림 (Hooks + Slack MCP)
```

#### 시나리오 D: 발명 신고 → 출원 End-to-End 자동화

```
┌─────────────────────────────────────────────────────────────┐
│          특허업무 자동화 워크플로우 (플러그인 활용)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [1] 발명신고서 수령                                         │
│       ↓  (Claude Cowork: 로컬 파일 자동 감지)               │
│  [2] /triage-invention — 발명 분류 및 출원 가치 평가          │
│       ↓  (Legal 플러그인 /triage-nda 패턴 차용)             │
│  [3] /search-prior-art — 선행기술 자동 조사                  │
│       ↓  (KIPRIS MCP 서버 연동)                             │
│  [4] /draft-specification — 명세서 초안 작성                  │
│       ↓  (patent_specification_guide.md 활용)               │
│  [5] /check-specification — 기재불비 점검 (신호등)            │
│       ↓  (Legal 플러그인 /review-contract 패턴)             │
│  [6] /convert-hlt — HLT 변환                                │
│       ↓  (patent_format_converter.py)                       │
│  [7] 전자출원                                                │
│       ↓                                                     │
│  [8] /monitor-oa — OA 모니터링 (예약 작업)                   │
│       ↓  (Hooks: 주기적 확인)                               │
│  [9] /review-oa — OA 대응 (수신 시 자동 분석)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 현재 환경에서의 구현 우선순위

현재 이 계정의 실제 환경(MCP 서버 없음, Skills 1개, Hooks 1개)을 감안한 단계적 구현 로드맵:

#### Phase 1: 즉시 구현 가능 (커스텀 Skills 추가)

| 우선순위 | Skill 이름 | 기능 | 난이도 |
|---------|-----------|------|--------|
| 1 | `/check-specification` | 명세서 기재불비 자동 점검 | 낮음 |
| 2 | `/review-claims` | 청구항 분석 및 권리범위 평가 | 낮음 |
| 3 | `/review-oa` | OA 분석 및 대응안 생성 | 중간 |
| 4 | `/triage-invention` | 발명 분류 및 출원 가치 평가 | 중간 |

#### Phase 2: MCP 서버 연동 (외부 데이터 접근)

| 우선순위 | MCP 연동 | 용도 |
|---------|----------|------|
| 1 | SQLite MCP + 특허 DB | 자체 특허 포트폴리오 관리 |
| 2 | KIPRIS API 연동 | 실시간 선행기술 조사 |
| 3 | Notion/Slack MCP | 업무 관리 및 커뮤니케이션 |

#### Phase 3: 플러그인 패키징 (팀 공유)

- 위 Skills + MCP를 하나의 플러그인으로 패키징
- 팀원들과 공유 가능한 형태로 배포

---

## 5부: Legal 플러그인과 특허 플러그인의 비교 전망

### 5.1 Legal 플러그인이 특허를 다루지 않는 이유

| 요인 | 설명 |
|------|------|
| **대상 사용자** | 기업법무(in-house counsel)에 초점. 특허는 별도 전문 분야 |
| **문서 구조 차이** | 계약서는 조항 중심, 특허는 청구항+도면+명세서의 복합 구조 |
| **분석 복잡도** | 특허는 선행기술 대비 신규성·진보성 판단이 필요하며, 이는 계약서 검토보다 복잡 |
| **관할권 의존도** | 특허는 국가별 특허법·심사기준이 크게 다름 (한국 KIPO, 미국 USPTO, 유럽 EPO 등) |
| **시장 규모** | 기업법무 시장이 특허 시장보다 크고, 먼저 진입하는 것이 전략적 |

### 5.2 향후 특허 전용 플러그인 등장 가능성

Legal 플러그인의 시장 반응을 고려할 때, Anthropic 또는 서드파티에서 **특허 전용 플러그인**이 등장할 가능성이 높다:

**예상 기능:**
- `/draft-claims` — 발명 설명에서 청구항 자동 생성
- `/check-patentability` — 특허성(신규성/진보성/산업상이용가능성) 사전 평가
- `/prior-art-analysis` — 선행기술 자동 비교 분석
- `/oa-response` — OA 대응 보정안 + 의견서 자동 생성
- `/fto-analysis` — Freedom-to-Operate 침해 위험 분석
- `/family-tree` — 특허 패밀리 관계도 자동 생성

### 5.3 우리가 지금 할 수 있는 것

특허 전용 플러그인을 기다리지 않고, **Claude Code의 확장 체계(Skills + MCP + Hooks)를 활용하여 자체 특허업무 자동화 환경을 구축**할 수 있다. 이미 이 리포지토리에 핵심 도구들(변환기, 선행조사 앱, 명세서 가이드)이 갖춰져 있으므로, 이를 Claude Code Skills로 래핑하면 Legal 플러그인과 유사한 수준의 워크플로우 자동화가 가능하다.

---

## 6부: 결론

### 핵심 요약

1. **Claude Cowork Legal 플러그인**은 계약서 검토·NDA 분류·벤더 점검 등 기업법무에 특화되어 있으며, 특허 기능은 현재 미포함이다.

2. 그러나 Legal 플러그인의 **접근 방식**(신호등 시스템, 플레이북 기반 분석, 레드라인 제안 등)은 특허업무에 충분히 차용 가능하다.

3. Claude Code의 **확장 체계(Skills, MCP, Hooks, Plugins)**를 활용하면, Legal 플러그인과 동등하거나 그 이상의 특허업무 자동화를 자체 구현할 수 있다.

4. **단기적으로는** 커스텀 Skills 개발이 가장 현실적이며, **중기적으로는** KIPRIS MCP 서버 연동, **장기적으로는** 팀 공유형 특허 플러그인 패키징이 목표가 될 수 있다.

5. 현재 리포지토리에 이미 갖춰진 도구들(특허 문서 변환기, 선행특허조사 앱, 명세서 작성 가이드)은 이러한 자동화의 **강력한 기반**이 된다.

---

## 참고 자료

- [Claude Cowork Legal Plugin - Anthropic 공식](https://claude.com/plugins/legal)
- [Claude Cowork Legal Plugin Tutorial](https://claudecowork.im/blog/legal-plugin-tutorial)
- [Anthropic's Legal Plugin - LawSites 분석](https://www.lawnext.com/2026/02/anthropics-legal-plugin-for-claude-cowork-may-be-the-opening-salvo-in-a-competition-between-foundation-models-and-legal-tech-incumbents.html)
- [Anthropic Moves Into Legal Tech - Artificial Lawyer](https://www.artificiallawyer.com/2026/02/02/anthropic-moves-into-legal-tech/)
- [Pramata Extension for Legal Plugin](https://www.pramata.com/blog/claude-cowork-legal-plugin-contract-management/)
- [Claude Cowork Legal Beyond the Hype - Kallam](https://www.kallam.ai/blog/claude-cowork-legal-beyond-hype)
- [Claude Code MCP 공식 문서](https://code.claude.com/docs/en/mcp)
- [Claude Code Skills 공식 문서](https://code.claude.com/docs/en/skills)
- [Claude Code Plugins 공식 문서](https://code.claude.com/docs/en/plugins)
- [50+ Best MCP Servers for Claude Code](https://claudefa.st/blog/tools/mcp-extensions/best-addons)
