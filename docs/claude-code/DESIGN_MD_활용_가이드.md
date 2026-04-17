# DESIGN.md 활용 가이드

> AI에게 UI를 만들라고 하면 매번 다른 디자인이 나온다?  
> **DESIGN.md** 하나면 해결된다.

---

## 1. DESIGN.md란?

프로젝트 루트에 놓는 마크다운 파일로, **디자인 시스템을 텍스트로 정의**한 것이다.

- 색상, 타이포그래피, 간격, 컴포넌트 스타일 등을 한 장에 기술
- AI 코딩 에이전트(Claude Code, Cursor, Copilot 등)가 이 파일을 읽고 **일관된 UI**를 생성
- Google Stitch에서 소개된 개념이며, [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)에 58개+ 유명 사이트의 디자인 시스템이 공개되어 있음

### 핵심 장점

| 기존 방식 | DESIGN.md 방식 |
|-----------|---------------|
| AI한테 매번 "파란색 버튼, 둥근 모서리..." 반복 | 파일 한 번 넣으면 끝 |
| 페이지마다 다른 색상·폰트·레이아웃 | 프로젝트 전체 통일 |
| Figma/JSON 등 별도 툴링 필요 | 마크다운 한 장, 추가 도구 없음 |
| 디자이너 없으면 일관성 유지 힘듦 | 검증된 디자인 시스템 바로 적용 |

---

## 2. 우리 프로젝트 현황 (문제점)

현재 이 레포의 UI 파일들은 **각각 다른 디자인**을 사용 중:

| 파일 | 색상 테마 | 문제 |
|------|----------|------|
| `patent-tools/templates/index.html` | 보라 그라데이션 (`#667eea` → `#764ba2`) | 독자적 스타일 |
| `tools/compound-interest-visualization.html` | 다크 테마 (`#0f172a`) | 완전히 다른 톤 |
| `tools/greens_theorem_simulator.html` | 다크 테마 (다른 변형) | 유사하지만 미통일 |
| `tools/figma_visualization_sample.html` | 또 다른 스타일 | 별도 디자인 |
| `patent-tools/patent_search_web.py` (Streamlit) | 블루 (`#1f77b4`) | Streamlit 기본 |

**→ DESIGN.md를 도입하면 새 UI를 만들 때 자동으로 통일된 스타일이 적용된다.**

---

## 3. 도입 방법 (3단계)

### Step 1: DESIGN.md 선택

[awesome-design-md](https://github.com/VoltAgent/awesome-design-md/tree/main/design-md)에서 프로젝트 성격에 맞는 것을 고른다.

**우리 프로젝트에 추천하는 디자인 시스템:**

| 디자인 시스템 | 왜 맞는가 | 적합도 |
|-------------|----------|--------|
| **Notion** | 도구+문서 중심, 깔끔한 UI | ★★★★★ |
| **Linear** | 생산성 도구, 다크/라이트 모드 | ★★★★☆ |
| **Vercel** | 개발자 도구, 모던한 느낌 | ★★★★☆ |
| **Claude** | AI 도구와의 일체감 | ★★★☆☆ |
| **Stripe** | 대시보드/폼 중심 UI | ★★★☆☆ |

### Step 2: 프로젝트 루트에 배치

```bash
# 방법 A: awesome-design-md에서 직접 가져오기
curl -o DESIGN.md https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/notion/DESIGN.md

# 방법 B: 직접 커스터마이징 (아래 섹션 4 참고)
```

파일 위치: **프로젝트 루트** (`/DESIGN.md`)  
→ AI 에이전트가 자동으로 인식

### Step 3: AI에게 UI 작업 요청

```
# 이전 (매번 디자인 지시 필요)
"파란색 배경에 흰색 텍스트, 둥근 버튼으로 특허 검색 페이지 만들어줘"

# 이후 (DESIGN.md가 있으면)
"특허 검색 페이지 만들어줘"
→ AI가 DESIGN.md를 읽고 자동으로 일관된 디자인 적용
```

---

## 4. 커스텀 DESIGN.md 작성법

기존 디자인 시스템을 그대로 쓸 수도 있지만, **우리 프로젝트에 맞게 커스터마이징**하는 것을 추천한다.

### 필수 포함 섹션

```markdown
# DESIGN.md

## Design Philosophy
프로젝트의 디자인 철학 한 줄 요약

## Colors
- Primary: #색상코드
- Secondary: #색상코드
- Background: #색상코드
- Text: #색상코드
- Accent: #색상코드
- Error/Success/Warning 색상

## Typography
- Font Family: 'Pretendard', -apple-system, sans-serif
- Heading sizes (h1~h4)
- Body text size
- Font weights

## Spacing
- Base unit (예: 4px 또는 8px 그리드)
- Section padding
- Component gaps

## Components
- Buttons (primary, secondary, ghost)
- Input fields
- Cards
- Tables
- Navigation

## Layout
- Max content width
- Responsive breakpoints
- Grid system
```

### 작성 팁

1. **구체적인 값**을 적어라 — "큰 여백" 대신 `padding: 32px`
2. **예시 코드**를 포함하면 AI가 더 정확하게 구현한다
3. **하지 말아야 할 것**(Don'ts)도 적으면 효과적
4. 한국어/영어 혼용 가능 — AI는 둘 다 이해함

---

## 5. 실전 활용 시나리오

### 시나리오 A: 새 도구 페이지 추가

```
프롬프트: "tools/ 폴더에 환율 계산기 HTML 페이지를 만들어줘"
→ AI가 DESIGN.md의 색상·폰트·레이아웃을 따라 기존 도구들과 통일된 UI 생성
```

### 시나리오 B: 기존 페이지 리디자인

```
프롬프트: "patent-tools/templates/index.html을 DESIGN.md 스타일에 맞게 리디자인해줘"
→ 기능은 유지하면서 디자인만 통일
```

### 시나리오 C: Streamlit 앱 스타일링

```
프롬프트: "patent_search_web.py의 Streamlit 커스텀 CSS를 DESIGN.md에 맞춰줘"
→ Streamlit의 st.markdown()으로 커스텀 CSS 주입 시 일관성 유지
```

---

## 6. 빠른 시작 체크리스트

- [ ] [awesome-design-md](https://github.com/VoltAgent/awesome-design-md/tree/main/design-md)에서 마음에 드는 디자인 시스템 선택
- [ ] `DESIGN.md`를 프로젝트 루트에 배치
- [ ] (선택) 프로젝트 특성에 맞게 색상·폰트 커스터마이징
- [ ] AI에게 UI 작업 요청 시 자동 적용 확인
- [ ] 기존 HTML 파일들을 순차적으로 통일 (급하지 않으면 새 파일부터)

---

## 참고 링크

- [VoltAgent/awesome-design-md (GitHub)](https://github.com/VoltAgent/awesome-design-md) — 58개+ 디자인 시스템 모음
- [design-md 목록](https://github.com/VoltAgent/awesome-design-md/tree/main/design-md) — 전체 디자인 시스템 브라우징
- [CONTRIBUTING.md](https://github.com/VoltAgent/awesome-design-md/blob/main/CONTRIBUTING.md) — 새 디자인 시스템 기여 방법
