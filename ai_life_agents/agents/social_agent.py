"""
AgentSocial - 관계 관리 에이전트

기능:
- 경조사 관리
- 기념일 알림
- 연락처 관리
- 선물 추천
- 모임 조율
- 관계 유지 리마인더
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import asyncio

from ..base_agent import BaseAgent, Task, Message, Priority


class RelationType(Enum):
    FAMILY = "family"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    BUSINESS = "business"
    ACQUAINTANCE = "acquaintance"


class EventCategory(Enum):
    WEDDING = "wedding"
    FUNERAL = "funeral"
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    GRADUATION = "graduation"
    PROMOTION = "promotion"
    HOUSEWARMING = "housewarming"
    BABY_SHOWER = "baby_shower"
    HOLIDAY = "holiday"


@dataclass
class Contact:
    """연락처"""
    id: str
    name: str
    relation_type: RelationType
    phone: str = ""
    email: str = ""
    birthday: Optional[date] = None
    anniversary: Optional[date] = None
    company: str = ""
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    last_contact: Optional[datetime] = None
    contact_frequency_days: int = 30  # 연락 권장 주기


@dataclass
class SocialEvent:
    """경조사/이벤트"""
    id: str
    contact_id: str
    contact_name: str
    category: EventCategory
    event_date: date
    location: str = ""
    gift_amount: int = 0  # 축의금/조의금
    gift_item: str = ""   # 선물
    notes: str = ""
    attended: bool = False
    rsvp_required: bool = False
    rsvp_deadline: Optional[date] = None


@dataclass
class Gathering:
    """모임"""
    id: str
    name: str
    participants: List[str] = field(default_factory=list)
    proposed_dates: List[datetime] = field(default_factory=list)
    confirmed_date: Optional[datetime] = None
    location: str = ""
    budget_per_person: int = 0
    organizer: str = ""
    status: str = "planning"  # planning, confirmed, completed, cancelled


@dataclass
class GiftIdea:
    """선물 아이디어"""
    id: str
    name: str
    category: str
    price_range: tuple  # (min, max)
    suitable_for: List[EventCategory] = field(default_factory=list)
    suitable_relations: List[RelationType] = field(default_factory=list)
    link: str = ""
    notes: str = ""


class AgentSocial(BaseAgent):
    """
    관계 관리 에이전트

    한국 맞춤 기능:
    - 경조사비 관리 (축의금, 조의금)
    - 명절 인사 관리
    - 동창회/동호회 모임 조율
    - 카카오톡 연동 (알림)
    - 네이버 페이/카카오페이 송금
    """

    def __init__(self, agent_id: str = "social"):
        super().__init__(
            agent_id=agent_id,
            name="AgentSocial",
            description="관계 및 사회 생활 관리 에이전트"
        )

        # 데이터 저장소
        self.contacts: Dict[str, Contact] = {}
        self.events: Dict[str, SocialEvent] = {}
        self.gatherings: Dict[str, Gathering] = {}
        self.gift_ideas: List[GiftIdea] = []

        # 경조사 히스토리
        self.gift_history: List[Dict[str, Any]] = []

        # 설정
        self.config = {
            "birthday_reminder_days": 7,
            "event_reminder_days": 3,
            "contact_reminder_enabled": True,
            "default_wedding_gift": 50000,
            "default_funeral_gift": 50000,
            "gift_tracking_enabled": True
        }

        # 한국 명절
        self.korean_holidays = {
            "설날": ["2024-02-10", "2025-01-29"],
            "추석": ["2024-09-17", "2025-10-06"],
            "어버이날": ["2024-05-08", "2025-05-08"],
            "스승의날": ["2024-05-15", "2025-05-15"]
        }

        # 기본 선물 아이디어
        self._init_gift_ideas()

    def _init_gift_ideas(self):
        """기본 선물 아이디어 초기화"""
        self.gift_ideas = [
            GiftIdea(
                id="gift_1", name="백화점 상품권", category="상품권",
                price_range=(50000, 200000),
                suitable_for=[EventCategory.WEDDING, EventCategory.HOUSEWARMING],
                suitable_relations=[RelationType.FRIEND, RelationType.COLLEAGUE]
            ),
            GiftIdea(
                id="gift_2", name="과일 바구니", category="식품",
                price_range=(50000, 100000),
                suitable_for=[EventCategory.HOUSEWARMING],
                suitable_relations=[RelationType.FAMILY, RelationType.FRIEND]
            ),
            GiftIdea(
                id="gift_3", name="건강식품 세트", category="건강",
                price_range=(50000, 150000),
                suitable_for=[EventCategory.BIRTHDAY],
                suitable_relations=[RelationType.FAMILY]
            ),
            GiftIdea(
                id="gift_4", name="육아용품", category="육아",
                price_range=(30000, 100000),
                suitable_for=[EventCategory.BABY_SHOWER],
                suitable_relations=[RelationType.FRIEND, RelationType.COLLEAGUE]
            ),
            GiftIdea(
                id="gift_5", name="와인 세트", category="주류",
                price_range=(50000, 150000),
                suitable_for=[EventCategory.HOUSEWARMING, EventCategory.PROMOTION],
                suitable_relations=[RelationType.FRIEND, RelationType.COLLEAGUE]
            ),
        ]

    async def initialize(self) -> bool:
        """초기화"""
        self.logger.info("관계 관리 에이전트 초기화 중...")

        # 이벤트 핸들러 등록
        self.on("contact_reminder", self._on_contact_reminder)
        self.on("event_reminder", self._on_event_reminder)

        # 스케줄러 시작
        await self._schedule_social_tasks()

        return True

    def get_capabilities(self) -> List[str]:
        """기능 목록"""
        return [
            "contact_management",     # 연락처 관리
            "event_tracking",        # 경조사 관리
            "gift_management",       # 선물/축의금 관리
            "gathering_coordination", # 모임 조율
            "relationship_reminders", # 관계 유지 알림
            "holiday_greetings",     # 명절 인사
            "gift_recommendations",  # 선물 추천
            "social_analytics",      # 관계 분석
            "rsvp_management",       # 참석 관리
            "social_report"         # 사회생활 리포트
        ]

    async def process_task(self, task: Task) -> Any:
        """작업 처리"""
        task_handlers = {
            "add_contact": self._add_contact,
            "add_event": self._add_social_event,
            "recommend_gift": self._recommend_gift,
            "record_gift": self._record_gift,
            "plan_gathering": self._plan_gathering,
            "check_reminders": self._check_reminders,
            "holiday_greetings": self._prepare_holiday_greetings,
            "monthly_report": self._generate_monthly_report
        }

        handler = task_handlers.get(task.name)
        if handler:
            return await handler(task.metadata)
        else:
            self.logger.warning(f"알 수 없는 작업: {task.name}")
            return None

    async def handle_request(self, message: Message) -> Optional[Message]:
        """요청 처리"""
        handlers = {
            "get_upcoming_events": self._handle_upcoming_events,
            "get_gift_history": self._handle_gift_history,
            "monthly_report": self._handle_monthly_report,
            "contact_suggestions": self._handle_contact_suggestions
        }

        handler = handlers.get(message.subject)
        if handler:
            result = await handler(message.content)
            return Message(
                sender=self.agent_id,
                receiver=message.sender,
                message_type="response",
                subject=f"{message.subject}_response",
                content=result
            )
        return None

    # ========== 연락처 관리 ==========

    async def _add_contact(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """연락처 추가"""
        contact = Contact(
            id=f"contact_{datetime.now().timestamp()}",
            name=metadata.get("name", ""),
            relation_type=RelationType(metadata.get("relation", "friend")),
            phone=metadata.get("phone", ""),
            email=metadata.get("email", ""),
            birthday=date.fromisoformat(metadata["birthday"]) if metadata.get("birthday") else None,
            company=metadata.get("company", ""),
            tags=metadata.get("tags", [])
        )

        self.contacts[contact.id] = contact
        self.logger.info(f"연락처 추가: {contact.name} ({contact.relation_type.value})")

        return {
            "added": True,
            "contact_id": contact.id,
            "name": contact.name
        }

    def get_contacts_by_relation(self, relation: RelationType) -> List[Contact]:
        """관계별 연락처 조회"""
        return [c for c in self.contacts.values() if c.relation_type == relation]

    def get_contacts_needing_contact(self) -> List[Contact]:
        """연락이 필요한 사람들"""
        needs_contact = []
        now = datetime.now()

        for contact in self.contacts.values():
            if contact.last_contact:
                days_since = (now - contact.last_contact).days
                if days_since >= contact.contact_frequency_days:
                    needs_contact.append({
                        "contact": contact,
                        "days_since": days_since,
                        "overdue_days": days_since - contact.contact_frequency_days
                    })

        return sorted(needs_contact, key=lambda x: x["overdue_days"], reverse=True)

    # ========== 경조사 관리 ==========

    async def _add_social_event(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """경조사 추가"""
        event = SocialEvent(
            id=f"social_{datetime.now().timestamp()}",
            contact_id=metadata.get("contact_id", ""),
            contact_name=metadata.get("contact_name", ""),
            category=EventCategory(metadata.get("category")),
            event_date=date.fromisoformat(metadata.get("date")),
            location=metadata.get("location", ""),
            rsvp_required=metadata.get("rsvp_required", False),
            rsvp_deadline=date.fromisoformat(metadata["rsvp_deadline"]) if metadata.get("rsvp_deadline") else None
        )

        self.events[event.id] = event
        self.logger.info(
            f"경조사 추가: {event.contact_name} {event.category.value} "
            f"({event.event_date})"
        )

        # 선물/축의금 추천
        gift_suggestion = await self._recommend_gift({
            "category": event.category.value,
            "contact_name": event.contact_name
        })

        # 일정 에이전트에 알림
        await self.send_message(
            "time",
            "social_event_added",
            {
                "title": f"{event.contact_name} {self._get_event_name(event.category)}",
                "date": str(event.event_date),
                "location": event.location
            }
        )

        # 재정 에이전트에 예상 비용 알림
        await self.send_message(
            "finance",
            "social_expense_expected",
            {
                "event": f"{event.contact_name} {self._get_event_name(event.category)}",
                "date": str(event.event_date),
                "estimated_amount": gift_suggestion.get("recommended_amount", 50000)
            }
        )

        return {
            "added": True,
            "event_id": event.id,
            "gift_suggestion": gift_suggestion
        }

    def _get_event_name(self, category: EventCategory) -> str:
        """이벤트 카테고리 한글명"""
        names = {
            EventCategory.WEDDING: "결혼식",
            EventCategory.FUNERAL: "장례식",
            EventCategory.BIRTHDAY: "생일",
            EventCategory.ANNIVERSARY: "기념일",
            EventCategory.GRADUATION: "졸업식",
            EventCategory.PROMOTION: "승진",
            EventCategory.HOUSEWARMING: "집들이",
            EventCategory.BABY_SHOWER: "출산",
            EventCategory.HOLIDAY: "명절"
        }
        return names.get(category, category.value)

    def get_upcoming_events(self, days: int = 30) -> List[SocialEvent]:
        """예정된 경조사"""
        cutoff = date.today() + timedelta(days=days)
        upcoming = [
            e for e in self.events.values()
            if date.today() <= e.event_date <= cutoff
        ]
        return sorted(upcoming, key=lambda e: e.event_date)

    # ========== 선물/축의금 관리 ==========

    async def _recommend_gift(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """선물/축의금 추천"""
        category = EventCategory(metadata.get("category"))
        contact_name = metadata.get("contact_name", "")

        # 관계 정보 찾기
        contact = next(
            (c for c in self.contacts.values() if c.name == contact_name),
            None
        )

        relation = contact.relation_type if contact else RelationType.FRIEND

        # 과거 선물 내역 확인 (상호성)
        received_from = [
            g for g in self.gift_history
            if g.get("from") == contact_name
        ]
        total_received = sum(g.get("amount", 0) for g in received_from)

        # 기본 금액 설정
        base_amounts = {
            EventCategory.WEDDING: {
                RelationType.FAMILY: 100000,
                RelationType.FRIEND: 50000,
                RelationType.COLLEAGUE: 50000,
                RelationType.BUSINESS: 100000,
                RelationType.ACQUAINTANCE: 30000
            },
            EventCategory.FUNERAL: {
                RelationType.FAMILY: 100000,
                RelationType.FRIEND: 50000,
                RelationType.COLLEAGUE: 50000,
                RelationType.BUSINESS: 100000,
                RelationType.ACQUAINTANCE: 30000
            },
            EventCategory.BIRTHDAY: {
                RelationType.FAMILY: 50000,
                RelationType.FRIEND: 30000,
                RelationType.COLLEAGUE: 20000
            },
            EventCategory.HOUSEWARMING: {
                RelationType.FAMILY: 50000,
                RelationType.FRIEND: 30000,
                RelationType.COLLEAGUE: 30000
            },
            EventCategory.BABY_SHOWER: {
                RelationType.FAMILY: 50000,
                RelationType.FRIEND: 30000,
                RelationType.COLLEAGUE: 30000
            }
        }

        base_amount = base_amounts.get(category, {}).get(relation, 50000)

        # 상호성 조정
        if total_received > base_amount:
            recommended_amount = min(total_received, base_amount * 2)
        else:
            recommended_amount = base_amount

        # 선물 아이디어
        suitable_gifts = [
            g for g in self.gift_ideas
            if category in g.suitable_for and relation in g.suitable_relations
        ]

        return {
            "event_type": category.value,
            "relation": relation.value,
            "recommended_amount": recommended_amount,
            "received_history": total_received,
            "gift_ideas": [
                {
                    "name": g.name,
                    "category": g.category,
                    "price_range": g.price_range
                }
                for g in suitable_gifts[:3]
            ],
            "notes": self._get_gift_etiquette(category)
        }

    def _get_gift_etiquette(self, category: EventCategory) -> str:
        """경조사 예절 안내"""
        etiquette = {
            EventCategory.WEDDING: "축의금은 홀수로 (3, 5, 7, 10만원). 흰 봉투 사용.",
            EventCategory.FUNERAL: "조의금은 홀수로. 검정 봉투 또는 흰 봉투 사용.",
            EventCategory.BIRTHDAY: "케이크와 함께 선물하면 좋습니다.",
            EventCategory.HOUSEWARMING: "휴지, 세제 등 생활용품이 전통적. 현금도 환영.",
            EventCategory.BABY_SHOWER: "실용적인 육아용품이 좋습니다."
        }
        return etiquette.get(category, "")

    async def _record_gift(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """선물/축의금 기록"""
        record = {
            "id": f"gift_{datetime.now().timestamp()}",
            "event_id": metadata.get("event_id"),
            "direction": metadata.get("direction", "given"),  # given or received
            "to": metadata.get("to"),
            "from": metadata.get("from"),
            "amount": metadata.get("amount", 0),
            "item": metadata.get("item", ""),
            "category": metadata.get("category"),
            "date": str(date.today()),
            "notes": metadata.get("notes", "")
        }

        self.gift_history.append(record)
        self.logger.info(
            f"경조사 기록: {record['direction']} {record['amount']:,}원 "
            f"({record.get('to') or record.get('from')})"
        )

        # 재정 에이전트에 지출 알림
        if record["direction"] == "given":
            await self.send_message(
                "finance",
                "social_expense",
                {
                    "category": "경조사비",
                    "amount": record["amount"],
                    "recipient": record["to"],
                    "event_type": record["category"]
                }
            )

        return {"recorded": True, "record": record}

    def get_gift_balance(self, contact_name: str) -> Dict[str, Any]:
        """특정 인물과의 경조사 주고받기 현황"""
        given = sum(
            g["amount"] for g in self.gift_history
            if g.get("to") == contact_name and g["direction"] == "given"
        )
        received = sum(
            g["amount"] for g in self.gift_history
            if g.get("from") == contact_name and g["direction"] == "received"
        )

        return {
            "contact": contact_name,
            "total_given": given,
            "total_received": received,
            "balance": received - given,
            "relationship_status": (
                "균형" if abs(received - given) < 50000
                else "받은 것이 많음" if received > given
                else "준 것이 많음"
            )
        }

    # ========== 모임 조율 ==========

    async def _plan_gathering(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """모임 계획"""
        gathering = Gathering(
            id=f"gathering_{datetime.now().timestamp()}",
            name=metadata.get("name", "모임"),
            participants=metadata.get("participants", []),
            organizer=metadata.get("organizer", ""),
            budget_per_person=metadata.get("budget", 30000)
        )

        # 제안 일정 추가
        if metadata.get("proposed_dates"):
            gathering.proposed_dates = [
                datetime.fromisoformat(d) for d in metadata["proposed_dates"]
            ]

        self.gatherings[gathering.id] = gathering
        self.logger.info(f"모임 계획: {gathering.name} ({len(gathering.participants)}명)")

        # 일정 에이전트에 가용 시간 확인 요청
        if gathering.proposed_dates:
            await self.send_message(
                "time",
                "check_availability",
                {
                    "dates": [d.isoformat() for d in gathering.proposed_dates],
                    "reason": gathering.name
                }
            )

        return {
            "created": True,
            "gathering_id": gathering.id,
            "participants": len(gathering.participants),
            "proposed_dates": [d.isoformat() for d in gathering.proposed_dates]
        }

    def find_common_available_date(self, gathering_id: str,
                                   responses: Dict[str, List[datetime]]) -> Optional[datetime]:
        """공통 가능 일정 찾기"""
        gathering = self.gatherings.get(gathering_id)
        if not gathering:
            return None

        date_counts = {}
        for participant, available_dates in responses.items():
            for d in available_dates:
                date_counts[d] = date_counts.get(d, 0) + 1

        # 가장 많은 사람이 가능한 날짜
        if date_counts:
            best_date = max(date_counts.items(), key=lambda x: x[1])
            if best_date[1] >= len(gathering.participants) * 0.7:  # 70% 이상 참석
                return best_date[0]

        return None

    # ========== 알림 관리 ==========

    async def _check_reminders(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """알림 체크"""
        reminders = {
            "birthdays": [],
            "events": [],
            "contact_needed": [],
            "holidays": []
        }

        today = date.today()
        reminder_days = self.config["birthday_reminder_days"]

        # 생일 알림
        for contact in self.contacts.values():
            if contact.birthday:
                # 올해 생일
                this_year_birthday = contact.birthday.replace(year=today.year)
                days_until = (this_year_birthday - today).days

                if 0 <= days_until <= reminder_days:
                    reminders["birthdays"].append({
                        "name": contact.name,
                        "date": str(this_year_birthday),
                        "days_until": days_until,
                        "relation": contact.relation_type.value
                    })

        # 경조사 알림
        for event in self.get_upcoming_events(self.config["event_reminder_days"]):
            days_until = (event.event_date - today).days
            reminders["events"].append({
                "contact": event.contact_name,
                "category": event.category.value,
                "date": str(event.event_date),
                "days_until": days_until,
                "rsvp_required": event.rsvp_required
            })

        # 연락 필요
        if self.config["contact_reminder_enabled"]:
            needs_contact = self.get_contacts_needing_contact()[:5]
            reminders["contact_needed"] = [
                {
                    "name": nc["contact"].name,
                    "days_since": nc["days_since"],
                    "relation": nc["contact"].relation_type.value
                }
                for nc in needs_contact
            ]

        # 명절 알림
        for holiday, dates in self.korean_holidays.items():
            for holiday_date in dates:
                hd = date.fromisoformat(holiday_date)
                days_until = (hd - today).days
                if 0 <= days_until <= 14:
                    reminders["holidays"].append({
                        "holiday": holiday,
                        "date": holiday_date,
                        "days_until": days_until
                    })

        return reminders

    # ========== 명절 인사 ==========

    async def _prepare_holiday_greetings(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """명절 인사 준비"""
        holiday = metadata.get("holiday", "설날")

        # 인사 대상 그룹화
        greeting_groups = {
            RelationType.FAMILY: [],
            RelationType.FRIEND: [],
            RelationType.COLLEAGUE: [],
            RelationType.BUSINESS: []
        }

        for contact in self.contacts.values():
            if contact.relation_type in greeting_groups:
                greeting_groups[contact.relation_type].append(contact.name)

        # 인사 메시지 템플릿
        templates = {
            "설날": {
                RelationType.FAMILY: "새해 복 많이 받으세요! 건강하시고 행복한 한 해 되세요.",
                RelationType.FRIEND: "새해 복 많이 받아! 올해도 좋은 일만 가득하길 바라.",
                RelationType.COLLEAGUE: "새해 복 많이 받으세요. 올해도 잘 부탁드립니다.",
                RelationType.BUSINESS: "새해 복 많이 받으십시오. 올해도 좋은 인연 이어가길 바랍니다."
            },
            "추석": {
                RelationType.FAMILY: "풍성한 한가위 보내세요! 가족 모두 건강하시길 바랍니다.",
                RelationType.FRIEND: "즐거운 추석 보내! 맛있는 거 많이 먹어.",
                RelationType.COLLEAGUE: "즐거운 추석 명절 되세요. 편안한 연휴 보내시길 바랍니다.",
                RelationType.BUSINESS: "풍요로운 한가위 되십시오."
            }
        }

        holiday_templates = templates.get(holiday, templates["설날"])

        return {
            "holiday": holiday,
            "groups": {
                rt.value: {
                    "count": len(names),
                    "contacts": names[:5],  # 상위 5명
                    "template": holiday_templates.get(rt, "")
                }
                for rt, names in greeting_groups.items()
                if names
            },
            "total_contacts": sum(len(names) for names in greeting_groups.values())
        }

    # ========== 리포트 ==========

    async def _generate_monthly_report(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """월간 사회생활 리포트"""
        month = metadata.get("month", date.today().month)
        year = metadata.get("year", date.today().year)

        # 이번 달 경조사
        month_events = [
            e for e in self.events.values()
            if e.event_date.month == month and e.event_date.year == year
        ]

        # 경조사비 지출
        month_gifts = [
            g for g in self.gift_history
            if g["direction"] == "given" and
            date.fromisoformat(g["date"]).month == month
        ]
        total_given = sum(g["amount"] for g in month_gifts)

        # 받은 축의금
        received_gifts = [
            g for g in self.gift_history
            if g["direction"] == "received" and
            date.fromisoformat(g["date"]).month == month
        ]
        total_received = sum(g["amount"] for g in received_gifts)

        # 연락 현황
        active_contacts = len([
            c for c in self.contacts.values()
            if c.last_contact and
            (datetime.now() - c.last_contact).days <= 30
        ])

        report = {
            "summary": f"경조사 {len(month_events)}건, 지출 {total_given:,}원",
            "period": f"{year}년 {month}월",
            "events": {
                "total": len(month_events),
                "by_category": self._count_by_category(month_events)
            },
            "expenses": {
                "total_given": total_given,
                "total_received": total_received,
                "net": total_received - total_given,
                "breakdown": [
                    {"to": g["to"], "amount": g["amount"], "category": g["category"]}
                    for g in month_gifts
                ]
            },
            "relationships": {
                "total_contacts": len(self.contacts),
                "active_this_month": active_contacts,
                "needs_attention": len(self.get_contacts_needing_contact())
            },
            "upcoming": [
                {
                    "contact": e.contact_name,
                    "category": e.category.value,
                    "date": str(e.event_date)
                }
                for e in self.get_upcoming_events(30)[:5]
            ]
        }

        return report

    def _count_by_category(self, events: List[SocialEvent]) -> Dict[str, int]:
        """카테고리별 집계"""
        counts = {}
        for event in events:
            cat = event.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    # ========== 이벤트 핸들러 ==========

    async def _on_contact_reminder(self, event) -> None:
        """연락 알림"""
        contact_name = event.data.get("name")
        self.logger.info(f"연락 알림: {contact_name}에게 연락할 때가 되었습니다")

    async def _on_event_reminder(self, event) -> None:
        """경조사 알림"""
        event_info = event.data
        self.logger.info(
            f"경조사 알림: {event_info.get('contact')}의 "
            f"{event_info.get('category')} ({event_info.get('date')})"
        )

    # ========== 핸들러 함수 ==========

    async def _handle_upcoming_events(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """예정 이벤트 요청 처리"""
        days = content.get("days", 30)
        events = self.get_upcoming_events(days)
        return {
            "count": len(events),
            "events": [
                {
                    "contact": e.contact_name,
                    "category": e.category.value,
                    "date": str(e.event_date),
                    "location": e.location
                }
                for e in events
            ]
        }

    async def _handle_gift_history(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """선물 내역 요청 처리"""
        contact = content.get("contact")
        if contact:
            return self.get_gift_balance(contact)

        # 최근 내역
        recent = sorted(
            self.gift_history,
            key=lambda x: x["date"],
            reverse=True
        )[:10]
        return {
            "recent": recent,
            "total_given": sum(
                g["amount"] for g in self.gift_history
                if g["direction"] == "given"
            ),
            "total_received": sum(
                g["amount"] for g in self.gift_history
                if g["direction"] == "received"
            )
        }

    async def _handle_monthly_report(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """월간 리포트 요청 처리"""
        return await self._generate_monthly_report(content)

    async def _handle_contact_suggestions(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """연락 제안 요청 처리"""
        needs_contact = self.get_contacts_needing_contact()
        return {
            "suggestions": [
                {
                    "name": nc["contact"].name,
                    "relation": nc["contact"].relation_type.value,
                    "days_since_contact": nc["days_since"],
                    "phone": nc["contact"].phone
                }
                for nc in needs_contact[:5]
            ]
        }

    async def _schedule_social_tasks(self) -> None:
        """사회생활 관리 작업 스케줄링"""
        # 매일 알림 체크
        await self.add_task(
            "check_reminders",
            "경조사 및 연락 알림 체크",
            Priority.NORMAL
        )
