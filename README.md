# test1 - 업무 도구 및 문서 모음

특허 업무 도구, PDF 변환기, AI 뉴스 다이제스트, 시각화 도구, Claude 관련 가이드 등을 포함하는 레포지토리입니다.

---

## 프로젝트 구조

```
.
├── patent-tools/              # 특허 문서 변환기 & 선행특허 검색
│   ├── app.py                       # Flask 웹 앱
│   ├── patent_format_converter.py   # Word/HWP → HLT 변환 엔진
│   ├── patent_search_app.py         # 선행특허 검색 CLI
│   ├── patent_search_web.py         # 선행특허 검색 웹 UI
│   ├── patent_specification_guide.md  # 특허 명세서 작성 가이드
│   ├── EASY_START.py                # 간편 실행 스크립트
│   ├── WHY.md                       # 설계 철학 & 배경
│   ├── scripts/                     # 실행 스크립트 (bat/sh)
│   ├── templates/                   # 웹 UI 템플릿
│   └── tests/                       # 테스트 코드 및 샘플 파일
│
├── tools/                     # 유틸리티 도구 모음
│   ├── pdf-converter/               # PDF → PPT 변환기
│   ├── ai-news-digest/              # AI 뉴스 수집/요약
│   ├── compound-interest-visualization.html  # 복리 계산 시각화
│   ├── figma_visualization_sample.html       # Figma 디자인 시각화
│   ├── greens_theorem_simulator.html         # 그린 정리 시뮬레이터
│   └── example.py
│
├── docs/                      # 문서 (주제별 분류)
│   ├── claude-code/                 # Claude Code 사용 가이드 (10개)
│   │   ├── Claude_Code_Agent_Teams_가이드.md
│   │   ├── Claude_Code_아키텍처_분석.md
│   │   ├── Claude_Code_예약작업_Scheduled_Tasks_가이드.md
│   │   ├── Claude_Code_플러그인_MCP_연동_정리.md
│   │   ├── Claude_Cowork_리걸플러그인_특허업무_활용_고찰.md
│   │   ├── claude_code_AskUserQuestion_가이드.md
│   │   ├── OpenClaw_Google_Embedding_설정_가이드.md
│   │   ├── 안그래비티_모바일_AG_연동_가이드.md
│   │   ├── 옵시디언_지식베이스_Claude_Code_연동_가이드.md
│   │   ├── 클로드코드_vs_웹앱_UX_비교조사.md
│   │   └── 플러그인_정리_및_특허업무_활용가이드.md
│   │
│   ├── claude-cowork/               # Claude Cowork 배포/운영 (5개)
│   │   ├── Claude_Cowork_윈도우_배포_가이드.md
│   │   ├── Claude_Cowork_특허업무_프롬프트_가이드.md
│   │   ├── Claude_멀티계정_연동_시나리오_분석.md
│   │   ├── claude-cowork-vm-fix-plan.md
│   │   └── fix_cowork_vhdx_access.ps1
│   │
│   ├── claude-desktop/              # Claude Desktop 트러블슈팅 (8개)
│   │   ├── CLAUDE_DESKTOP_CRASH_FIX_GUIDE.md
│   │   ├── CLAUDE_DESKTOP_크래시_근본해결.md
│   │   ├── claude-desktop-crash-fix-guide.md
│   │   ├── claude-desktop-outage-report-2026-02-10.md
│   │   ├── claude_desktop_guardian.ps1
│   │   ├── claude_desktop_guardian.sh
│   │   ├── fix_claude_desktop_crash.ps1
│   │   └── fix_instant_crash_deepclean.ps1
│   │
│   ├── research/                    # 리서치/분석 문서 (15개)
│   │   ├── AI_GPU_커널_최적화_심층분석.md
│   │   ├── Antigravity_사용량_및_모델_가이드.md
│   │   ├── DeerFlow_분석_바이트댄스_AI에이전트.md
│   │   ├── GPT5.2_이론물리학_글루온진폭_연구정리.md
│   │   ├── Google_Gemini_Workspace_통합_분석.md
│   │   ├── WoW_한밤_PVP_티어리스트.md
│   │   ├── WoW_한밤_확장팩_PvP_가이드.md
│   │   ├── WoW_한밤_힐러_PVP_종합분석.md
│   │   ├── ai-wrapper-strategy.md
│   │   ├── antigravity_connection_test.md
│   │   ├── hanwha-solution-capital-increase.md
│   │   ├── middle-east-conflict-summary.md
│   │   ├── turboquant-explanation.md
│   │   ├── 바이브코딩_도구_총정리_2026.md
│   │   └── 이란전쟁_유가_TACO_시나리오_분석.md
│   │
│   └── personal/                    # 개인 메모 (3개)
│       ├── session-2026-03-15-visualization.md
│       ├── 리나_건강이력_및_관리계획.md
│       └── 한울_촉촉_고구마스틱_보관법_조사.md
│
├── .github/workflows/         # GitHub Actions (AI 뉴스 자동 수집)
├── requirements.txt           # Python 의존성
└── .gitignore
```

---

## 주요 도구

### 1. 특허 문서 변환기 (`patent-tools/`)

Word/HWP 파일을 한국특허청 HLT 형식으로 자동 변환합니다.

**실행 방법:**
- Windows: `patent-tools/scripts/실행.bat` 더블클릭
- Mac/Linux: `python patent-tools/EASY_START.py`

자세한 사용법은 `patent-tools/사용방법.txt` 참고.

### 2. PDF → PPT 변환기 (`tools/pdf-converter/`)

PDF 파일을 편집 가능한 PowerPoint로 변환합니다.

```bash
python tools/pdf-converter/pdf_to_ppt.py your_file.pdf
```

### 3. AI 뉴스 다이제스트 (`tools/ai-news-digest/`)

AI 관련 뉴스를 수집/요약합니다.

사용법은 `tools/ai-news-digest/AI_뉴스_다이제스트_사용방법.txt` 참고.

### 4. 시각화 도구 (`tools/`)

- **복리 계산기**: `tools/compound-interest-visualization.html` - 인터랙티브 복리 계산 시각화
- **그린 정리 시뮬레이터**: `tools/greens_theorem_simulator.html` - 수학 정리 시각화
- **Figma 시각화**: `tools/figma_visualization_sample.html` - 디자인 시각화 샘플

---

## 지식 DB (`docs/`)

이 레포의 `docs/`는 단순 문서 저장소가 아닌 **점진적 실무 지식 DB**입니다.

### 빠른 탐색

→ **[KNOWLEDGE_INDEX.md](docs/KNOWLEDGE_INDEX.md)** — 카테고리·태그별 전체 문서 인덱스 (자동 생성)

### 카테고리

| 카테고리 | 경로 | 설명 |
|----------|------|------|
| Claude Code | `docs/claude-code/` | Claude Code 기능, 플러그인, MCP 연동, UX 비교 등 |
| Claude Cowork | `docs/claude-cowork/` | 윈도우 배포, 특허업무 프롬프트, VM 트러블슈팅 |
| Claude Desktop | `docs/claude-desktop/` | 크래시 해결, 장애 보고서, 복구 스크립트 |
| 리서치 | `docs/research/` | AI/ML, 전략, 금융 분석 |
| 개인 | `docs/personal/` | 개인 메모 |

### 새 지식 문서 추가하기

1. 목적에 맞는 템플릿 복사: `docs/_templates/` (guide / analysis / troubleshoot / insight)
2. YAML frontmatter 작성: `docs/_meta/STANDARDS.md` 참고
3. `docs/<카테고리>/` 에 저장
4. 인덱스는 `master` 푸시 시 자동 갱신 (또는 `python scripts/build_knowledge_index.py` 수동 실행)

---

## 설치

```bash
git clone <repository-url>
cd test1
pip install -r requirements.txt
```

## 라이선스

MIT License
