# DESIGN.md — test1 프로젝트 디자인 시스템

> 이 파일은 AI 코딩 에이전트가 읽고 일관된 UI를 생성하기 위한 디자인 시스템 정의입니다.
> 모든 새 UI 페이지는 이 스타일을 따릅니다.

---

## Design Philosophy

실용적이고 깔끔한 도구 UI. 군더더기 없이 기능에 집중하며, 한국어 콘텐츠가 잘 읽히는 것을 최우선으로 한다. 다크 모드 기본, 라이트 모드 선택적 지원.

---

## Colors

### Dark Theme (기본)

```
--color-bg-primary:     #0f172a    /* 메인 배경 */
--color-bg-secondary:   #1e293b    /* 카드, 섹션 배경 */
--color-bg-tertiary:    #334155    /* 호버, 입력 필드 배경 */

--color-text-primary:   #f1f5f9    /* 본문 텍스트 */
--color-text-secondary: #94a3b8    /* 보조 텍스트, 라벨 */
--color-text-muted:     #64748b    /* 비활성 텍스트 */

--color-accent:         #6366f1    /* 주요 액센트 (인디고) */
--color-accent-hover:   #818cf8    /* 액센트 호버 */
--color-accent-subtle:  rgba(99, 102, 241, 0.15)  /* 액센트 배경 */

--color-success:        #22c55e
--color-warning:        #f59e0b
--color-error:          #ef4444

--color-border:         #334155    /* 기본 테두리 */
--color-border-subtle:  #1e293b    /* 미묘한 구분선 */
```

### Light Theme (선택)

```
--color-bg-primary:     #ffffff
--color-bg-secondary:   #f8fafc
--color-bg-tertiary:    #f1f5f9
--color-text-primary:   #0f172a
--color-text-secondary: #475569
--color-accent:         #4f46e5
```

---

## Typography

```
--font-family:      'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                    'Malgun Gothic', sans-serif
--font-mono:        'JetBrains Mono', 'Fira Code', 'Consolas', monospace

--font-size-xs:     0.75rem    /* 12px — 캡션, 뱃지 */
--font-size-sm:     0.875rem   /* 14px — 보조 텍스트 */
--font-size-base:   1rem       /* 16px — 본문 */
--font-size-lg:     1.125rem   /* 18px — 강조 본문 */
--font-size-xl:     1.25rem    /* 20px — 소제목 */
--font-size-2xl:    1.5rem     /* 24px — 섹션 제목 */
--font-size-3xl:    1.875rem   /* 30px — 페이지 제목 */

--font-weight-normal:  400
--font-weight-medium:  500
--font-weight-bold:    700

--line-height-tight:   1.25
--line-height-normal:  1.6
--line-height-relaxed: 1.75
```

---

## Spacing

8px 그리드 시스템 기반.

```
--space-1:   4px
--space-2:   8px
--space-3:   12px
--space-4:   16px
--space-5:   20px
--space-6:   24px
--space-8:   32px
--space-10:  40px
--space-12:  48px
--space-16:  64px
```

---

## Border Radius

```
--radius-sm:    4px     /* 입력 필드, 뱃지 */
--radius-md:    8px     /* 버튼, 카드 */
--radius-lg:    12px    /* 모달, 큰 카드 */
--radius-xl:    16px    /* 히어로 섹션 */
--radius-full:  9999px  /* 원형 아바타, 태그 */
```

---

## Shadows

```
--shadow-sm:    0 1px 2px rgba(0, 0, 0, 0.3)
--shadow-md:    0 4px 6px rgba(0, 0, 0, 0.3)
--shadow-lg:    0 10px 25px rgba(0, 0, 0, 0.4)
--shadow-glow:  0 0 20px rgba(99, 102, 241, 0.3)   /* 액센트 글로우 효과 */
```

---

## Components

### Buttons

```css
/* Primary */
.btn-primary {
    background: var(--color-accent);
    color: #ffffff;
    padding: 10px 20px;
    border-radius: var(--radius-md);
    font-weight: var(--font-weight-medium);
    font-size: var(--font-size-sm);
    border: none;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s;
}
.btn-primary:hover {
    background: var(--color-accent-hover);
    box-shadow: var(--shadow-glow);
}

/* Secondary (outline) */
.btn-secondary {
    background: transparent;
    color: var(--color-accent);
    border: 1px solid var(--color-accent);
    padding: 10px 20px;
    border-radius: var(--radius-md);
}

/* Ghost */
.btn-ghost {
    background: transparent;
    color: var(--color-text-secondary);
    border: none;
    padding: 10px 20px;
}
.btn-ghost:hover {
    background: var(--color-bg-tertiary);
}
```

### Input Fields

```css
input, textarea, select {
    background: var(--color-bg-tertiary);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    font-size: var(--font-size-base);
    transition: border-color 0.2s;
}
input:focus, textarea:focus, select:focus {
    border-color: var(--color-accent);
    outline: none;
    box-shadow: 0 0 0 3px var(--color-accent-subtle);
}
```

### Cards

```css
.card {
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    transition: box-shadow 0.2s;
}
.card:hover {
    box-shadow: var(--shadow-md);
}
```

### Tables

```css
table {
    width: 100%;
    border-collapse: collapse;
}
th {
    background: var(--color-bg-tertiary);
    color: var(--color-text-secondary);
    font-weight: var(--font-weight-medium);
    font-size: var(--font-size-sm);
    text-align: left;
    padding: 12px 16px;
}
td {
    padding: 12px 16px;
    border-bottom: 1px solid var(--color-border-subtle);
    color: var(--color-text-primary);
}
tr:hover {
    background: var(--color-bg-tertiary);
}
```

---

## Layout

```
--max-content-width:  1200px
--content-padding:    var(--space-6)     /* 좌우 여백 */

/* 반응형 Breakpoints */
--breakpoint-sm:   640px
--breakpoint-md:   768px
--breakpoint-lg:   1024px
--breakpoint-xl:   1280px
```

### 페이지 구조

```
┌─────────────────────────────────────┐
│  Header (고정, blur 배경)            │
├─────────────────────────────────────┤
│                                     │
│  Main Content (max-width: 1200px)   │
│  ┌───────────┐  ┌───────────┐      │
│  │   Card     │  │   Card    │      │
│  └───────────┘  └───────────┘      │
│                                     │
├─────────────────────────────────────┤
│  Footer (간결하게)                   │
└─────────────────────────────────────┘
```

---

## Don'ts (하지 말 것)

- 그라데이션 배경을 페이지 전체에 쓰지 않는다 (액센트 버튼에만 허용)
- 3개 이상의 폰트를 섞지 않는다
- 그림자를 과도하게 쓰지 않는다 — 계층 구분은 배경색 차이로
- 밝은 색 텍스트에 밝은 배경을 쓰지 않는다 (대비 4.5:1 이상 유지)
- 애니메이션은 0.3s 이하로 — 느린 전환은 답답하게 느껴진다
