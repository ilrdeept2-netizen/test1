# test1 - 업무 도구 및 문서 모음

특허 업무 도구, PDF 변환기, AI 뉴스 다이제스트, Claude 관련 가이드 등을 포함하는 레포지토리입니다.

---

## 프로젝트 구조

```
.
├── patent-tools/          # 특허 문서 변환기 & 선행특허 검색
│   ├── app.py                   # Flask 웹 앱
│   ├── patent_format_converter.py  # Word/HWP → HLT 변환 엔진
│   ├── patent_search_app.py     # 선행특허 검색 CLI
│   ├── patent_search_web.py     # 선행특허 검색 웹 UI
│   ├── EASY_START.py            # 간편 실행 스크립트
│   ├── scripts/                 # 실행 스크립트 (bat/sh)
│   ├── templates/               # 웹 UI 템플릿
│   └── tests/                   # 테스트 코드 및 샘플 파일
│
├── tools/                 # 기타 도구 & 시각화
│   ├── pdf-converter/           # PDF → PPT 변환기
│   ├── ai-news-digest/          # AI 뉴스 다이제스트
│   ├── compound-interest-visualization.html  # 복리 시각화
│   ├── figma_visualization_sample.html
│   ├── greens_theorem_simulator.html
│   └── example.py
│
├── docs/                  # 문서
│   ├── claude-code/             # Claude Code 가이드
│   ├── claude-cowork/           # Claude Cowork 배포/운영
│   ├── claude-desktop/          # Claude Desktop 트러블슈팅
│   ├── research/                # 리서치/분석 문서
│   ├── strategy/                # 전략/방향 문서
│   ├── guides/                  # 설정/연동 가이드
│   └── personal/                # 개인 메모
│
├── .github/workflows/     # GitHub Actions
├── requirements.txt       # Python 의존성
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

---

## 설치

```bash
git clone <repository-url>
cd test1
pip install -r requirements.txt
```

## 라이선스

MIT License
