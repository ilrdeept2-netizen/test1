# Claude Code 웹앱 플러그인 & MCP 연동 정리

> 작성일: 2026-02-24
> 기준: Claude Code v2.1.34 / Claude Cowork Research Preview

---

## 목차

1. [MCP (Model Context Protocol) 연동](#1-mcp-model-context-protocol-연동)
2. [Skills 시스템 (플러그인)](#2-skills-시스템-플러그인)
3. [외부 서비스 커넥터](#3-외부-서비스-커넥터)
4. [Agent Teams (에이전트 팀)](#4-agent-teams-에이전트-팀)
5. [서브에이전트 시스템](#5-서브에이전트-시스템)
6. [설정 파일 기반 확장](#6-설정-파일-기반-확장)
7. [플랫폼별 가용 기능 요약](#7-플랫폼별-가용-기능-요약)

---

## 1. MCP (Model Context Protocol) 연동

MCP는 Claude Code에서 외부 서버·도구·데이터 소스를 연결하는 표준 프로토콜이다.

### 개요

- CLAUDE.md, 커스텀 훅과 함께 Claude Code의 **깊은 커스터마이징** 수단으로 활용
- 외부 API, 데이터베이스, 자체 서버를 Claude의 컨텍스트로 주입 가능
- 생태계/확장성 측면에서 Claude Code를 Claude.ai 웹앱보다 높게 평가받는 핵심 요소

### 설정 위치

```
~/.claude/settings.json
```

### 활용 예시

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/path/to/mcp-server.js"]
    }
  }
}
```

### 주요 MCP 연동 유형

| 유형 | 설명 | 예시 |
|------|------|------|
| **파일시스템** | 로컬 파일/디렉토리 접근 확장 | 특정 경로 권한 부여 |
| **데이터베이스** | DB 쿼리 및 조작 | PostgreSQL, SQLite 연동 |
| **외부 API** | 3rd-party 서비스 호출 | GitHub, Jira, Slack API |
| **커스텀 서버** | 자체 구축 도구 서버 | 내부 시스템 연동 |

---

## 2. Skills 시스템 (플러그인)

Claude Cowork(데스크톱 에이전트)에서 제공하는 **플러그인형 역량 확장 시스템**이다.

### 주요 Skills

| Skill | 기능 | 산출물 |
|-------|------|--------|
| **Excel 생성** | 수식·서식이 포함된 스프레드시트 생성 | `.xlsx` 파일 |
| **PowerPoint 생성** | 포맷이 갖춰진 프레젠테이션 제작 | `.pptx` 파일 |
| **문서 생성** | 구조화된 비즈니스 문서 작성 | Word/PDF 등 |
| **데이터 분석** | CSV/Excel 데이터 분석 및 인사이트 도출 | 보고서 |

### 동작 방식

```
사용자 요청
    ↓
Skill 선택 (자동)
    ↓
서브에이전트 병렬 실행
    ↓
최종 파일 생성 → 지정 폴더에 저장
```

---

## 3. 외부 서비스 커넥터

Claude Cowork에서 외부 SaaS 서비스와 직접 연동할 수 있는 **커넥터** 기능이다.

### 현재 지원 커넥터

| 서비스 | 기능 | 비고 |
|--------|------|------|
| **Asana** | 태스크 읽기/생성/업데이트 | 프로젝트 관리 자동화 |
| **Notion** | 페이지 읽기/쓰기, 데이터베이스 조작 | 문서·지식 관리 |

### 향후 추가 예정

- 2026년 상반기 내 **추가 커넥터 확대** 계획 (Anthropic 공식 확인)
- Slack, Google Workspace, Microsoft 365 등 협업 도구 연동 예상

### 커넥터 설정 방법

Claude Desktop 앱 → 설정 → 커넥터 → 원하는 서비스 인증 후 활성화

---

## 4. Agent Teams (에이전트 팀)

Claude Code의 **실험적 기능**으로, 리드 에이전트가 여러 팀원 에이전트를 생성해 병렬 작업한다.

### 활성화

```json
// ~/.claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### 표시 모드

| 모드 | 설명 | 요구사항 |
|------|------|----------|
| **in-process** | 단일 터미널에서 팀원 전환 | 별도 설치 불필요 |
| **split panes** | 각 팀원이 별도 패널 | tmux 또는 iTerm2 필요 |

```json
{ "teammateMode": "in-process" }
```

### 조작 단축키

| 동작 | 단축키 |
|------|--------|
| 팀원 선택 | `Shift+Up/Down` |
| 팀원 세션 진입/나가기 | `Enter` / `Escape` |
| 작업 목록 보기 | `Ctrl+T` |
| 위임 모드 (리드만 조율) | `Shift+Tab` |

### 서브에이전트 vs 에이전트 팀 비교

| 항목 | 서브에이전트 | 에이전트 팀 |
|------|-------------|------------|
| 컨텍스트 | 결과만 메인에 반환 | 완전히 독립 |
| 팀원 간 소통 | 메인에만 보고 | 팀원끼리 직접 대화 |
| 조율 방식 | 메인이 모든 작업 관리 | 공유 작업 목록으로 자율 조율 |
| 적합한 작업 | 결과 중심 집중 작업 | 토론·협업이 필요한 복잡한 작업 |
| 토큰 비용 | 낮음 | 높음 (팀원마다 별도 컨텍스트) |

### 주의사항

- **실험적 기능**: 세션 복구, 종료 등 일부 제한 존재
- **파일 충돌**: 동일 파일을 여러 팀원이 수정하면 덮어쓰기 위험
- **중첩 팀 불가**: 팀원이 자체 팀 생성 불가
- **세션당 1팀**: 새 팀 시작 전 기존 팀 정리 필요

---

## 5. 서브에이전트 시스템

Claude Cowork의 핵심 아키텍처로, 복잡한 작업을 자동으로 분해·병렬 실행한다.

### 태스크 처리 흐름

```
사용자 요청
    ↓
① 목표 분석 (의도 파악, 범위 결정)
    ↓
② 계획 수립 (DAG 방향 비순환 그래프 형태로 서브태스크 분해)
    ↓
③ 서브에이전트 생성 (Spawn)
    ↓
④ 병렬 실행 (각 에이전트 독립 동시 실행)
    ↓
⑤ 결과 집계 (메인 컨텍스트로 통합)
    ↓
⑥ 최종 전달 (완성 산출물)
```

### 서브에이전트 구성요소

| 구성요소 | 설명 |
|----------|------|
| 컨텍스트 윈도우 | 독자적인 컨텍스트에서 작동 |
| 시스템 프롬프트 | 태스크 특화 커스텀 시스템 프롬프트 |
| 도구 접근 | 필요한 도구에만 선택적 접근 |
| 영구 메모리 | 대화를 넘어 유지되는 메모리 디렉토리 |

### 상태 관리 (UNIX 철학)

- 프로젝트 상태를 **로컬 파일시스템**에 저장: `~/.claude/tasks`
- `/clear`, `/compact`로 컨텍스트를 비워도 로드맵은 디스크에 유지
- "공격적 컨텍스트 관리"가 가능한 구조

---

## 6. 설정 파일 기반 확장

### 주요 설정 경로

| 경로 | 용도 |
|------|------|
| `~/.claude/settings.json` | 전역 설정 (MCP, 실험 기능, 팀 모드 등) |
| `~/.claude/tasks` | 프로젝트 상태 및 태스크 저장 |
| `CLAUDE.md` (프로젝트 루트) | 프로젝트별 영구 컨텍스트 제공 |

### CLAUDE.md 활용

- 프로젝트별로 Claude에게 전달할 고정 컨텍스트 정의
- 세션 간 일관된 행동·스타일·규칙 유지
- 팀 공유 시 모든 팀원이 동일한 컨텍스트로 작업 가능

### 커스텀 훅

Claude Code의 특정 이벤트(파일 저장, 커밋, 테스트 등)에 반응하는 사용자 정의 스크립트 연결

```json
// ~/.claude/settings.json 예시
{
  "hooks": {
    "onFileSave": "npm run lint",
    "onCommit": "npm test"
  }
}
```

### CI/CD 파이프라인 통합

- **GitHub Actions** 연동으로 PR 자동 리뷰, 코드 생성 자동화 가능
- 자율 루프 실행으로 야간 빌드·배포("설정 후 방치") 구현

---

## 7. 플랫폼별 가용 기능 요약

| 기능 | Claude Code (CLI) | Claude.ai 웹앱 | Claude Cowork (Desktop) |
|------|:-----------------:|:--------------:|:-----------------------:|
| **MCP 연동** | ✅ | ❌ | ✅ |
| **Skills 시스템** | ❌ | ❌ | ✅ |
| **Asana 커넥터** | ❌ | ❌ | ✅ |
| **Notion 커넥터** | ❌ | ❌ | ✅ |
| **Agent Teams** | ✅ (실험적) | ❌ | ✅ |
| **서브에이전트** | ✅ | ❌ | ✅ |
| **커스텀 훅** | ✅ | ❌ | ❌ |
| **CLAUDE.md** | ✅ | ❌ | 제한적 |
| **CI/CD 통합** | ✅ | ❌ | ❌ |
| **Artifacts 프리뷰** | ❌ | ✅ | ❌ |
| **로컬 파일 직접 접근** | ✅ | ❌ | ✅ |

### 플랫폼 선택 가이드

```
개발 자동화·CI/CD·MCP 커스텀 연동 → Claude Code (CLI)
문서 작성·데이터 분석·PPT 생성·비코딩 업무 → Claude Cowork (Desktop)
빠른 질의응답·비개발자 범용 작업 → Claude.ai 웹앱
```

---

## 참고 링크

- [Claude Code 공식 문서](https://docs.anthropic.com/claude-code)
- [Agent Teams 가이드](https://code.claude.com/docs/en/agent-teams)
- [Claude Cowork 공식 블로그](https://claude.com/blog/cowork-research-preview)
- [MCP 프로토콜 사양](https://modelcontextprotocol.io)
- [Claude Help Center: Cowork 시작 가이드](https://support.claude.com/en/articles/13345190-getting-started-with-cowork)

---

*이 문서는 2026-02-24 기준으로 작성되었습니다. Research Preview 단계의 기능은 변경될 수 있습니다.*
