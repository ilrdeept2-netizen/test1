# AI GPU 커널 최적화: 인간 수준을 넘어선 자동화 시대

> Sharon Zhou(@realSharonZhou) — AMD VP of AI, 前 Lamini CEO, 前 Stanford AI 교수
> "LLM이 어떤 새로운 하드웨어 세대에서든 차세대 AI 연구를 초고속으로 만들 수 있는 미래가 열리고 있다 — IDE 안에서 즉석으로."

---

## 1. 핵심 요약

| 항목 | 내용 |
|------|------|
| **무엇이 일어났나** | AI가 실제 프로덕션 모델에서 GPU 커널을 자동 최적화해 인간 엔지니어 수준 이상의 성능 달성 |
| **왜 중요한가** | 수주~수개월 걸리던 GPU 세대 전환 커널 작업이 수시간으로 단축 가능 |
| **누가 주도하나** | Meta(KernelEvolve), NVIDIA(DeepSeek-R1 실험), AMD+Stanford(PEAK, Astra), Sakana AI 등 |
| **파급효과** | GPU 최적화 → 연산량 증가 → 파운데이션 모델 학습 가속 → 더 강력한 AI → 더 나은 커널 최적화 (선순환) |

---

## 2. 배경: GPU 커널 최적화가 왜 어려운가

GPU 커널은 GPU 위에서 실행되는 저수준 코드로, AI 모델의 실제 연산을 수행하는 핵심 단위다.

### 전통적 어려움
- **조합적 최적화 공간**: 메모리 레이아웃, 스레드 블록 크기, 레지스터 할당, 공유 메모리 활용 등 수백 가지 파라미터 조합
- **하드웨어 종속성**: NVIDIA(CUDA), AMD(ROCm/HIP), Meta MTIA 등 아키텍처마다 완전히 다른 최적화 전략 필요
- **전문 인력 부족**: 고성능 커널을 작성할 수 있는 엔지니어는 전 세계적으로 극소수
- **세대 전환 비용**: 새 GPU 출시 시마다 커널을 재작성·재최적화하는 데 수주~수개월 소요

### GPU 커널이 중요한 이유
커널 런타임의 작은 개선이라도 대규모 배포 시 비용 효율성과 에너지 소비에서 막대한 이득을 가져온다. 수십억 사용자에게 서비스하는 추천 모델이라면 1%의 성능 향상도 수백만 달러의 비용 절감으로 이어진다.

---

## 3. 주요 시스템 및 연구 성과

### 3.1 KernelEvolve (Meta) — 프로덕션 배포 사례

Meta가 설계·구현·배포한 에이전틱 커널 코딩 프레임워크.

**적용 범위:**
- NVIDIA GPU (H100, A100), AMD GPU (MI300, MI350), Meta 자체 가속기 (MTIA v3)
- **수백 개의 프로덕션 추천 모델**, 매일 수십억 사용자에게 서비스

**핵심 성과:**
| 워크로드 | 성능 향상 (vs PyTorch 기준) |
|----------|---------------------------|
| MTIA RMSNorm 2D backward | **17×** |
| Batch Event Truncate | 9.8× |
| MBDT (데이터 전처리) | 9.3× |
| conv1d | 6.5× |
| Llama-3.1-8B Vanilla Attention | 4.6× |
| WuKong Optimized FM | 4.0× |

- **개발 시간**: 수주 → 수시간으로 단축
- **KernelBench**: 250개 문제 전체에서 100% 통과율 달성
- **480개 연산자-플랫폼 조합**에서 100% 정확성

**기술 핵심:**
- 그래프 기반 탐색 + 선택 정책 + 적합도 함수
- Triton, CuTe DSL부터 저수준 하드웨어 비종속 언어까지 다층 추상화
- 커널 융합(kernel fusion)이 핵심 최적화 전략: 여러 연산을 하나의 커널로 통합해 중간 텐서 물질화 제거
- 자기 개선 상태 머신 + 트리 탐색 + 영속적 지식 베이스

### 3.2 NVIDIA — DeepSeek-R1 기반 자동 커널 생성

NVIDIA 엔지니어들이 DeepSeek-R1 모델에 추가 추론 연산을 투입해 자동으로 최적화된 GPU 어텐션 커널을 생성.

- Level-1 문제: **100%** 정확한 커널 생성
- Level-2 문제: **96%** 정확한 커널 생성
- **일부 결과가 숙련된 엔지니어가 개발한 최적화 커널보다 우수**

### 3.3 PEAK (Microsoft Research / Stanford)

성능 엔지니어링 AI 어시스턴트. GPU Kernel Scientist가 LLM을 사용해 CUDA/HIP 커널을 반복적으로 변형.

- 벤더 라이브러리 대비 MatMul 성능: AI CUDA Engineer ~45% → **PEAK 90% 이상**
- 인간 엔지니어와 협업 모드 또는 완전 자율 모드 모두 지원

### 3.4 Astra (Stanford)

프로덕션 환경의 현실을 반영해, 처음부터 생성이 아닌 **기존 CUDA 구현의 최적화**에 집중. SGLang(프로덕션급 LLM 서빙 프레임워크)에서 직접 커널을 가져와 최적화.

### 3.5 Sakana AI — AI CUDA Engineer

에이전틱 CUDA 커널 벤치마킹·검증·최적화 프레임워크. 진화적 탐색과 LLM 기반 코드 변형을 결합.

---

## 4. Sharon Zhou와 AMD의 전략적 위치

### 4.1 경력 배경
- Stanford에서 Andrew Ng 지도 하에 AI 박사 취득
- Stanford에서 50명 이상의 생성 AI 연구 그룹 주도
- Lamini 공동 창업 (VentureBeat Gen AI Startup Award, Forbes Cloud 100 Rising Star)
- 현재 AMD VP of AI

### 4.2 Lamini → AMD 합류의 의미
Lamini 시절부터 AMD GPU(ROCm)에서 LLM 파인튜닝·학습·추론을 성공적으로 구동. AMD의 ML 소프트웨어 스택이 "10% 완성"이라는 시장 인식과 달리 실제로는 ~90% 완성임을 입증. 이 경험을 AMD VP of AI로서 확대 적용 중.

### 4.3 NeurIPS 튜토리얼: "에이전트로 커널을 생성해 LLM 속도 높이기"

AMD, Stanford, Google DeepMind, Arm, NVIDIA, Meta, Modular, UC Irvine, MLCommons의 공동 협력으로 진행. 이 분야가 단일 기업의 독점이 아닌 **산업 전체의 공동 관심사**임을 시사.

### 4.4 AMD x GPU MODE 커널 경쟁 (2026년 3월)

- **Phase 1 예선**: 2026년 3월 6일~30일
- **최적화 대상 커널**: MXFP4 MoE, MLA Decode, MXFP4 GEMM
- **상금**: 최대 $100,000
- AMD가 커널 최적화 생태계를 적극적으로 육성하고 있음을 보여주는 사례

---

## 5. "인간 수준을 넘어선" 성능의 의미

### 무엇이 초인적인가

1. **속도**: 인간 엔지니어가 수주 걸리는 최적화를 수시간 만에 완료
2. **범위**: 480개 연산자-플랫폼 조합을 동시에 처리 (인간 팀으로는 불가능한 규모)
3. **성능**: 특정 워크로드에서 숙련된 엔지니어의 수작업 최적화보다 우수한 결과
4. **이식성**: 동일한 시스템이 NVIDIA, AMD, MTIA 등 이기종 하드웨어를 모두 커버

### 아직 인간이 필요한 영역

- 새로운 알고리즘적 돌파구 설계 (AI는 기존 패턴의 조합·변형에 강함)
- 프로덕션 환경의 가변 조건 대응 (테스트 케이스에 과적합되는 문제 잔존)
- 하드웨어-소프트웨어 공동 설계의 상위 수준 의사결정
- cuDNN과 같이 이미 고도로 최적화된 벤더 라이브러리 수준 도달은 여전히 도전적

---

## 6. 파급효과: GPU 최적화 → 파운데이션 모델 가속의 선순환

```
┌─────────────────────────────────────────────────┐
│                  선순환 구조                       │
│                                                   │
│   더 강력한 AI 모델                                │
│        │                                          │
│        ▼                                          │
│   더 나은 GPU 커널 자동 최적화                      │
│        │                                          │
│        ▼                                          │
│   GPU 연산 효율 향상 (최대 17×)                     │
│        │                                          │
│        ▼                                          │
│   동일 비용으로 더 많은 연산량 확보                   │
│        │                                          │
│        ▼                                          │
│   파운데이션 모델 학습 가속                          │
│        │                                          │
│        ▼                                          │
│   더 강력한 AI 모델 (반복)                          │
└─────────────────────────────────────────────────┘
```

이 선순환이 의미하는 것:

1. **GPU 세대 전환 자동화**: 새 GPU(예: NVIDIA B200, AMD MI400)가 출시되면, AI가 즉시 해당 아키텍처에 맞는 커널을 자동 생성. 몇 달 걸리던 마이그레이션이 수일 이내로.
2. **하드웨어 민주화**: NVIDIA 독점 구조에서 AMD, 커스텀 가속기(Meta MTIA, Google TPU 등)로의 전환이 용이해짐. 커널 작성이 병목이 아니게 되면 하드웨어 선택의 자유도 증가.
3. **AI 개발 가속**: 연산 효율이 높아지면 같은 예산으로 더 큰 모델을 더 빨리 학습할 수 있어, 다음 세대 파운데이션 모델 개발 주기가 단축.
4. **비용 절감**: Meta의 사례처럼 수십억 사용자 서비스에서 커널 최적화로 인한 에너지·비용 절감 효과는 천문학적.

---

## 7. 2026년 1월 종합 서베이의 핵심 트렌드

BAAI(Beijing Academy of AI) 연구자들의 조사에 따르면:

- **단순 코드 합성 → 정교한 에이전틱 AI 시스템**으로 전환 중
- 진화적 탐색, 검색 증강 메모리, 세밀한 하드웨어 프로파일링, 멀티 에이전트 협업을 결합
- LLM이 하드웨어 사양에 관한 **전문가 수준의 지식을 압축**하고, 에이전트가 반복적 개선을 통해 비정규 최적화 공간을 탐색

---

## 8. 남은 과제

| 과제 | 설명 |
|------|------|
| **프로덕션 일반화** | 좁은 테스트 케이스에 최적화된 솔루션이 실제 ML 파이프라인의 가변 조건에서 실패할 수 있음 |
| **정확성 검증** | 수치적 정확성 보장이 안전성·신뢰성의 핵심 (특히 금융, 의료 AI) |
| **성숙한 벤더 라이브러리 대비 경쟁력** | cuDNN 등 고도로 최적화된 기존 라이브러리 수준 도달은 여전히 도전적 |
| **도메인 전문성 의존** | Triton 등 상위 추상화를 사용해도 경쟁력 있는 성능 달성에는 상당한 도메인 지식 필요 |

---

## 9. 결론

AI가 GPU 커널을 자동 최적화하는 것은 단순한 기술 데모가 아니라, **이미 Meta에서 수십억 사용자에게 서비스하는 프로덕션 환경에 배포된 현실**이다. Sharon Zhou가 강조하듯, 이는 GPU 세대 전환의 자동화, 하드웨어 생태계의 민주화, 그리고 AI 개발 자체의 가속이라는 세 가지 축에서 근본적인 변화를 예고한다.

특히 "AI가 더 나은 AI를 만든다"는 선순환 구조가 현실화되면서, GPU 커널 최적화는 AI 발전의 **숨겨진 가속 페달** 역할을 하고 있다.

---

## 참고 자료

- [KernelEvolve: Scaling Agentic Kernel Coding for Heterogeneous AI Accelerators at Meta](https://arxiv.org/abs/2512.23236)
- [PEAK: A Performance Engineering AI-Assistant for GPU Kernels](https://arxiv.org/html/2512.19018v1)
- [Towards Robust Agentic CUDA Kernel Benchmarking, Verification, and Optimization (Sakana AI)](https://sakana.ai/ai-cuda-engineer/)
- [Automating GPU Kernel Generation with DeepSeek-R1 — NVIDIA Technical Blog](https://developer.nvidia.com/blog/automating-gpu-kernel-generation-with-deepseek-r1-and-inference-time-scaling/)
- [Towards Automated Kernel Generation in the Era of LLMs](https://arxiv.org/pdf/2601.15727)
- [Astra: A Multi-Agent System for GPU Kernel Performance Optimization (Stanford)](https://cs.stanford.edu/~anjiang/papers/Astra.pdf)
- [Sharon Zhou NeurIPS Tutorial: How to Build Agents to Generate Kernels for Faster LLMs](https://x.com/realSharonZhou/status/1995863023769039069)
- [Eye on AI Podcast #324 — Sharon Zhou: Inside AMD's Plan to Build Self-Improving AI](https://open.spotify.com/episode/7b0k7noiHmy8EAoxUH4NQ7)
- [GPU Kernel Scientist: An LLM-Driven Framework for Iterative Kernel Optimization](https://arxiv.org/html/2506.20807v2)
- [SwizzlePerf: Hardware-Aware LLMs for GPU Kernel Performance Optimization](https://www.arxiv.org/pdf/2508.20258)
