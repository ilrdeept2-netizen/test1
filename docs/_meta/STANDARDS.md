---
title: "지식 DB 메타데이터 표준"
date: 2026-04-09
category: meta
tags: [meta, standards, knowledge-db]
status: active
summary: "이 레포에서 모든 지식 문서에 적용하는 YAML frontmatter 규칙"
---

# 지식 DB 메타데이터 표준

이 레포의 모든 `docs/` 문서는 **YAML frontmatter**를 포함해야 합니다.
표준화된 메타데이터가 있어야 자동 인덱싱, 태그 검색, 연관 문서 추천이 가능합니다.

---

## Frontmatter 필드 명세

```yaml
---
title: "문서 제목 (명확한 설명형)"
date: YYYY-MM-DD          # 최초 작성일 (필수)
updated: YYYY-MM-DD       # 최종 수정일 (선택, 수정 시 갱신)
category: <카테고리>      # 아래 카테고리 목록 참고 (필수)
tags: [tag1, tag2]        # 아래 태그 목록에서 선택 (필수, 1개 이상)
status: <상태>            # draft | active | archived (필수)
summary: "한 줄 요약"     # 50자 이내, 검색 스니펫으로 사용 (필수)
related:                  # 연관 문서 (선택)
  - docs/path/to/doc.md
source: "출처 URL 또는 저자"  # 외부 출처가 있을 때만 (선택)
---
```

---

## 카테고리 목록

| 카테고리 | 설명 | 해당 폴더 |
|---------|------|---------|
| `claude-code` | Claude Code 사용법, 팁, 아키텍처 | `docs/claude-code/` |
| `claude-cowork` | Claude Cowork 배포/운영 | `docs/claude-cowork/` |
| `claude-desktop` | Claude Desktop 설정/트러블슈팅 | `docs/claude-desktop/` |
| `patent` | 특허 업무 실무 노하우 | `docs/research/`, `patent-tools/` |
| `ai-research` | AI/ML 기술 분석, 모델 리뷰 | `docs/research/` |
| `strategy` | 비즈니스/기술 전략 분석 | `docs/research/` |
| `howto` | 실행 가능한 절차/가이드 | 어디서나 |
| `troubleshoot` | 문제-원인-해결 패턴 | `docs/claude-desktop/` 등 |
| `personal` | 개인 메모, 비업무 자료 | `docs/personal/` |
| `meta` | 이 레포 자체에 대한 문서 | `docs/_meta/` |

---

## 태그 풀 (권장 태그 목록)

**Claude 생태계**
- `claude`, `claude-code`, `claude-cowork`, `claude-desktop`
- `mcp`, `mcp-server`, `agent`, `multi-agent`
- `prompt`, `prompt-engineering`, `context-window`

**도구/인프라**
- `python`, `flask`, `streamlit`, `github-actions`
- `windows`, `linux`, `docker`, `npm`
- `workflow`, `automation`, `script`

**특허/법률**
- `patent`, `kipo`, `hlt`, `korean-law`
- `patent-claim`, `prior-art`, `oa-response`

**AI/ML 기술**
- `llm`, `gpu`, `fine-tuning`, `embedding`
- `rag`, `vector-db`, `inference`
- `openai`, `anthropic`, `google-ai`, `meta-ai`

**비즈니스/전략**
- `strategy`, `finance`, `startup`, `ai-wrapper`
- `geopolitics`, `market-analysis`

**상태/타입**
- `setup`, `troubleshoot`, `fix`, `workaround`
- `analysis`, `guide`, `reference`, `insight`

---

## 상태(status) 의미

| 상태 | 의미 |
|------|------|
| `draft` | 작성 중, 검증 전 |
| `active` | 현재 유효한 지식 |
| `archived` | 더 이상 유효하지 않음 (구버전, 서비스 종료 등) |

---

## 작성 원칙

1. **제목은 행동/결과 중심으로**: "Claude Code 아키텍처 분석" → "Claude Code가 비용을 줄이는 4단계 압축 원리"처럼 핵심이 제목에 드러나야 함
2. **summary는 검색 스니펫**: 누군가 이 문서를 찾을 때 보게 될 한 줄. 키워드 포함 필수
3. **related는 양방향**: A → B를 연결하면 B에도 A를 related로 추가
4. **tags는 3~7개**: 너무 적으면 검색 안 됨, 너무 많으면 의미 없음
5. **archived 처리**: 삭제하지 말고 status를 archived로 변경 → 히스토리 보존

---

## 인덱스 자동 갱신

`scripts/build_knowledge_index.py`를 실행하면 `docs/KNOWLEDGE_INDEX.md`가 자동 생성됩니다.

```bash
python scripts/build_knowledge_index.py
```

GitHub Actions (`knowledge_index.yml`)가 `docs/` 변경 시 자동으로 인덱스를 갱신합니다.
