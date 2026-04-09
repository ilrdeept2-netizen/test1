# Figma AI 디자인 워크플로우 - Antigravity AG 적용 가이드

Figma의 `use_figma` 도구(캔버스 직접 쓰기)와 `get_design_context`를 활용하여, AG 환경에서 **디자인 → 코드** 파이프라인을 구축하는 방법을 정리합니다.

---

## 배경: 무엇이 바뀌었나 (2026년 3월 기준)

| 구분 | 이전 (read-only) | 현재 (read + write) |
|------|-------------------|---------------------|
| Figma MCP | `get_design_context`로 **읽기만** 가능 | `use_figma`로 **캔버스에 직접 쓰기** 가능 |
| 워크플로우 | 디자이너가 먼저 그림 → 개발자가 코드 변환 | AI가 디자인 생성 → 디자이너가 검수 → AI가 코드 변환 |
| 컴포넌트 | 수동으로 컴포넌트 구성 | AI가 컴포넌트 기반으로 자동 생성 |

---

## 핵심 3단계 워크플로우

```
┌─────────────────────────────────────────────────────────┐
│  1️⃣ use_figma          2️⃣ Figma에서         3️⃣ get_design_context  │
│  컴포넌트/디자인 생성  → 확인 및 수정     → 코드 변환              │
│                                                         │
│  "로그인 페이지        디자이너가 간격,    AG에서 React/HTML       │
│   만들어줘"            색상, 레이아웃 조정  코드로 자동 변환        │
└─────────────────────────────────────────────────────────┘
```

### Step 1: `use_figma`로 디자인 생성

AI에게 자연어로 디자인을 요청하면 Figma 캔버스에 컴포넌트 기반 디자인이 생성됩니다.

**프롬프트 예시:**
```
use_figma로 다음 디자인을 만들어줘:
- 로그인 페이지 (이메일 + 비밀번호 + 소셜 로그인)
- 모바일 반응형 고려
- Auto Layout 적용
- 컬러 스타일은 프로젝트 디자인 시스템 따르기
```

**생성되는 결과물:**
- Figma 프레임 (Auto Layout 적용)
- 컴포넌트 인스턴스 (Button, Input, Typography 등)
- 스타일 변수 연결 (Color, Typography tokens)

### Step 2: Figma에서 확인/수정

디자이너 또는 본인이 Figma에서 직접 검수합니다.

**체크리스트:**
- [ ] 레이아웃 간격/정렬 확인
- [ ] 브랜드 컬러 및 타이포그래피 일관성
- [ ] 컴포넌트 네이밍 컨벤션 준수
- [ ] 반응형 Constraints / Auto Layout 정상 동작
- [ ] 불필요한 레이어 정리

### Step 3: `get_design_context`로 코드 변환

수정 완료된 디자인을 AI가 읽어서 코드로 변환합니다.

```
get_design_context로 이 Figma 프레임을 읽어서
React + Tailwind CSS 컴포넌트로 변환해줘.
- TypeScript 사용
- 컴포넌트 분리
- 반응형 대응
```

---

## Antigravity AG에서의 설정 방법

### 1. Figma MCP 서버 연결

AG의 MCP 설정에 Figma 서버를 추가합니다.

**`~/.antigravity/settings.json` (또는 프로젝트 `.antigravity/settings.json`):**

```json
{
  "mcpServers": {
    "figma": {
      "command": "npx",
      "args": ["-y", "figma-developer-mcp", "--stdio"],
      "env": {
        "FIGMA_API_KEY": "<your-figma-personal-access-token>"
      }
    }
  }
}
```

**Figma API 토큰 발급:**
1. Figma → Settings → Personal Access Tokens
2. 토큰 생성 (scope: `file:read`, `file:write` 필수)
3. 환경변수 또는 설정 파일에 등록

### 2. AG 에이전트 모드 활용

AG에서 Claude Opus 4.6 모델을 에이전트 모드로 사용하면, `use_figma`와 `get_design_context`를 하나의 대화 흐름 안에서 연속 호출할 수 있습니다.

```
[AG Agent Mode]
├─ use_figma: 디자인 생성
├─ (사용자가 Figma에서 검수)
├─ get_design_context: 디자인 읽기
└─ 파일 생성: React 컴포넌트 코드 출력
```

### 3. 프로젝트 구조 권장

```
project/
├── design/
│   └── figma-tokens.json       # Figma에서 추출한 디자인 토큰
├── src/
│   ├── components/
│   │   ├── ui/                 # Figma 컴포넌트 → 코드 매핑
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Card.tsx
│   │   └── pages/
│   │       ├── LoginPage.tsx   # use_figma로 생성된 디자인 기반
│   │       └── Dashboard.tsx
│   └── styles/
│       └── tokens.css          # 디자인 토큰 CSS 변수
└── .antigravity/
    └── settings.json           # MCP 서버 설정
```

---

## 실전 워크플로우 시나리오

### 시나리오 1: 특허 도구 UI 리디자인

기존 `patent-tools/templates/`의 Flask 템플릿을 현대적 UI로 개선:

```
1. AG에서 프롬프트:
   "use_figma로 특허 문서 변환기 대시보드를 만들어줘.
    - 파일 업로드 영역
    - 변환 진행률 표시
    - 결과 다운로드 버튼
    - 사이드바에 변환 이력"

2. Figma에서 검수 후 수정

3. AG에서:
   "get_design_context로 읽어서 Flask Jinja2 템플릿 +
    Tailwind CSS로 변환해줘"
```

### 시나리오 2: 모바일 AG 모니터링 UI

`안그래비티_모바일_AG_연동_가이드.md`의 Phone Connect UI를 개선:

```
1. "use_figma로 AG 모바일 모니터링 대시보드를 디자인해줘.
    - 에이전트 상태 카드
    - 실시간 로그 뷰
    - 승인/거부 버튼 (큰 터치 타겟)
    - 다크 모드"

2. Figma에서 터치 UX 검수

3. "get_design_context → React Native 또는 PWA 코드로 변환"
```

### 시나리오 3: AI 뉴스 다이제스트 리포트 페이지

`tools/ai-news-digest/`의 출력물을 시각적 리포트로:

```
1. "use_figma로 AI 뉴스 다이제스트 웹 리포트 레이아웃:
    - 카드형 뉴스 목록
    - 중요도 태그 (🔴 높음 / 🟡 보통 / 🟢 낮음)
    - 요약/원문 토글
    - 날짜 필터"

2. 검수 후 수정

3. "get_design_context → 정적 HTML 페이지로 변환"
```

---

## 팁 & 베스트 프랙티스

### 효과적인 프롬프트 작성법

| 나쁜 예 | 좋은 예 |
|---------|---------|
| "대시보드 만들어줘" | "use_figma로 SaaS 대시보드를 만들어줘. 좌측 사이드바, 상단에 KPI 카드 4개, 하단에 차트 2개. Auto Layout, 1440x900 기준" |
| "모바일 앱" | "use_figma로 모바일 로그인 화면: 375x812, 상단 로고, 이메일/비밀번호 입력, 소셜 로그인 3개(Google/Apple/Kakao), 하단 회원가입 링크" |

### 주의사항

1. **use_figma는 기존 디자인을 덮어쓸 수 있음** → 항상 새 페이지에서 작업
2. **컴포넌트 네이밍**이 코드 변환 품질에 직접 영향 → 생성 후 네이밍 확인 필수
3. **디자인 토큰 연결** 확인 → 하드코딩된 색상값이 아닌 변수 참조인지 체크
4. **Auto Layout** 적용 여부 확인 → 미적용 시 반응형 코드 변환이 부정확해짐
5. **AG에서 use_figma 호출 시** → 에이전트 모드에서 MCP 도구 승인 필요 (첫 호출 시)

### 디자인 시스템 연동

기존 Figma 디자인 시스템이 있다면 `use_figma`에 명시:

```
"use_figma로 디자인을 만들되,
 기존 디자인 시스템 라이브러리 'AG Design System'의
 컴포넌트를 사용해줘:
 - Button/Primary, Button/Secondary
 - Input/Default, Input/Error
 - Typography/H1, Typography/Body"
```

---

## AG + Figma + Claude 통합 아키텍처

```
┌──────────────────────────────────────────────────────┐
│                  Antigravity AG                       │
│              (Claude Opus 4.6 Agent)                  │
│                                                      │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────┐ │
│  │  use_figma   │    │ get_design_  │    │  파일    │ │
│  │  (MCP Write) │───→│ context      │───→│  생성   │ │
│  │              │    │ (MCP Read)   │    │         │ │
│  └──────┬───────┘    └──────┬───────┘    └────┬────┘ │
│         │                   │                  │      │
└─────────┼───────────────────┼──────────────────┼──────┘
          │                   │                  │
          ▼                   ▼                  ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │   Figma      │    │   Figma      │    │  프로젝트    │
   │   캔버스     │←──→│   캔버스     │    │  소스 코드   │
   │   (생성)     │    │   (읽기)     │    │  (.tsx 등)   │
   └─────────────┘    └─────────────┘    └─────────────┘
         │
         ▼
   ┌─────────────┐
   │  디자이너    │
   │  검수/수정   │
   └─────────────┘
```

---

## 참고

- [Figma Developer MCP](https://github.com/nichochar/figma-developer-mcp)
- [Figma API 공식 문서](https://www.figma.com/developers/api)
- [안그래비티 모바일 AG 연동 가이드](안그래비티_모바일_AG_연동_가이드.md)
- [Claude Code MCP 연동 정리](Claude_Code_플러그인_MCP_연동_정리.md)
