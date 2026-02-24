# 이 계정에서 실제 가동 중인 플러그인 & MCP 연동 현황

> 작성일: 2026-02-24
> 기준: `~/.claude/` 실제 설정 파일 직접 조회 결과

---

## 실제 구성 현황 요약

| 항목 | 상태 |
|------|------|
| MCP 서버 | **없음** (미설정) |
| 활성 Skills | **1개** (`session-start-hook`) |
| 활성 Hooks | **1개** (`Stop` 이벤트 → Git 체크) |
| 차단된 플러그인 | **2개** (blocklist에 등록됨) |
| 허용된 도구 | **Skill** 도구만 명시적 허용 |

---

## 1. MCP 서버

```
없음
```

`~/.claude/settings.json`에 `mcpServers` 설정이 없음. 현재 이 세션에서 MCP로 연결된 외부 서버는 0개.

---

## 2. 활성 Skills (실제 로드됨)

### `session-start-hook` (startup-hook-skill)

- **파일**: `~/.claude/skills/session-start-hook/SKILL.md`
- **트리거**: `/session-start-hook` 또는 해당 상황에 맞는 요청 시

**기능:**
- 프로젝트 레포지토리에 `SessionStart` 훅을 생성·등록
- 세션 시작 시 자동으로 의존성 설치 (`npm install`, `pip install` 등)
- 린터/테스트 실행 환경 자동 구성

**지원하는 패키지 매니저:**
- `package.json` / `package-lock.json` → npm
- `pyproject.toml` / `requirements.txt` → pip/Poetry
- `Cargo.toml` → cargo
- `go.mod` → go
- `Gemfile` → bundler

**생성 결과물:**
```
.claude/hooks/session-start.sh  ← 설치 스크립트
.claude/settings.json           ← SessionStart 훅 등록
```

---

## 3. 활성 Hooks (자동 실행 중)

### `Stop` 이벤트 훅 — Git 상태 체크

- **파일**: `~/.claude/stop-hook-git-check.sh`
- **이벤트**: Claude가 작업을 **완료(Stop)할 때마다** 자동 실행
- **설정**: `~/.claude/settings.json` → `hooks.Stop`

**동작:**
1. Git 리포지토리인지 확인
2. 미커밋(staged/unstaged) 변경사항 있으면 → **오류 반환** (exit 2)
3. 추적되지 않는 파일 있으면 → **오류 반환** (exit 2)
4. 원격 브랜치 대비 미푸시 커밋 있으면 → **오류 반환** (exit 2)

**효과**: 내가 작업을 마칠 때 커밋·푸시가 완료되지 않으면 자동으로 경고.

---

## 4. 차단된 플러그인 (Blocklist)

`~/.claude/plugins/blocklist.json`에 등록된 플러그인 — **사용 불가** 상태.

| 플러그인 ID | 차단 이유 | 차단 일시 |
|------------|----------|----------|
| `code-review@claude-plugins-official` | 테스트 목적 (`just-a-test`) | 2026-02-11 |
| `fizz@testmkt-marketplace` | 보안 이슈 (`security`) | 2026-02-12 |

---

## 5. 현재 `settings.json` 전체 내용

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/stop-hook-git-check.sh"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": ["Skill"]
  }
}
```

**주요 포인트:**
- `Skill` 도구만 명시적으로 허용됨
- MCP 서버 설정 없음
- Agent Teams 실험 기능 비활성화 상태

---

## 결론

이 계정에서 지금 실제로 작동 중인 것:

1. **Stop 훅** — 모든 작업 완료 시 Git 커밋/푸시 여부 자동 검사
2. **session-start-hook Skill** — 요청 시 SessionStart 훅 생성 가능

연결된 MCP 없음, 차단된 플러그인 2개, Agent Teams 미활성화.
