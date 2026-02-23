# Claude Code AskUserQuestion 완전 가이드

> Claude Code가 작업 중 사용자에게 직접 질문을 던져 요구사항을 명확히 하는 기능

## 목차

1. [AskUserQuestion이란?](#askuserquestion이란)
2. [왜 필요한가?](#왜-필요한가)
3. [동작 원리](#동작-원리)
4. [UI 구성 요소 상세](#ui-구성-요소-상세)
5. [실제 사용 시나리오](#실제-사용-시나리오)
6. [Agent SDK에서의 활용](#agent-sdk에서의-활용)
7. [팁과 주의사항](#팁과-주의사항)
8. [참고 자료](#참고-자료)

---

## AskUserQuestion이란?

AskUserQuestion은 Claude Code(CLI, VS Code 확장, Agent SDK)에 내장된 도구로, **Claude가 작업 도중 사용자에게 구조화된 질문을 던질 수 있게** 해주는 기능입니다.

일반적인 AI 코딩 도구는 모호한 요구사항을 받으면 **추측해서 진행**합니다. 그 결과 원하지 않는 방향으로 코드가 작성되어 재작업이 필요해지는 경우가 많습니다.

AskUserQuestion은 이 문제를 근본적으로 해결합니다:

```
기존 방식:  모호한 요청 → 추측 → 구현 → 수정 → 수정 → 수정...
개선된 방식: 모호한 요청 → 질문 → 명확한 답변 → 정확한 구현
```

Claude Code v2.0.21부터 도입되었으며, **Plan Mode와 함께 사용할 때 가장 효과적**입니다.

---

## 왜 필요한가?

### 기획의 중요성

소프트웨어 개발에서 **기획이 전체 프로젝트의 성패를 좌우**합니다. AskUserQuestion은 Claude가 마치 숙련된 기획자처럼 행동하여:

- 요구사항의 빈틈을 사전에 발견
- 다양한 구현 방식 중 최적안을 사용자와 함께 선택
- 설계 단계에서 놓치기 쉬운 엣지 케이스를 질문으로 도출

### 실제 효과

| 구분 | AskUserQuestion 미사용 | AskUserQuestion 사용 |
|------|----------------------|---------------------|
| 재작업 빈도 | 높음 (추측 기반 구현) | 낮음 (확인 후 구현) |
| 토큰 사용량 | 많음 (되돌아가며 수정) | 적음 (한 번에 정확히) |
| 사용자 만족도 | 결과물이 기대와 다름 | 의도에 맞는 결과물 |
| 작업 시간 | 길어짐 (반복 수정) | 단축됨 (선행 확인) |

---

## 동작 원리

### 실행 흐름

```
1. 사용자가 작업 요청
       ↓
2. Claude가 코드베이스를 분석
       ↓
3. 모호하거나 선택이 필요한 지점 발견
       ↓
4. AskUserQuestion 호출 → 실행 일시 중단
       ↓
5. 사용자에게 구조화된 질문 표시
       ↓
6. 사용자가 선택지 중 하나를 선택 (또는 직접 입력)
       ↓
7. Claude가 답변을 받고 작업 재개
       ↓
8. 명확해진 요구사항에 따라 구현
```

### 핵심 특징

- **자동 분석 기반**: Claude가 코드베이스를 분석하고 문맥에 맞는 선택지를 자동 생성
- **구조화된 인터페이스**: 자유 텍스트가 아닌 선택형 UI로 빠르고 정확한 응답 가능
- **실행 일시 중단**: 질문이 나오면 실행이 멈추고, 답변을 받아야 진행
- **1~4개 질문**: 한 번에 최대 4개의 질문을 동시에 표시 가능

---

## UI 구성 요소 상세

### 질문(Question) 구조

각 질문은 다음 필드로 구성됩니다:

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `question` | string | 질문 전문 | "어떤 인증 방식을 사용할까요?" |
| `header` | string | 짧은 레이블 (최대 12자) | "인증 방식" |
| `options` | array | 2~4개의 선택지 | 아래 참조 |
| `multiSelect` | boolean | 복수 선택 허용 여부 | false |

### 선택지(Option) 구조

각 선택지는 다음 필드를 가집니다:

| 필드 | 타입 | 설명 |
|------|------|------|
| `label` | string | 선택지 표시 텍스트 (1~5단어) |
| `description` | string | 선택지에 대한 부연 설명 |
| `markdown` | string (선택) | 미리보기 콘텐츠 (코드, ASCII 목업 등) |

### UI 렌더링 방식

#### 일반 질문 (미리보기 없음)

```
┌─────────────────────────────────────────────┐
│  [인증 방식]                                  │
│                                              │
│  어떤 인증 방식을 사용할까요?                    │
│                                              │
│  ○ JWT (Recommended)                         │
│    stateless 토큰 기반 인증                    │
│                                              │
│  ○ 세션 기반                                  │
│    서버 세션을 이용한 전통적 인증                 │
│                                              │
│  ○ OAuth 2.0                                 │
│    소셜 로그인 연동 가능                        │
│                                              │
│  ○ Other...                                  │
│    (직접 입력)                                 │
└─────────────────────────────────────────────┘
```

- 단일 선택: 라디오 버튼 (○) 형태
- 복수 선택 (`multiSelect: true`): 체크박스 (☐) 형태

#### 미리보기(Preview) 모드

선택지에 `markdown` 필드가 있으면, 좌우 분할 레이아웃으로 전환됩니다:

```
┌──────────────────┬──────────────────────────┐
│  선택지 목록       │  미리보기 패널             │
│                   │                          │
│  ▶ 방식 A         │  ┌────────────────────┐  │
│    방식 B         │  │ // 방식 A 코드 예시   │  │
│    방식 C         │  │ const auth = jwt()  │  │
│                   │  │ app.use(auth)       │  │
│                   │  └────────────────────┘  │
└──────────────────┴──────────────────────────┘
```

이 기능은 **코드 스니펫, ASCII UI 목업, 다이어그램, 설정 예시** 등을 비교할 때 유용합니다.

> 참고: 미리보기는 단일 선택(`multiSelect: false`) 질문에서만 지원됩니다.

### "Other" 옵션

모든 질문에 자동으로 **"Other"** 옵션이 추가됩니다. 사용자가 제시된 선택지 외에 직접 텍스트를 입력할 수 있어, 예상치 못한 요구사항도 전달 가능합니다.

---

## 실제 사용 시나리오

### 시나리오 1: 아키텍처 결정

**사용자 요청**: "사용자 인증 기능을 추가해 주세요"

**Claude의 질문**:

> **인증 방식** - 어떤 인증 방식을 사용할까요?
> - JWT (Recommended) - stateless 토큰 기반, API 서비스에 적합
> - 세션 기반 - 서버 세션 이용, 전통적 웹 앱에 적합
> - OAuth 2.0 - 소셜 로그인 연동 필요 시
>
> **저장소** - 사용자 정보를 어디에 저장할까요?
> - PostgreSQL - 관계형 DB, 복잡한 쿼리 지원
> - MongoDB - NoSQL, 유연한 스키마
> - SQLite - 가벼운 파일 기반 DB

### 시나리오 2: UI 레이아웃 선택 (미리보기 활용)

**사용자 요청**: "대시보드 페이지를 만들어 주세요"

**Claude의 질문** (미리보기 포함):

> **레이아웃** - 대시보드 레이아웃을 어떻게 구성할까요?

각 선택지에 ASCII 목업이 미리보기로 제공됩니다:

**옵션 A: 그리드 레이아웃**
```
┌──────┬──────┬──────┐
│ 카드1 │ 카드2 │ 카드3 │
├──────┴──────┼──────┤
│   차트 영역   │ 사이드 │
└─────────────┴──────┘
```

**옵션 B: 리스트 레이아웃**
```
┌─────────────────────┐
│  요약 통계 바          │
├─────────────────────┤
│  항목 1              │
│  항목 2              │
│  항목 3              │
└─────────────────────┘
```

### 시나리오 3: 기능 범위 결정 (복수 선택)

**사용자 요청**: "엑셀 내보내기 기능을 추가해 주세요"

**Claude의 질문** (`multiSelect: true`):

> **내보내기 옵션** - 어떤 항목을 포함할까요? (복수 선택 가능)
> - ☐ 원본 데이터 - 필터 적용 전 전체 데이터
> - ☐ 차트 이미지 - 현재 표시된 차트를 이미지로 포함
> - ☐ 요약 시트 - 통계 요약 정보 별도 시트
> - ☐ 메타데이터 - 생성일시, 필터 조건 등

### 시나리오 4: Plan Mode에서의 활용

Plan Mode(`/plan`)와 함께 사용하면 **구현 전에 충분한 질의응답**이 이루어집니다:

```
사용자: /plan 특허 검색 기능을 개선해 주세요

Claude (Plan Mode):
  [코드베이스 분석 중...]

  질문 1: 검색 범위를 어디까지 확장할까요?
  - 제목+요약만 (현재)
  - 전문 검색 포함
  - 청구항 검색 포함

  질문 2: 검색 결과 정렬 기준은?
  - 관련도순 (Recommended)
  - 최신순
  - 출원일순

  [사용자 답변 수신 후]
  → 구체적인 구현 계획 수립
  → 사용자 승인 후 구현 시작
```

---

## Agent SDK에서의 활용

### 기본 통합 방법 (TypeScript)

Claude Agent SDK에서 AskUserQuestion을 처리하려면 `canUseTool` 콜백을 구현합니다:

```typescript
import Anthropic from "@anthropic-ai/sdk";
import { MessageStream } from "@anthropic-ai/sdk/lib/MessageStream";

const client = new Anthropic();

// AskUserQuestion 감지 및 처리
const stream = client.messages.stream({
  model: "claude-sonnet-4-20250514",
  max_tokens: 1024,
  messages: [...],
  tools: [/* AskUserQuestion 포함 */],
});

stream.on("toolUse", async (toolUse) => {
  if (toolUse.name === "AskUserQuestion") {
    const questions = toolUse.input.questions;

    // 사용자에게 질문 표시하고 답변 수집
    const answers = await displayQuestionsToUser(questions);

    // 답변을 Claude에게 전달
    return {
      questions: questions,
      answers: answers  // { "질문텍스트": "선택한label" }
    };
  }
});
```

### 답변 형식

```json
{
  "questions": [원본 질문 배열을 그대로 전달],
  "answers": {
    "어떤 인증 방식을 사용할까요?": "JWT",
    "어떤 항목을 포함할까요?": "원본 데이터, 차트 이미지"
  }
}
```

- 키: `question` 필드의 원문
- 값: 선택한 `label` (복수 선택 시 쉼표+공백으로 연결)
- "Other" 선택 시: 사용자가 입력한 텍스트가 그대로 전달

---

## 팁과 주의사항

### 효과적으로 활용하는 방법

1. **Plan Mode와 함께 사용**: `/plan` 명령과 함께 쓰면 구현 전 충분한 질의응답이 가능
2. **모호한 요청일수록 효과적**: "기능 추가해 줘" 같은 넓은 요청에서 진가 발휘
3. **설계 검증 도구로 활용**: 놓치기 쉬운 엣지 케이스를 Claude가 질문으로 발견
4. **추천 옵션 활용**: 첫 번째 선택지에 `(Recommended)` 표시가 있으면 Claude의 분석 기반 추천

### 알려진 제한사항

| 제한사항 | 설명 |
|---------|------|
| 질문 수 | 한 번에 1~4개까지 |
| 선택지 수 | 질문당 2~4개 (+ 자동 추가되는 "Other") |
| 미리보기 | `multiSelect: false`인 질문에서만 지원 |
| 서브에이전트 | Task 도구로 생성된 하위 에이전트에서는 사용 불가 |
| multiSelect 버그 | Enter 키가 선택 대신 다음 필드로 이동하는 이슈 존재 ([#12030](https://github.com/anthropics/claude-code/issues/12030)) |

### 주의사항

- AskUserQuestion은 **Claude가 자율적으로 호출**합니다. 사용자가 직접 질문을 주입할 수는 없음
- Agent SDK에서 `tools` 배열을 제한할 경우, `"AskUserQuestion"`을 명시적으로 포함해야 함
- 질문이 나오면 **실행이 일시 중단**되므로 자동화 파이프라인에서는 답변 핸들러 구현 필요

---

## 참고 자료

- [Claude Agent SDK 공식 문서 - Handle approvals and user input](https://platform.claude.com/docs/en/agent-sdk/user-input)
- [AskUserQuestion 활용 가이드 (Atcyrus)](https://www.atcyrus.com/stories/claude-code-ask-user-question-tool-guide)
- [Create Interactive AI Tools with Claude Code's AskUserQuestion (egghead.io)](https://egghead.io/create-interactive-ai-tools-with-claude-codes-ask-user-question~b47wn)
- [Claude Code AskUserQuestion으로 모호한 지시의 재작업 줄이기 (SmartScope)](https://smartscope.blog/en/generative-ai/claude/claude-code-askuserquestion-tool-guide/)
- [GitHub Issue #12030 - multiSelect 버그](https://github.com/anthropics/claude-code/issues/12030)
- [GitHub Issue #12605 - AskUserQuestion Hook 지원 요청](https://github.com/anthropics/claude-code/issues/12605)

---

*이 문서는 Claude Code의 AskUserQuestion 기능에 대한 종합 가이드입니다. 2025년 기준 정보를 바탕으로 작성되었습니다.*
