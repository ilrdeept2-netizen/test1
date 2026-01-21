#!/usr/bin/env python3
"""
AI 생활 자동화 에이전트 데모
============================
Matt Schlicht의 AgentWealth, AgentHealth, AgentHome 컨셉을
한국 상황에 맞게 구현한 에이전트 시스템 데모입니다.

사용법:
    python ai_life_agents_demo.py
"""

import asyncio
from datetime import datetime, timedelta, date
from decimal import Decimal

from ai_life_agents import (
    AgentCoordinator,
    AgentFinance,
    AgentHealth,
    AgentHome,
    AgentTime,
    AgentSocial
)
from ai_life_agents.agents.finance_agent import Account, Bill, Investment
from ai_life_agents.agents.health_agent import Medication, VitalType
from ai_life_agents.agents.home_agent import SmartDevice, DeviceType, UtilityBill
from ai_life_agents.agents.time_agent import TodoPriority
from ai_life_agents.agents.social_agent import Contact, RelationType, EventCategory


def print_section(title: str):
    """섹션 출력"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


async def demo_finance_agent():
    """재정 에이전트 데모"""
    print_section("💰 AgentFinance - 재정/자산 관리")

    agent = AgentFinance()
    await agent.initialize()

    # 계좌 추가
    agent.add_account(Account(
        id="checking_1",
        name="주거래 계좌",
        bank="카카오뱅크",
        account_type="checking",
        balance=Decimal("3500000")
    ))

    agent.add_account(Account(
        id="savings_1",
        name="비상금 계좌",
        bank="토스뱅크",
        account_type="savings",
        balance=Decimal("15000000")
    ))

    print(f"✅ 총 잔액: {agent.get_total_balance():,}원")
    print(f"✅ 순자산: {agent.get_net_worth():,}원")

    # 청구서 추가
    agent.add_bill(Bill(
        id="bill_1",
        name="통신비",
        amount=Decimal("55000"),
        due_date=datetime.now() + timedelta(days=5),
        category="utilities",
        auto_pay=True
    ))

    # DCA 설정
    agent.setup_dca("TIGER S&P500", Decimal("500000"), "monthly", 25)
    agent.setup_dca("삼성전자", Decimal("300000"), "monthly", 25)
    print("✅ 적립식 투자 설정 완료")

    # 지출 분석 (시뮬레이션)
    print("\n📊 재정 현황:")
    status = agent.get_status()
    print(f"   - 상태: {status['status']}")
    print(f"   - 기능: {', '.join(status['capabilities'][:5])}...")

    # 절약 기회 찾기
    savings = await agent._find_savings({})
    print(f"\n💡 절약 기회: {len(savings['opportunities'])}건 발견")
    for opp in savings['opportunities'][:3]:
        print(f"   - {opp['description']}")


async def demo_health_agent():
    """건강 에이전트 데모"""
    print_section("❤️ AgentHealth - 건강/의료 관리")

    agent = AgentHealth()
    await agent.initialize()

    # 프로필 설정
    agent.profile.update({
        "birth_year": 1990,
        "gender": "male",
        "height_cm": 175,
        "blood_type": "A+"
    })

    # 바이탈 기록
    await agent._record_vital({
        "type": "heart_rate",
        "value": 72,
        "unit": "bpm",
        "source": "apple_watch"
    })

    await agent._record_vital({
        "type": "steps",
        "value": 8500,
        "unit": "steps",
        "source": "apple_watch"
    })

    print("✅ 바이탈 기록 완료")

    # 복약 추가
    agent.add_medication(Medication(
        id="med_1",
        name="비타민D",
        dosage="1000IU",
        frequency="daily",
        times=["09:00"],
        pharmacy="올리브영"
    ))
    print("✅ 복약 정보 등록 완료")

    # 건강검진 일정 확인
    checkups = await agent._check_checkup_schedule({})
    print(f"\n🏥 건강검진 대상: {checkups['total_due']}건")
    for checkup in checkups['checkups_due'][:3]:
        print(f"   - {checkup['type']}: {checkup['description']}")

    # 영양 분석
    await agent._log_meal({
        "meal_type": "lunch",
        "calories": 750,
        "protein": 30,
        "carbs": 100,
        "fat": 25
    })
    print("\n🍽️ 식사 기록 완료")


async def demo_home_agent():
    """주거 에이전트 데모"""
    print_section("🏠 AgentHome - 주거/가정 관리")

    agent = AgentHome()
    await agent.initialize()

    # 집 정보 설정
    agent.home_profile.update({
        "type": "apartment",
        "size_sqm": 84,
        "floor": 15,
        "lease_type": "jeonse"
    })

    # 스마트 기기 등록
    agent.register_device(SmartDevice(
        id="light_living",
        name="거실 조명",
        device_type=DeviceType.LIGHT,
        location="living_room",
        current_state={"power": True, "brightness": 80}
    ))

    agent.register_device(SmartDevice(
        id="thermostat_main",
        name="메인 온도조절기",
        device_type=DeviceType.THERMOSTAT,
        location="living_room",
        current_state={"temperature": 24}
    ))

    agent.register_device(SmartDevice(
        id="robot_vacuum",
        name="로봇청소기",
        device_type=DeviceType.ROBOT_VACUUM,
        location="living_room",
        current_state={"power": False}
    ))

    print(f"✅ 스마트 기기 {len(agent.smart_devices)}개 등록")

    # 공과금 등록
    agent.add_utility_bill(UtilityBill(
        id="elec_202401",
        utility_type="electricity",
        amount=Decimal("85000"),
        usage=350,
        usage_unit="kWh",
        billing_period="2024-01",
        due_date=date.today() + timedelta(days=10)
    ))

    # 홈 모드 설정
    result = await agent.set_home_mode("home")
    print(f"\n🏠 홈 모드: {result['mode']}")

    # 에너지 최적화
    optimization = await agent._optimize_energy({})
    print(f"⚡ 에너지 최적화: {len(optimization['optimizations_applied'])}건 적용")

    # 업체 찾기
    vendor = await agent._find_vendor({"service_type": "cleaning"})
    print(f"\n🧹 청소 업체 추천: {vendor['recommended_vendor']} (평점 {vendor['rating']})")


async def demo_time_agent():
    """시간 관리 에이전트 데모"""
    print_section("⏰ AgentTime - 시간/일정 관리")

    agent = AgentTime()
    await agent.initialize()

    # 일정 추가
    await agent._add_event({
        "title": "팀 미팅",
        "type": "meeting",
        "start_time": (datetime.now() + timedelta(hours=2)).isoformat(),
        "end_time": (datetime.now() + timedelta(hours=3)).isoformat(),
        "location": "회의실 A"
    })

    await agent._add_event({
        "title": "치과 예약",
        "type": "appointment",
        "start_time": (datetime.now() + timedelta(days=3, hours=14)).isoformat(),
        "end_time": (datetime.now() + timedelta(days=3, hours=15)).isoformat(),
        "location": "강남 치과"
    })

    print("✅ 일정 등록 완료")

    # 할 일 추가
    await agent._add_todo({
        "title": "프로젝트 기획서 작성",
        "priority": "urgent_important",
        "due_date": str(date.today() + timedelta(days=2)),
        "estimated_minutes": 120
    })

    await agent._add_todo({
        "title": "운동하기",
        "priority": "not_urgent_important",
        "estimated_minutes": 60
    })

    print("✅ 할 일 등록 완료")

    # 일일 계획
    plan = await agent._generate_daily_plan({"date": str(date.today())})
    print(f"\n📅 오늘의 계획 ({plan['day_of_week']}요일):")
    print(f"   - 일정: {len(plan['schedule'])}개")
    print(f"   - 오늘 마감 할 일: {len(plan['todos_due_today'])}개")
    print(f"   - 집중 가능 시간: {plan['focus_time_available']}분")

    # 빈 시간대 찾기
    free_slots = agent.find_free_slots(date.today(), 60)
    print(f"\n🕐 1시간 이상 빈 시간: {len(free_slots)}개")


async def demo_social_agent():
    """관계 관리 에이전트 데모"""
    print_section("👥 AgentSocial - 관계/사회생활 관리")

    agent = AgentSocial()
    await agent.initialize()

    # 연락처 추가
    await agent._add_contact({
        "name": "김철수",
        "relation": "friend",
        "phone": "010-1234-5678",
        "birthday": "1990-05-15",
        "tags": ["대학동기"]
    })

    await agent._add_contact({
        "name": "이영희",
        "relation": "colleague",
        "phone": "010-2345-6789",
        "company": "ABC 회사"
    })

    await agent._add_contact({
        "name": "부모님",
        "relation": "family",
        "phone": "010-3456-7890"
    })

    print(f"✅ 연락처 {len(agent.contacts)}명 등록")

    # 경조사 추가
    result = await agent._add_social_event({
        "contact_name": "김철수",
        "category": "wedding",
        "date": str(date.today() + timedelta(days=30)),
        "location": "강남 웨딩홀"
    })

    print("\n💒 경조사 등록 완료")
    print(f"   선물 추천 금액: {result['gift_suggestion']['recommended_amount']:,}원")

    # 명절 인사 준비
    greetings = await agent._prepare_holiday_greetings({"holiday": "설날"})
    print(f"\n🎊 설날 인사 대상: {greetings['total_contacts']}명")

    # 알림 체크
    reminders = await agent._check_reminders({})
    print(f"\n📢 알림:")
    print(f"   - 생일 알림: {len(reminders['birthdays'])}건")
    print(f"   - 경조사 알림: {len(reminders['events'])}건")
    print(f"   - 연락 필요: {len(reminders['contact_needed'])}명")


async def demo_coordinator():
    """코디네이터 데모 - 에이전트 간 협업"""
    print_section("🔄 AgentCoordinator - 에이전트 간 협업")

    # 코디네이터 생성
    coordinator = AgentCoordinator()

    # 모든 에이전트 등록
    finance = AgentFinance()
    health = AgentHealth()
    home = AgentHome()
    time_agent = AgentTime()
    social = AgentSocial()

    coordinator.register_agent(finance)
    coordinator.register_agent(health)
    coordinator.register_agent(home)
    coordinator.register_agent(time_agent)
    coordinator.register_agent(social)

    print(f"✅ {len(coordinator.agents)}개 에이전트 등록 완료")

    # 협업 규칙 추가
    coordinator.add_collaboration_rule(
        trigger_event="income_received",
        source_agent="finance",
        target_agent="finance",
        action="execute_dca",
        conditions={"amount": {"op": "gt", "value": 1000000}}
    )

    coordinator.add_collaboration_rule(
        trigger_event="health_checkup_due",
        source_agent="health",
        target_agent="time",
        action="add_event",
        conditions={}
    )

    coordinator.add_collaboration_rule(
        trigger_event="social_event_added",
        source_agent="social",
        target_agent="finance",
        action="budget_check",
        conditions={}
    )

    print(f"✅ 협업 규칙 {len(coordinator.collaboration_rules)}개 설정")

    # 시스템 상태
    status = coordinator.get_system_status()
    print(f"\n📊 시스템 상태:")
    print(f"   - 활성 에이전트: {status['agents_count']}개")
    print(f"   - 협업 규칙: {status['rules_count']}개")

    # 에이전트 목록
    print("\n🤖 등록된 에이전트:")
    for agent_status in status["agents"]:
        print(f"   - {agent_status['name']}: {agent_status['status']}")


async def demo_scenarios():
    """실제 사용 시나리오 데모"""
    print_section("📋 실제 사용 시나리오")

    print("""
╔══════════════════════════════════════════════════════════════╗
║                    🌟 사용 시나리오 예시 🌟                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1️⃣  급여일 자동 처리 (매월 25일)                              ║
║     ┌─────────────────────────────────────────────────────┐ ║
║     │ Finance: 급여 입금 감지                              │ ║
║     │    ↓                                                │ ║
║     │ Finance: 고정비 자동 이체 (월세, 보험 등)              │ ║
║     │    ↓                                                │ ║
║     │ Finance: 적립식 투자 실행 (S&P500, 삼성전자)           │ ║
║     │    ↓                                                │ ║
║     │ Home: 공과금 자동 납부                               │ ║
║     │    ↓                                                │ ║
║     │ Health: 보험료 납부 확인                             │ ║
║     └─────────────────────────────────────────────────────┘ ║
║                                                              ║
║  2️⃣  건강 이상 감지 시 대응                                   ║
║     ┌─────────────────────────────────────────────────────┐ ║
║     │ Health: 심박수 이상 감지 (150bpm)                    │ ║
║     │    ↓                                                │ ║
║     │ Health: 비상 연락처 알림                             │ ║
║     │    ↓                                                │ ║
║     │ Time: 오늘 일정 자동 조정                            │ ║
║     │    ↓                                                │ ║
║     │ Finance: 실손보험 청구 준비                          │ ║
║     └─────────────────────────────────────────────────────┘ ║
║                                                              ║
║  3️⃣  친구 결혼식 (경조사)                                     ║
║     ┌─────────────────────────────────────────────────────┐ ║
║     │ Social: 결혼식 일정 등록                             │ ║
║     │    ↓                                                │ ║
║     │ Social: 축의금 추천 (과거 내역 기반)                   │ ║
║     │    ↓                                                │ ║
║     │ Time: 캘린더에 일정 추가                             │ ║
║     │    ↓                                                │ ║
║     │ Finance: 경조사비 예산 반영                          │ ║
║     └─────────────────────────────────────────────────────┘ ║
║                                                              ║
║  4️⃣  외출 모드 활성화                                         ║
║     ┌─────────────────────────────────────────────────────┐ ║
║     │ Home: 외출 모드 설정                                 │ ║
║     │    ↓                                                │ ║
║     │ Home: 조명 끄기, 온도 낮추기                         │ ║
║     │    ↓                                                │ ║
║     │ Home: 보안 카메라 활성화                             │ ║
║     │    ↓                                                │ ║
║     │ Finance: 에너지 절약 예상 금액 계산                   │ ║
║     └─────────────────────────────────────────────────────┘ ║
║                                                              ║
║  5️⃣  월간 종합 리뷰 (매월 1일)                                ║
║     ┌─────────────────────────────────────────────────────┐ ║
║     │ Coordinator: 모든 에이전트에 월간 리포트 요청          │ ║
║     │    ↓                                                │ ║
║     │ Finance: 지출 분석, 투자 성과                        │ ║
║     │ Health: 건강 지표 트렌드                             │ ║
║     │ Home: 공과금 분석, 에너지 사용                       │ ║
║     │ Time: 생산성 분석                                   │ ║
║     │ Social: 경조사 지출, 관계 현황                       │ ║
║     │    ↓                                                │ ║
║     │ Coordinator: 종합 리포트 생성                        │ ║
║     └─────────────────────────────────────────────────────┘ ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


async def main():
    """메인 데모"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🤖 AI 생활 자동화 에이전트 시스템 🤖                         ║
║                                                              ║
║     Matt Schlicht의 AgentWealth, AgentHealth, AgentHome      ║
║     컨셉을 한국 상황에 맞게 구현한 에이전트 프레임워크입니다.       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    # 각 에이전트 데모 실행
    await demo_finance_agent()
    await demo_health_agent()
    await demo_home_agent()
    await demo_time_agent()
    await demo_social_agent()
    await demo_coordinator()
    await demo_scenarios()

    print_section("✨ 데모 완료")
    print("""
🎯 이 시스템의 핵심 가치:
   1. 자동화: 반복적인 생활 관리 업무 자동 처리
   2. 통합: 5개 에이전트가 유기적으로 협업
   3. 맞춤형: 한국 서비스 및 문화에 최적화
   4. 확장성: 새로운 에이전트/기능 쉽게 추가 가능

📚 자세한 사용법은 README_AGENTS.md를 참조하세요.
""")


if __name__ == "__main__":
    asyncio.run(main())
