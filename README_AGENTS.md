# AI 생활 자동화 에이전트 시스템

Matt Schlicht의 AgentWealth, AgentHealth, AgentHome 컨셉을 기반으로 한국 상황에 맞게 설계된 AI 생활 자동화 에이전트 프레임워크입니다.

## 개요

이 시스템은 5개의 전문 에이전트가 실시간으로 소통하며 삶의 다양한 영역을 자동화합니다:

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentCoordinator                         │
│              (에이전트 간 통신 및 협업 관리)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Finance  │  │  Health  │  │   Home   │                  │
│  │  재정관리  │  │  건강관리  │  │  주거관리  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│                                                             │
│  ┌──────────┐  ┌──────────┐                                │
│  │   Time   │  │  Social  │                                │
│  │  시간관리  │  │  관계관리  │                                │
│  └──────────┘  └──────────┘                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 에이전트 소개

### 💰 AgentFinance (재정 관리)
- 계좌/자산 관리
- 청구서 자동 납부
- 적립식 투자 (DCA)
- 지출 분석 및 예산 관리
- 카드 혜택 최적화
- 구독 서비스 관리
- 연말정산 준비

**한국 맞춤 기능:**
- 토스/카카오뱅크 연동
- 국민연금/건강보험료 추적
- 주식/ETF 자동 투자

### ❤️ AgentHealth (건강 관리)
- 바이탈 모니터링 (심박수, 혈압, 체중 등)
- 식단 관리 및 영양 분석
- 복약 알림
- 건강검진 예약 관리
- 운동 트래킹
- 수면 분석

**한국 맞춤 기능:**
- 국민건강보험 건강검진 알림
- 실손보험 청구 자동화
- 네이버 예약/똑닥 연동

### 🏠 AgentHome (주거 관리)
- 공과금 자동 납부
- 스마트홈 제어
- 유지보수 스케줄링
- 보안 모니터링
- 에너지 최적화
- 생필품 자동 주문

**한국 맞춤 기능:**
- 아파트 관리비 분석
- 한국전력/도시가스 연동
- 숨고/당근마켓 업체 연결
- 삼성 SmartThings/LG ThinQ 연동

### ⏰ AgentTime (시간 관리)
- 일정 관리 및 최적화
- 할 일 목록 관리 (GTD/아이젠하워 매트릭스)
- 집중 세션 (포모도로)
- 습관 트래킹
- 생산성 분석

**한국 맞춤 기능:**
- 카카오/네이버 캘린더 연동
- 한국 공휴일 자동 반영
- KTX/SRT 예약 시간 최적화

### 👥 AgentSocial (관계 관리)
- 경조사 관리 (결혼식, 장례식 등)
- 축의금/조의금 추적
- 기념일 알림
- 선물 추천
- 모임 조율
- 관계 유지 리마인더

**한국 맞춤 기능:**
- 경조사비 상호성 추적
- 명절 인사 관리
- 카카오페이 송금 연동

## 설치 및 실행

### 요구사항
- Python 3.8+
- asyncio 지원

### 설치
```bash
cd ai_life_agents
pip install -e .
```

### 데모 실행
```bash
python ai_life_agents_demo.py
```

## 사용 예시

### 기본 사용
```python
import asyncio
from ai_life_agents import (
    AgentCoordinator,
    AgentFinance,
    AgentHealth,
    AgentHome
)

async def main():
    # 코디네이터 생성
    coordinator = AgentCoordinator()

    # 에이전트 생성 및 등록
    finance = AgentFinance()
    health = AgentHealth()
    home = AgentHome()

    coordinator.register_agent(finance)
    coordinator.register_agent(health)
    coordinator.register_agent(home)

    # 에이전트 초기화
    await finance.initialize()
    await health.initialize()
    await home.initialize()

    # 재정 에이전트 사용
    from ai_life_agents.agents.finance_agent import Account
    from decimal import Decimal

    finance.add_account(Account(
        id="main",
        name="주거래 계좌",
        bank="카카오뱅크",
        account_type="checking",
        balance=Decimal("5000000")
    ))

    # 지출 분석
    analysis = await finance._analyze_spending({"period": 30})
    print(f"이번 달 지출: {analysis['total_spending']:,}원")

asyncio.run(main())
```

### 에이전트 간 협업 설정
```python
# 협업 규칙 추가
coordinator.add_collaboration_rule(
    trigger_event="income_received",      # 급여 입금 시
    source_agent="finance",
    target_agent="finance",
    action="execute_dca",                  # 적립식 투자 실행
    conditions={"amount": {"op": "gt", "value": 1000000}}
)

coordinator.add_collaboration_rule(
    trigger_event="social_event_added",   # 경조사 등록 시
    source_agent="social",
    target_agent="finance",
    action="budget_check",                 # 예산 확인
    conditions={}
)
```

## 협업 시나리오

### 1. 급여일 자동 처리
```
Finance: 급여 입금 감지
    ↓
Finance: 고정비 자동 이체
    ↓
Finance: 적립식 투자 실행
    ↓
Home: 공과금 자동 납부
```

### 2. 건강 이상 대응
```
Health: 바이탈 이상 감지
    ↓
Health: 비상 연락처 알림
    ↓
Time: 일정 자동 조정
    ↓
Finance: 보험 청구 준비
```

### 3. 경조사 처리
```
Social: 결혼식 일정 등록
    ↓
Social: 축의금 추천
    ↓
Time: 캘린더 추가
    ↓
Finance: 예산 반영
```

## 아키텍처

```
ai_life_agents/
├── __init__.py              # 패키지 초기화
├── base_agent.py            # 기본 에이전트 클래스
├── coordinator.py           # 에이전트 코디네이터
└── agents/
    ├── __init__.py
    ├── finance_agent.py     # 재정 에이전트
    ├── health_agent.py      # 건강 에이전트
    ├── home_agent.py        # 주거 에이전트
    ├── time_agent.py        # 시간 에이전트
    └── social_agent.py      # 관계 에이전트
```

## 확장 방법

### 새로운 에이전트 추가
```python
from ai_life_agents.base_agent import BaseAgent, Task

class AgentTravel(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="travel",
            name="AgentTravel",
            description="여행 관리 에이전트"
        )

    async def initialize(self) -> bool:
        # 초기화 로직
        return True

    async def process_task(self, task: Task):
        # 작업 처리 로직
        pass

    def get_capabilities(self) -> list:
        return ["flight_booking", "hotel_search", "itinerary_planning"]
```

## 향후 계획

- [ ] 실제 API 연동 (토스, 카카오, 네이버 등)
- [ ] 머신러닝 기반 예측 모델
- [ ] 음성 인터페이스 (스마트 스피커)
- [ ] 모바일 앱 연동
- [ ] 더 많은 협업 시나리오

## 라이선스

MIT License

## 참고

- [Matt Schlicht의 AI 에이전트 사례](https://twitter.com/mattschlicht)
- AgentWealth, AgentHealth, AgentHome 컨셉 참조
