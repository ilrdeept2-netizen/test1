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
- 파일시스템 접근 가능
- Bash/Python 완전 지원
- 스레드별 격리 환경

### 3-3. 영구 메모리 (Persistent Memory)

세션 간 컨텍스트를 유지합니다. 대화가 끝나도 사용자 맥락을 기억합니다.

### 3-4. 확장 가능한 스킬 시스템

마크다운 기반 스킬 모듈로 기능을 확장합니다:
- 리서치 보고서 생성
- 슬라이드(PPT) 생성
- 이미지/비디오 생성
- 팟캐스트 생성 (2인 호스트 형식)
- 데이터 파이프라인 구축
- 대시보드 생성

### 3-5. MCP (Model Context Protocol) 통합

커스텀 도구 통합을 위한 MCP 서버를 지원합니다.

### 3-6. 멀티채널 IM 연동

Telegram, Slack, Feishu/Lark와 바로 연결됩니다.

---

## 4. 기술 스택

```
Backend:   Python + LangChain + LangGraph
Frontend:  Next.js + Node.js 22+
패키지:     uv (Python) / pnpm (Node)
실행환경:   Docker / Kubernetes
프록시:     Nginx
검색엔진:   Tavily, Brave, DuckDuckGo, Arxiv
벡터DB:    Qdrant, Milvus, VikingDB
RAG:       RAGFlow 지원
LLM:       OpenAI 호환 엔드포인트 (어떤 LLM이든 연결 가능)
```

---

## 5. 프로젝트 구조

```
deer-flow/
├── backend/          # Python 서비스, 에이전트, 게이트웨이
├── frontend/         # Web UI (Next.js)
├── docker/           # 컨테이너 설정
├── docs/             # 문서
├── scripts/          # 유틸리티
├── skills/public/    # 내장 스킬 라이브러리
└── Makefile          # 개발 커맨드
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

**핵심 차이**: DeerFlow는 "에이전트가 추론할 수 있게 해주는 도구"가 아니라, **"에이전트가 실제로 일할 수 있는 실행 환경"**을 제공합니다.

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
