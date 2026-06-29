#!/usr/bin/env python3
"""
지식 인덱스 빌더
docs/ 하위의 모든 마크다운 파일을 스캔하여 YAML frontmatter를 읽고
docs/KNOWLEDGE_INDEX.md를 자동 생성합니다.

사용법:
    python scripts/build_knowledge_index.py

또는 docs/ 변경 시 GitHub Actions가 자동 실행합니다.
"""

import os
import re
from datetime import date
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR = REPO_ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "KNOWLEDGE_INDEX.md"

# 인덱스에서 제외할 경로
EXCLUDE_DIRS = {"_templates", "_meta"}
EXCLUDE_FILES = {"KNOWLEDGE_INDEX.md"}


def parse_frontmatter(content: str) -> dict:
    """YAML frontmatter 파싱 (외부 라이브러리 없이)"""
    if not content.startswith("---"):
        return {}

    end = content.find("\n---", 3)
    if end == -1:
        return {}

    frontmatter_text = content[3:end].strip()
    meta = {}

    for line in frontmatter_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # tags: [a, b, c] 형식
        if line.startswith("tags:"):
            value = line[5:].strip()
            if value.startswith("[") and value.endswith("]"):
                tags = [t.strip().strip('"').strip("'") for t in value[1:-1].split(",")]
                meta["tags"] = [t for t in tags if t]
            continue

        # related: 리스트 형식 (다음 줄에 - item)
        if line == "related:":
            meta["related"] = []
            continue

        if line.startswith("- ") and "related" in meta and isinstance(meta.get("related"), list):
            meta["related"].append(line[2:].strip())
            continue

        # key: value 형식
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip().strip('"').strip("'")
            meta[key.strip()] = value

    return meta


def collect_docs() -> list[dict]:
    """docs/ 하위 모든 마크다운 파일 수집"""
    docs = []

    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        # 제외 경로 필터
        rel = md_file.relative_to(DOCS_DIR)
        parts = rel.parts

        if parts[0] in EXCLUDE_DIRS:
            continue
        if md_file.name in EXCLUDE_FILES:
            continue

        content = md_file.read_text(encoding="utf-8", errors="ignore")
        meta = parse_frontmatter(content)

        # frontmatter 없으면 기본값으로 포함
        if not meta:
            meta = {
                "title": md_file.stem.replace("_", " ").replace("-", " "),
                "status": "draft",
                "tags": [],
                "summary": "(메타데이터 없음 — frontmatter 추가 필요)",
            }
            meta["_missing_frontmatter"] = True

        meta["_path"] = str(rel)
        meta["_file"] = md_file

        # category가 없으면 폴더 이름에서 추론
        if "category" not in meta:
            meta["category"] = parts[0] if len(parts) > 1 else "uncategorized"

        # tags가 없으면 빈 리스트
        if "tags" not in meta or not isinstance(meta.get("tags"), list):
            meta["tags"] = []

        docs.append(meta)

    return docs


def render_index(docs: list[dict]) -> str:
    """KNOWLEDGE_INDEX.md 렌더링"""
    today = date.today().isoformat()

    # 카테고리별 그룹핑
    by_category = defaultdict(list)
    for doc in docs:
        cat = doc.get("category", "uncategorized")
        by_category[cat].append(doc)

    # 태그별 그룹핑
    by_tag = defaultdict(list)
    for doc in docs:
        for tag in doc.get("tags", []):
            by_tag[tag].append(doc)

    # frontmatter 없는 파일 목록
    missing = [d for d in docs if d.get("_missing_frontmatter")]

    lines = [
        f"# 지식 인덱스",
        f"",
        f"> 자동 생성 — `python scripts/build_knowledge_index.py` | 마지막 갱신: {today}",
        f"",
        f"**총 {len(docs)}개 문서** | 카테고리 {len(by_category)}개 | 태그 {len(by_tag)}개",
        f"",
    ]

    if missing:
        lines += [
            f"---",
            f"",
            f"## ⚠️ Frontmatter 미추가 문서 ({len(missing)}개)",
            f"",
            f"> 아래 문서에 [메타데이터 표준](docs/_meta/STANDARDS.md)에 따라 frontmatter를 추가해 주세요.",
            f"",
        ]
        for doc in missing:
            lines.append(f"- `{doc['_path']}`")
        lines.append("")

    lines += [
        f"---",
        f"",
        f"## 카테고리별 문서",
        f"",
    ]

    # 카테고리 순서 (중요도순)
    cat_order = [
        "claude-code", "claude-cowork", "claude-desktop",
        "patent", "howto", "troubleshoot",
        "ai-research", "strategy",
        "personal", "meta", "uncategorized"
    ]
    sorted_cats = sorted(by_category.keys(), key=lambda c: (cat_order.index(c) if c in cat_order else 99, c))

    cat_labels = {
        "claude-code": "Claude Code",
        "claude-cowork": "Claude Cowork",
        "claude-desktop": "Claude Desktop",
        "patent": "특허 실무",
        "howto": "How-To 가이드",
        "troubleshoot": "문제 해결",
        "ai-research": "AI/ML 리서치",
        "strategy": "전략/비즈니스",
        "personal": "개인 메모",
        "meta": "레포 메타",
        "uncategorized": "미분류",
    }

    for cat in sorted_cats:
        cat_docs = sorted(by_category[cat], key=lambda d: d.get("date", "0000"), reverse=True)
        label = cat_labels.get(cat, cat)
        lines += [
            f"### {label} ({len(cat_docs)})",
            f"",
        ]

        for doc in cat_docs:
            path = doc["_path"]
            title = doc.get("title", path)
            summary = doc.get("summary", "")
            status = doc.get("status", "")
            tags = doc.get("tags", [])
            updated = doc.get("updated", doc.get("date", ""))

            status_badge = {"draft": "🔵", "active": "🟢", "archived": "⚫"}.get(status, "⚪")
            tag_str = " ".join(f"`{t}`" for t in tags[:4])
            date_str = f" · {updated}" if updated else ""

            lines.append(f"- {status_badge} [{title}](docs/{path}){date_str}")
            if summary and not doc.get("_missing_frontmatter"):
                lines.append(f"  > {summary}")
            if tag_str:
                lines.append(f"  > {tag_str}")
            lines.append("")

    lines += [
        f"---",
        f"",
        f"## 태그 인덱스",
        f"",
    ]

    # 빈도순 태그 정렬
    sorted_tags = sorted(by_tag.items(), key=lambda kv: -len(kv[1]))
    for tag, tag_docs in sorted_tags:
        doc_links = ", ".join(
            f"[{d.get('title', d['_path'])}](docs/{d['_path']})"
            for d in tag_docs[:5]
        )
        suffix = f" …외 {len(tag_docs)-5}개" if len(tag_docs) > 5 else ""
        lines.append(f"- **`{tag}`** ({len(tag_docs)}) — {doc_links}{suffix}")

    lines += [
        f"",
        f"---",
        f"",
        f"## 범례",
        f"",
        f"| 아이콘 | 상태 | 의미 |",
        f"|--------|------|------|",
        f"| 🟢 | active | 현재 유효한 지식 |",
        f"| 🔵 | draft | 작성 중 / 검증 전 |",
        f"| ⚫ | archived | 더 이상 유효하지 않음 |",
        f"| ⚪ | (미지정) | frontmatter 없음 |",
        f"",
        f"---",
        f"",
        f"*[STANDARDS.md](docs/_meta/STANDARDS.md) · [새 문서 템플릿](docs/_templates/)*",
    ]

    return "\n".join(lines) + "\n"


def main():
    print(f"docs/ 스캔 중: {DOCS_DIR}")
    docs = collect_docs()
    print(f"  → {len(docs)}개 마크다운 파일 발견")

    missing = [d for d in docs if d.get("_missing_frontmatter")]
    if missing:
        print(f"  ⚠️  frontmatter 없음: {len(missing)}개")
        for d in missing:
            print(f"     - {d['_path']}")

    index_content = render_index(docs)
    OUTPUT_FILE.write_text(index_content, encoding="utf-8")
    print(f"\n✓ 인덱스 생성 완료: {OUTPUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
