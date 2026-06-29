# CLAUDE.md — 이 레포 작업 시 항상 적용할 지침

## 📌 사용자 표준 관점 (STANDING INSTRUCTION)

사용자가 **스레드(주로), 유튜브, 웹 주소** 등을 공유할 때, 목적은 단순 내용 파악이 **아니다**.
항상 다음 관점으로 분석/정리할 것:

> **"이 내용의 핵심을, 내 웹앱 또는 로컬(Codex·Claude Code) 환경에 도입해서 실제로 활용 가능한가?"**

따라서 모든 리소스(스레드/영상/링크)를 처리할 때 반드시 아래를 포함한다:

1. **핵심 내용** — 무엇인지
2. **원본 출처 URL** — 추적 가능하게 보존
3. **도입 가능성 판정** — ✅도입가능 / 🔶부분·조건부 / ❌해당없음(단순정보)
4. **도입 대상** — 웹앱 / 로컬(Codex·Claude Code) / 둘다 / 해당없음
5. **구체적 액션** — 도입한다면 무엇을, 어떻게 (또는 제외 사유)

> 즉, "재미있는 정보"로 끝내지 말고 **"내 작업 환경에 흡수 가능한 기술/패턴/도구인지"** 를 항상 함께 판정한다.

## 📂 지식 DB 운용 규칙

- 이 레포의 `docs/`는 단순 저장소가 아니라 **점진적 실무 지식 DB**다.
- 새 리소스 정리 시: `docs/_templates/` 템플릿 사용 → frontmatter 작성(`docs/_meta/STANDARDS.md`) → 적절한 카테고리에 저장.
- 인덱스: `python scripts/build_knowledge_index.py` 로 갱신 (또는 master 푸시 시 자동).
- 도입 가능성 전수 평가는 `docs/_meta/리소스_활용가능성_평가.md` 에 누적·갱신한다.

## 🗂️ 카테고리

| 카테고리 | 경로 |
|----------|------|
| Claude Code | `docs/claude-code/` |
| Claude Cowork | `docs/claude-cowork/` |
| Claude Desktop | `docs/claude-desktop/` |
| 리서치 | `docs/research/` |
| 개인 | `docs/personal/` |
