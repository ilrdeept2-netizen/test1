# 2개 Claude 계정 연동 시나리오 심층 분석

2개의 서로 다른 Claude 계정을 최대한 연동하여 사용할 수 있는 모든 가능한 시나리오를 심층 검토한 문서입니다.

---

## 1. Claude Code CLI — `CLAUDE_CONFIG_DIR` 동시 사용

**가장 실용적인 방법**으로, 별도의 config 디렉토리를 지정하여 2개 계정을 동시에 운용할 수 있습니다.

```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
alias claude-work="CLAUDE_CONFIG_DIR=~/.claude-work claude"
alias claude-personal="CLAUDE_CONFIG_DIR=~/.claude-personal claude"
```

- 각각 별도 터미널 탭에서 실행
- 각 계정의 사용량(rate limit)이 독립적으로 적용
- 별도 이메일의 Anthropic 계정 필요

### 연동 포인트

- `.mcp.json` 파일을 프로젝트 루트에 두면 (`--scope project`) 어떤 계정으로 접속하든 동일한 MCP 서버 구성 공유 가능
- `--scope user` MCP 설정은 config 디렉토리별로 분리되므로 심링크로 연결 가능

### 인증 방법

```bash
# 각 계정을 별도 터미널에서 인증
claude-work    # 터미널 1에서 회사 계정으로 로그인
claude-personal  # 터미널 2에서 개인 계정으로 로그인
```

---

## 2. Claude Desktop — 멀티 인스턴스 운용

### 방법 A: 브라우저 + 데스크톱 병행

- **계정 A** → Claude Desktop 앱
- **계정 B** → 브라우저(claude.ai)

### 방법 B: 서드파티 멀티 인스턴스 도구

[`claude-desktop-multi-instance`](https://github.com/weidwonder/claude-desktop-multi-instance) 활용:

- 각 인스턴스별 독립된 MCP 서버 설정 및 로그인 자격증명
- Dock에 "Claude Work", "Claude Personal" 등 커스텀 이름 표시
- Spotlight 통합 지원
- 독립된 설정 파일로 MCP 서버 구성 분리

---

## 3. API 조직(Organization) + Workspace 기반 연동

2개의 API 계정이 **같은 조직** 아래 있다면 가장 강력한 연동이 가능합니다.

| 기능 | 설명 |
|------|------|
| **Parent Organization 통합** | 여러 조직을 하나의 부모 조직 아래 병합 가능 |
| **SSO 공유** | 부모 조직의 SSO 설정을 하위 조직들이 공유 |
| **Advanced Group Mappings** | IdP 그룹으로 각 조직별 접근 제어 |
| **Admin API** | `sk-ant-admin...` 키로 멤버, 워크스페이스, API 키를 프로그래밍 방식으로 관리 |
| **Workspace 분리** | 프로젝트/환경/팀별 워크스페이스, API 키는 워크스페이스 단위로 스코핑 |

### Workspace 구조 예시

```
Parent Organization
├── Organization A (회사)
│   ├── Workspace: Production
│   ├── Workspace: Development
│   └── Workspace: Research
└── Organization B (개인)
    ├── Workspace: Side Projects
    └── Workspace: Learning
```

### Admin API 활용

```bash
# Admin API로 조직 멤버/워크스페이스/API 키를 프로그래밍 방식으로 관리
# sk-ant-admin... 키 필요 (조직 관리자만 발급 가능)
curl -X GET https://api.anthropic.com/v1/organizations/members \
  -H "x-api-key: sk-ant-admin..."
```

---

## 4. Team/Enterprise 플랜 — 프로젝트 공유

Team 또는 Enterprise 플랜을 사용하면 **프로젝트 단위 협업**이 가능합니다.

### 프로젝트 가시성 옵션

- **Public 프로젝트**: 조직 내 모든 멤버가 조회/사용 가능
- **Private 프로젝트**: 초대된 멤버만 접근

### 권한 레벨

- `Can use`: 프로젝트 내용 조회 + 채팅 가능
- `Can edit`: 프로젝트 지침/지식 수정 + 기여 가능

### 프라이버시

- 각 멤버의 채팅 내역은 프로젝트가 Public이라도 **비공개** 유지
- 수동으로 공유하지 않는 한 다른 멤버가 접근 불가

### 제한 사항

- 개인 Pro/Max 계정과 Team/Enterprise 계정은 **병합 불가** (같은 이메일이라도)
- Team 플랜 최소 5명 필요
- 데이터는 플랜 간 이전 불가

---

## 5. MCP 서버를 통한 간접 연동

2개 계정이 **동일한 외부 도구/데이터에 접근**하도록 MCP 서버를 공유 설정하는 방식입니다.

### 프로젝트 레벨 공유 설정

```json
// .mcp.json (프로젝트 루트 — 두 계정 모두 접근 가능)
{
  "mcpServers": {
    "github-shared": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_..." }
    },
    "database-shared": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": { "DATABASE_URL": "postgresql://..." }
    },
    "slack-shared": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": { "SLACK_BOT_TOKEN": "xoxb-..." }
    }
  }
}
```

### 멀티 인스턴스 MCP 구성

```json
{
  "mcpServers": {
    "github-work": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_work_token..." }
    },
    "github-personal": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_personal_token..." }
    }
  }
}
```

### MCP 설정 공유 방법

- **프로젝트 스코프** (`--scope project`): `.mcp.json`이 리포에 포함되어 누구든 동일 구성 사용
- **유저 스코프** (`--scope user`): config 디렉토리별 분리, 심링크로 연결 가능
- **로컬 스코프** (기본값): 현재 프로젝트 + 현재 사용자만 적용

---

## 6. Claude Connectors (2026년 기준 50+ 통합)

Claude Connectors를 통해 두 계정이 **같은 외부 서비스에 연결**되면 사실상 동일한 데이터 소스를 공유합니다.

### 주요 커넥터 카테고리

| 카테고리 | 예시 서비스 |
|----------|-------------|
| 생산성 | Google Drive, Notion, Obsidian |
| 커뮤니케이션 | Slack, Gmail |
| 엔지니어링 | GitHub, GitLab, Jira |
| 디자인 | Figma |
| 금융 | 각종 금융 플랫폼 |
| 헬스케어 | 건강 데이터 플랫폼 (미국 한정) |
| CRM | Salesforce (Claude Cowork 통합) |

### 특징

- 구독 요금에 포함 (추가 비용 없음)
- 각 사용자의 접근 권한이 원본 서비스 기준으로 적용
- 원클릭 연동
- 2026년 2월 기준 50+ 통합 제공

---

## 7. 계정 전환 (Switch Account/Organization)

claude.ai에서 좌측 하단 프로필 클릭 → **Switch Account** 또는 **Switch Organization**으로 전환 가능

### 현재 상태

- 동시 사용이 아닌 **전환 방식**
- 같은 이메일로 개인 + 조직 계정이 있으면 라우팅 충돌 발생 가능
- 세션별 계정 선택 기능은 아직 요청 단계 ([GitHub Issue #29544](https://github.com/anthropics/claude-code/issues/29544))

### 전환 방법

1. 좌측 하단의 이니셜/이름 클릭
2. "Switch Account" 또는 "Switch Organization" 선택
3. 원하는 계정/조직 선택

---

## 시나리오별 추천 정리

| 사용 목적 | 최적 방법 | 연동 수준 |
|-----------|-----------|-----------|
| **개발자 2명이 같은 코드베이스 작업** | Team 플랜 + 프로젝트 공유 + `.mcp.json` | ★★★★★ |
| **혼자 개인+회사 계정 동시 사용 (CLI)** | `CLAUDE_CONFIG_DIR` 분리 + MCP 심링크 | ★★★★☆ |
| **혼자 개인+회사 계정 동시 사용 (Desktop)** | 멀티 인스턴스 도구 또는 앱+브라우저 병행 | ★★★☆☆ |
| **API 기반 서비스에서 멀티 조직 관리** | Parent Org + Admin API + Workspace 분리 | ★★★★★ |
| **두 계정이 같은 외부 데이터 접근** | 공유 MCP 서버 + Connectors | ★★★★☆ |
| **단순 계정 전환** | claude.ai Switch Account | ★★☆☆☆ |

---

## 주의사항

### 계정 공유 금지
- 1개 개인 계정을 여러 사람이 사용하면 Anthropic TOS 위반
- 다른 IP/브라우저에서 동시 로그인 시 비정상 활동 감지 → 계정 정지 가능

### 계정 병합 불가
- Pro/Max ↔ Team/Enterprise 간 데이터 이전 불가
- 같은 이메일이라도 별도 인스턴스로 취급

### API 키 보안
- 유출 시 해당 워크스페이스의 모든 파일에 대한 읽기/쓰기 접근 가능
- [CVE-2026-21852](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/) 참고
- 환경변수 또는 시크릿 매니저 사용 권장

---

## 참고 자료

- [Manage Multiple Claude Code Accounts (Gist)](https://gist.github.com/KMJ-007/0979814968722051620461ab2aa01bf2)
- [Claude Desktop Multi-Account Feature Request #18435](https://github.com/anthropics/claude-code/issues/18435)
- [Claude Code Multi-Session Feature Request #261](https://github.com/anthropics/claude-code/issues/261)
- [Multi-Account API Selection Feature Request #29544](https://github.com/anthropics/claude-code/issues/29544)
- [Account Migration — Claude Help Center](https://support.claude.com/en/articles/9267400-can-individuals-with-pro-or-max-plan-accounts-migrate-them-to-team-or-enterprise-plan-organizations)
- [Claude Workspaces — API Docs](https://platform.claude.com/docs/en/build-with-claude/workspaces)
- [Project Visibility and Sharing — Claude Help Center](https://support.claude.com/en/articles/9519189-project-visibility-and-sharing)
- [Claude Connectors Guide 2026](https://max-productive.ai/blog/claude-ai-connectors-guide-2025/)
- [Claude MCP Server Setup — Claude Code Docs](https://code.claude.com/docs/en/mcp)
- [Claude Desktop Multi-Instance Tool](https://github.com/weidwonder/claude-desktop-multi-instance)
- [SSO Setup — Claude Console](https://support.anthropic.com/en/articles/10280258-setting-up-single-sign-on-on-the-api-console)
- [Admin API Overview — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/administration-api)
