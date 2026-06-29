---
title: "DeerFlow 분석: ByteDance 오픈소스 AI 슈퍼에이전트 하네스"
date: 2026-03-01
category: ai-research
tags: [agent, multi-agent, llm, open-source, analysis, deerflow]
status: active
summary: "ByteDance가 공개한 MIT 라이선스 AI 에이전트 하네스 DeerFlow 구조 및 특징 분석"
source: "https://github.com/bytedance/deer-flow"
related:
  - docs/research/ai-wrapper-strategy.md
  - docs/claude-code/Claude_Code_Agent_Teams_가이드.md
---

# DeerFlow 분석: ByteDance의 오픈소스 AI 에이전트

> ByteDance(틱톡 모회사)가 공개한 AI 슈퍼에이전트 하네스
> GitHub Stars: 27,300+ | Forks: 3,000+ | Contributors: 107+
> 라이선스: MIT

---

## 1. DeerFlow란?

**DeerFlow** = **D**eep **E**xploration and **E**fficient **R**esearch **Flow**

한 줄 요약: **리서치하고, 코딩하고, 콘텐츠를 만드는 오픈소스 슈퍼에이전트 하네스**

단순한 챗봇이 아닙니다. 샌드박스, 메모리, 도구, 스킬, 서브에이전트를 활용해서 수 분에서 수 시간이 걸리는 복잡한 작업을 자율적으로 처리합니다.

### 버전 히스토리

| 버전 | 시기 | 특징 |
|------|------|------|
| v1.0 | 2025년 5월 | Deep Research 프레임워크로 출발 |
| v2.0 | 2026년 2월 27일 | 완전히 새로 작성. 슈퍼에이전트 하네스로 진화 |

v2.0은 v1과 코드를 공유하지 않는 **완전한 재작성**입니다. 출시 당일 GitHub 트렌딩 1위를 달성했습니다.

---

## 2. 아키텍처 - 핵심 구조

```
┌─────────────────────────────────────────────────┐
│                   Frontend (Next.js)             │
├─────────────────────────────────────────────────┤
│                 Nginx Reverse Proxy              │
├──────────┬──────────────┬───────────────────────┤
│ LangGraph│  Gateway API │   Provisioner         │
│  Server  │  (REST)      │   (K8s Sandbox)       │
│          │              │                       │
│ ┌──────┐ │ • 모델 관리   │ • 샌드박스 할당        │
│ │Agent │ │ • 스킬 관리   │ • 컨테이너 격리        │
│ │Runtime│ │ • 메모리 관리 │                       │
│ └──────┘ │ • 파일 관리   │                       │
├──────────┴──────────────┴───────────────────────┤
│              LangChain + LangGraph               │
└─────────────────────────────────────────────────┘
```

### 4개의 핵심 서비스

1. **Next.js Frontend** - 웹 UI
2. **LangGraph Server** - 에이전트 런타임 (핵심 두뇌)
3. **Gateway API** - 모델/스킬/메모리/파일 관리 REST 엔드포인트
4. **Provisioner** - Kubernetes 기반 샌드박스 할당 (선택)

### 멀티에이전트 계층 구조

```
         ┌─────────────┐
         │ Coordinator  │  ← 전체 프로세스 감독
         └──────┬───────┘
                │
         ┌──────┴───────┐
         │   Planner    │  ← 리서치 계획 수립
         └──────┬───────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐
│Researcher│ │ Coder  │ │Reporter│
└────────┘ └────────┘ └────────┘
  웹 검색     코드 실행   결과 요약
```

각 에이전트는 독립적인 역할을 가지며, LangGraph 상태 머신을 통해 협업합니다.

---

## 3. 핵심 차별점 - 뭐가 다른가?

### 3-1. 프레임워크가 아닌 "하네스"

기존 도구들(LangChain, CrewAI 등)은 **추상화 레이어**를 제공합니다.
DeerFlow는 **실행 인프라**를 제공합니다.

| 구분 | 기존 프레임워크 | DeerFlow |
|------|---------------|----------|
| 접근 | 고수준 추상화 | 저수준 실행 인프라 |
| 실행 환경 | 개발자가 구성 | 샌드박스 내장 |
| 메모리 | 플러그인 필요 | 영구 메모리 기본 탑재 |
| 배포 | 직접 구성 | Local/Docker/K8s 3모드 |
| 서브에이전트 | 제한적 | 병렬 스폰 네이티브 지원 |

### 3-2. 샌드박스 실행 환경

모든 코드 실행이 **격리된 Docker 컨테이너** 안에서 이루어집니다.

```
SandboxProvider (추상)
├── LocalSandboxProvider   → 로컬 파일시스템 직접 접근
└── AioSandboxProvider     → Docker 컨테이너 격리

파일시스템 구조:
/mnt/user-data/
├── workspace/    # 작업 디렉토리
├── uploads/      # 업로드 파일
└── outputs/      # 결과물 출력

내장 도구: bash, ls, read_file, write_file, str_replace
```

- 스레드별 완전 격리 환경
- 3가지 배포 모드: Local → Docker → Kubernetes Provisioner

### 3-3. 영구 메모리 (Persistent Memory)

단순히 "기억한다"가 아닙니다. **신뢰도 점수 기반 메모리 시스템**입니다.

```
요청 → MemoryMiddleware → 30초 디바운스 → MemoryUpdater (LLM)
                                              ↓
                                    사용자 맥락/사실/선호도 추출
                                    + 신뢰도 점수 부여
                                              ↓
                                    memory.json에 저장
                                              ↓
                               다음 대화 시 상위 15개 사실 주입
```

- 세션 간 컨텍스트 유지
- 30초 디바운스로 LLM 호출 최소화
- 완전 로컬 저장 (외부 전송 없음)

### 3-4. 확장 가능한 스킬 시스템

스킬이 **코드가 아닌 마크다운 파일**이라는 것이 핵심입니다. 비개발자도 작성할 수 있고, 버전 관리와 공유가 쉽습니다.

```
skills/
├── public/          # 내장 스킬
│   ├── research/SKILL.md
│   ├── report/SKILL.md
│   ├── slides/SKILL.md
│   ├── image_gen/SKILL.md
│   └── video_gen/SKILL.md
└── custom/          # 사용자 커스텀 스킬
    └── my_skill/SKILL.md
```

내장 스킬: 리서치, 보고서, 슬라이드(PPT), 웹페이지, 이미지 생성, 비디오 생성, 팟캐스트(2인 호스트, Volcengine TTS)

### 3-5. MCP (Model Context Protocol) 통합

커스텀 도구 통합을 위한 MCP 서버를 지원합니다. OAuth 플로우까지 내장.

### 3-6. 멀티채널 IM 연동 (공인 IP 불필요)

| 채널 | 연결 방식 |
|------|----------|
| Telegram | Bot API Long-Polling |
| Slack | Socket Mode |
| Feishu/Lark | WebSocket |

지원 커맨드: `/new`, `/status`, `/models`, `/memory`, `/help`

### 3-7. 컨텍스트 엔지니어링

장시간 작업에서 토큰 예산을 관리하기 위한 전략:
- 공격적인 중간 결과 요약 (Aggressive Summarization)
- 중간 결과물을 파일시스템으로 오프로드
- 체크포인팅과 상태 관리

---

## 4. 기술 스택

```
Backend:   Python + LangChain + LangGraph + LiteLLM
Frontend:  Next.js + Node.js 22+
패키지:     uv (Python) / pnpm (Node)
실행환경:   Docker / Kubernetes
프록시:     Nginx
검색엔진:   Tavily, Brave, DuckDuckGo, Arxiv
벡터DB:    Qdrant, Milvus, VikingDB
RAG:       RAGFlow 지원
LLM:       LiteLLM → OpenAI, Qwen, Claude 등 모든 OpenAI 호환 API
TTS:       Volcengine (팟캐스트용)
크롤링:     Jina Crawler
```

### 내부 구조 심화: 9-미들웨어 체인

에이전트 런타임은 `make_lead_agent(config)`로 생성되며, 동적 모델 선택과 9개의 미들웨어 체인으로 구성됩니다. 이 미들웨어가 메모리, 컨텍스트, 도구 라우팅 등 교차 관심사를 처리합니다.

---

## 5. 프로젝트 구조

```
deer-flow/
├── .github/          # CI/CD 워크플로우
├── backend/          # Python 서비스 (에이전트 런타임, 게이트웨이, 프로비저너)
├── frontend/         # Web UI (Next.js)
├── docker/           # 컨테이너 정의
├── docs/             # 문서
├── scripts/          # 자동화 스크립트
├── skills/public/    # 내장 스킬 라이브러리 (research, reports, slides 등)
├── config.yaml       # 모델/도구/샌드박스 설정
└── Makefile          # 태스크 오케스트레이션
```

### 빠른 시작

```bash
# Docker 배포 (프로덕션)
make docker-init && make docker-start

# 로컬 개발
make dev

# 접속: http://localhost:2026
```

---

## 6. 경쟁 도구 비교

| 항목 | DeerFlow | AutoGPT | CrewAI | LangGraph |
|------|----------|---------|--------|-----------|
| **유형** | 슈퍼에이전트 하네스 | 자율 에이전트 | 멀티에이전트 프레임워크 | 상태 그래프 라이브러리 |
| **실행 환경** | 샌드박스 내장 | 제한적 | 없음 | 없음 |
| **영구 메모리** | 기본 탑재 | 부분 지원 | 제한적 | 직접 구현 |
| **배포 모드** | Local/Docker/K8s | Docker | 없음 | 없음 |
| **서브에이전트** | 네이티브 | 제한적 | 역할 기반 | 노드 기반 |
| **스킬 시스템** | 마크다운 기반 확장 | 플러그인 | 도구 | 도구 |
| **벤치마크** | 93%+ 정확도 | - | - | - |
| **Human-in-the-Loop** | 네이티브 지원 | 제한적 | 제한적 | 지원 |
| **IM 연동** | Telegram/Slack/Lark | 없음 | 없음 | 없음 |
| **라이선스** | MIT | MIT | MIT | MIT |
| **적합한 용도** | 코드 실행/파일 I/O가 필요한 자율 멀티스텝 작업 | 탐색적 프로토타이핑 | 팀 메타포 기반 비즈니스 워크플로우 | 조건 분기가 있는 정밀 워크플로우 오케스트레이션 |

**핵심 차이**: DeerFlow는 "에이전트가 추론할 수 있게 해주는 도구"가 아니라, **"에이전트가 실제로 일할 수 있는 실행 환경"**을 제공합니다.

**LangGraph와의 관계**: DeerFlow는 LangGraph와 경쟁하지 않습니다. LangGraph **위에** 구축되어 이를 확장합니다. LangGraph가 상태 머신을 제공한다면, DeerFlow는 그 위에 파일시스템, 샌드박스, 메모리, 스킬, 오케스트레이션 레이어를 올린 **완전한 런타임**입니다.

---

## 7. 왜 오픈소스인가? (전략적 분석)

ByteDance가 MIT 라이선스로 이것을 공개한 데는 전략적 이유가 있습니다:

1. **생태계 장악**: OpenAI/Microsoft의 독점적 시스템과 경쟁하려면 제품이 아닌 **생태계**를 잠가야 합니다
2. **인재 확보**: 오픈소스 크레딧이 AI 엔지니어링 인재를 끌어당깁니다
3. **표준화**: AI 에이전트 실행 환경의 사실상 표준(de facto standard)을 노립니다
4. **커뮤니티 혁신**: v1에서 커뮤니티가 Deep Research를 넘어 다양한 용도로 확장한 것처럼, 생태계 확장을 기대합니다

---

## 8. 요약 - 한눈에 보기

```
┌──────────────────────────────────────────────┐
│              DeerFlow 2.0 요약                │
├──────────────────────────────────────────────┤
│ 만든 곳:    ByteDance (틱톡 모회사)            │
│ 유형:      오픈소스 슈퍼에이전트 하네스          │
│ 기반:      LangChain + LangGraph              │
│ 핵심:      샌드박스 + 메모리 + 스킬 + 서브에이전트│
│ Stars:    27,300+                             │
│ 라이선스:   MIT                                │
│ 정확도:    벤치마크 93%+                        │
│ 배포:      Local / Docker / Kubernetes         │
│                                              │
│ 한 줄 정리:                                    │
│ "AI 에이전트에게 추상화가 아닌                   │
│  실행 인프라를 제공하는 하네스"                   │
└──────────────────────────────────────────────┘
```

---

## 참고 자료

- [GitHub: bytedance/deer-flow](https://github.com/bytedance/deer-flow)
- [DeerFlow 2.0 분석 - YUV.AI](https://yuv.ai/blog/deer-flow)
- [DeerFlow 2.0 - Edward Kiledjian](https://kiledjian.com/2026/03/06/deerflow-bytedances-opensource-ai-agent.html)
- [MarkTechPost - DeerFlow 분석](https://www.marktechpost.com/2025/05/09/bytedance-open-sources-deerflow-a-modular-multi-agent-framework-for-deep-research-automation/)
- [ByteIota - DeerFlow GitHub #2](https://byteiota.com/bytedance-deerflow-open-source-ai-agent-framework-hits-github-2/)
- [DeepWiki - deer-flow 개요](https://deepwiki.com/bytedance/deer-flow/1-overview)
