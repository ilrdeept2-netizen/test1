# 세션 기록: 레포 구조 정리 및 AG 활용방안

> 세션 일시: 2026-04-06
> 브랜치: `claude/organize-repo-structure-dJMUL`

---

## 작업 요약

GitHub 레포(`ilrdeept2-netizen/test1`)의 전체 구조를 파악하고, 미분류 파일을 주제별로 정리하고, AG 연동 활용방안 문서를 작성했습니다.

---

## 1. 레포 현황 분석 결과

### 전체 규모
- **총 76개 파일**, 4개 주요 디렉토리
- Python 15개, Markdown 36개, HTML 4개, 설정 5개, 스크립트 6개, 테스트 5개 등

### 정리 전 문제점
- `docs/` 루트에 5개 파일이 주제 분류 없이 방치
- 루트에 `compound-interest-visualization.html`이 단독으로 존재
- README.md가 실제 구조와 불일치

---

## 2. 수행한 작업

### 파일 이동 (6건)

| 원래 위치 | 이동 후 | 분류 근거 |
|-----------|---------|-----------|
| `docs/ai-wrapper-strategy.md` | `docs/research/` | AI 래퍼 전략 분석 → 리서치 |
| `docs/middle-east-conflict-summary.md` | `docs/research/` | 지정학 분석 → 리서치 |
| `docs/turboquant-explanation.md` | `docs/research/` | AI 기술 설명 → 리서치 |
| `docs/OpenClaw_Google_Embedding_설정_가이드.md` | `docs/claude-code/` | 도구 설정 가이드 → Claude Code |
| `docs/WHY.md` | `patent-tools/` | 특허 도구 설계 철학 → 해당 도구 폴더 |
| `compound-interest-visualization.html` (루트) | `tools/` | 시각화 도구 → 도구 폴더 |

### README.md 전면 업데이트
- 정리된 구조 반영한 디렉토리 트리
- 시각화 도구 섹션 신규 추가
- 문서 카테고리 표 추가 (claude-code, claude-cowork, claude-desktop, research, personal)

### AG 연동 활용방안 문서 신규 작성
- 경로: `docs/claude-code/AG_레포_연동_활용방안.md`
- 레포 5개 영역별 AG 활용 시나리오 및 추천 모델
- 4개 핵심 시나리오 (특허 도구 고도화, 리서치 후속 분석, Claude Code 가이드 적용, 새 도구 개발)
- 모델별 활용 전략표, 일일 워크플로우, 모바일 연동

---

## 3. 정리 후 최종 구조

```
test1/
├── patent-tools/              # 특허 문서 변환기 & 선행특허 검색
│   ├── app.py                       # Flask 웹 앱
│   ├── patent_format_converter.py   # Word/HWP → HLT 변환 엔진
│   ├── patent_search_app.py         # 선행특허 검색 CLI
│   ├── patent_search_web.py         # 선행특허 검색 웹 UI
│   ├── patent_specification_guide.md
│   ├── EASY_START.py
│   ├── WHY.md                       # ← docs/에서 이동
│   ├── scripts/                     # 실행 스크립트 (bat/sh)
│   ├── templates/                   # 웹 UI 템플릿
│   └── tests/                       # 테스트 코드 및 샘플
│
├── tools/                     # 유틸리티 도구 모음
│   ├── pdf-converter/               # PDF → PPT 변환기
│   ├── ai-news-digest/              # AI 뉴스 수집/요약
│   ├── compound-interest-visualization.html  # ← 루트에서 이동
│   ├── figma_visualization_sample.html
│   ├── greens_theorem_simulator.html
│   └── example.py
│
├── docs/                      # 문서 (주제별 분류)
│   ├── claude-code/ (11개)          # Claude Code 사용 가이드
│   │   ├── AG_레포_연동_활용방안.md        # ← 신규 작성
│   │   ├── Claude_Code_Agent_Teams_가이드.md
│   │   ├── Claude_Code_아키텍처_분석.md
│   │   ├── Claude_Code_예약작업_Scheduled_Tasks_가이드.md
│   │   ├── Claude_Code_플러그인_MCP_연동_정리.md
│   │   ├── Claude_Cowork_리걸플러그인_특허업무_활용_고찰.md
│   │   ├── OpenClaw_Google_Embedding_설정_가이드.md  # ← docs/에서 이동
│   │   ├── claude_code_AskUserQuestion_가이드.md
│   │   ├── 안그래비티_모바일_AG_연동_가이드.md
│   │   ├── 옵시디언_지식베이스_Claude_Code_연동_가이드.md
│   │   ├── 클로드코드_vs_웹앱_UX_비교조사.md
│   │   └── 플러그인_정리_및_특허업무_활용가이드.md
│   │
│   ├── claude-cowork/ (5개)         # Claude Cowork 배포/운영
│   │   ├── Claude_Cowork_윈도우_배포_가이드.md
│   │   ├── Claude_Cowork_특허업무_프롬프트_가이드.md
│   │   ├── Claude_멀티계정_연동_시나리오_분석.md
│   │   ├── claude-cowork-vm-fix-plan.md
│   │   └── fix_cowork_vhdx_access.ps1
│   │
│   ├── claude-desktop/ (8개)        # Claude Desktop 트러블슈팅
│   │   ├── CLAUDE_DESKTOP_CRASH_FIX_GUIDE.md
│   │   ├── CLAUDE_DESKTOP_크래시_근본해결.md
│   │   ├── claude-desktop-crash-fix-guide.md
│   │   ├── claude-desktop-outage-report-2026-02-10.md
│   │   ├── claude_desktop_guardian.ps1
│   │   ├── claude_desktop_guardian.sh
│   │   ├── fix_claude_desktop_crash.ps1
│   │   └── fix_instant_crash_deepclean.ps1
│   │
│   ├── research/ (15개)             # 리서치/분석 문서
│   │   ├── AI_GPU_커널_최적화_심층분석.md
│   │   ├── Antigravity_사용량_및_모델_가이드.md
│   │   ├── DeerFlow_분석_바이트댄스_AI에이전트.md
│   │   ├── GPT5.2_이론물리학_글루온진폭_연구정리.md
│   │   ├── Google_Gemini_Workspace_통합_분석.md
│   │   ├── WoW_한밤_PVP_티어리스트.md
│   │   ├── WoW_한밤_확장팩_PvP_가이드.md
│   │   ├── WoW_한밤_힐러_PVP_종합분석.md
│   │   ├── ai-wrapper-strategy.md          # ← docs/에서 이동
│   │   ├── antigravity_connection_test.md
│   │   ├── hanwha-solution-capital-increase.md
│   │   ├── middle-east-conflict-summary.md  # ← docs/에서 이동
│   │   ├── turboquant-explanation.md        # ← docs/에서 이동
│   │   ├── 바이브코딩_도구_총정리_2026.md
│   │   └── 이란전쟁_유가_TACO_시나리오_분석.md
│   │
│   └── personal/ (3개)              # 개인 메모
│       ├── session-2026-03-15-visualization.md
│       ├── 리나_건강이력_및_관리계획.md
│       └── 한울_촉촉_고구마스틱_보관법_조사.md
│
├── .github/workflows/         # GitHub Actions
├── requirements.txt
├── README.md                  # ← 전면 업데이트
└── .gitignore
```

---

## 4. 콘텐츠 카테고리별 요약

### 특허 도구 (patent-tools/)
특허 문서 자동 변환(Word/HWP → HLT) 및 선행특허 검색 도구. Flask 웹 앱 + CLI 제공. 원클릭 실행(EASY_START.py) 지원.

### 유틸리티 (tools/)
- **PDF → PPT 변환기**: PDF를 편집 가능한 파워포인트로 변환
- **AI 뉴스 다이제스트**: RSS 기반 AI/LLM 뉴스 자동 수집/요약
- **시각화 도구 3종**: 복리 계산기, 그린 정리 시뮬레이터, Figma 디자인 시각화

### Claude Code 가이드 (docs/claude-code/) - 11개
Agent Teams, 아키텍처 분석, 예약작업, MCP 플러그인 연동, AskUserQuestion, OpenClaw/Embedding 설정, AG 모바일 연동, 옵시디언 연동, UX 비교, 특허업무 플러그인, AG 레포 활용방안

### Claude Cowork (docs/claude-cowork/) - 5개
윈도우 배포, 특허업무 프롬프트, 멀티계정 연동, VM 트러블슈팅(VHDX)

### Claude Desktop (docs/claude-desktop/) - 8개
크래시 해결 가이드 3종, 장애 보고서, 가디언 스크립트(PS1/SH), 복구 스크립트 2종

### 리서치 (docs/research/) - 15개
- **AI/ML**: GPU 커널 최적화, DeerFlow 분석, GPT-5.2 물리학, TurboQuant, AI 래퍼 전략
- **도구/서비스**: Antigravity 가이드, Gemini Workspace, 바이브코딩 도구 총정리
- **금융/지정학**: 한화솔루션 유상증자, 이란전쟁 유가 시나리오, 중동 분쟁 요약
- **게임**: WoW 한밤 PVP 가이드 3종 (티어리스트, 확장팩, 힐러)

### 개인 메모 (docs/personal/) - 3개
시각화 세션 기록, 건강 관리 계획, 제품 보관법

---

## 5. 기술 스택 정리

| 분류 | 기술 |
|------|------|
| 백엔드 | Python (Flask, Streamlit) |
| 프론트엔드 | HTML5 (인터랙티브 시각화) |
| 문서 처리 | PDF, Word(.docx), HWP, XML/HLT |
| 자동화 | GitHub Actions (AI 뉴스 자동 수집) |
| 데이터 수집 | RSS, BeautifulSoup |
| AI 모델 연동 | Claude Opus/Sonnet, Gemini, MCP 서버 |

---

## 6. 커밋 정보

- **커밋**: `49780b5`
- **브랜치**: `claude/organize-repo-structure-dJMUL`
- **변경**: 8 files changed, 256 insertions, 24 deletions
