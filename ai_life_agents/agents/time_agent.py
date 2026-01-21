"""
AgentTime - 시간/일정 관리 에이전트

기능:
- 일정 관리 및 최적화
- 할 일 목록 관리
- 생산성 분석
- 알림 및 리마인더
- 시간 블록 관리
- 습관 트래킹
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date, time
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import asyncio

from ..base_agent import BaseAgent, Task, Message, Priority


class EventType(Enum):
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    DEADLINE = "deadline"
    REMINDER = "reminder"
    FOCUS_TIME = "focus_time"
    PERSONAL = "personal"
    TRAVEL = "travel"


class TodoPriority(Enum):
    URGENT_IMPORTANT = "urgent_important"      # 긴급 + 중요
    NOT_URGENT_IMPORTANT = "not_urgent_important"  # 비긴급 + 중요
    URGENT_NOT_IMPORTANT = "urgent_not_important"  # 긴급 + 비중요
    NOT_URGENT_NOT_IMPORTANT = "not_urgent_not_important"  # 비긴급 + 비중요


@dataclass
class CalendarEvent:
    """캘린더 이벤트"""
    id: str
    title: str
    event_type: EventType
    start_time: datetime
    end_time: datetime
    location: str = ""
    description: str = ""
    attendees: List[str] = field(default_factory=list)
    recurring: Optional[str] = None  # daily, weekly, monthly
    reminder_minutes: int = 30
    is_all_day: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class TodoItem:
    """할 일 항목"""
    id: str
    title: str
    description: str = ""
    priority: TodoPriority = TodoPriority.NOT_URGENT_IMPORTANT
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    estimated_minutes: int = 30
    actual_minutes: Optional[int] = None
    status: str = "pending"  # pending, in_progress, completed, cancelled
    tags: List[str] = field(default_factory=list)
    project: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class Habit:
    """습관 트래킹"""
    id: str
    name: str
    frequency: str  # daily, weekly, monthly
    target_count: int = 1
    current_streak: int = 0
    best_streak: int = 0
    completion_history: List[date] = field(default_factory=list)
    reminder_time: Optional[time] = None


@dataclass
class TimeBlock:
    """시간 블록"""
    id: str
    name: str
    block_type: str  # deep_work, meeting, admin, break
    start_time: time
    end_time: time
    days: List[int] = field(default_factory=list)  # 0=월요일


class AgentTime(BaseAgent):
    """
    시간/일정 관리 에이전트

    한국 맞춤 기능:
    - 카카오/네이버 캘린더 연동
    - 공휴일 자동 반영
    - KTX/SRT 예약 시간 최적화
    - 배달 시간 예측
    """

    def __init__(self, agent_id: str = "time"):
        super().__init__(
            agent_id=agent_id,
            name="AgentTime",
            description="시간 및 일정 관리 에이전트"
        )

        # 데이터 저장소
        self.events: Dict[str, CalendarEvent] = {}
        self.todos: Dict[str, TodoItem] = {}
        self.habits: Dict[str, Habit] = {}
        self.time_blocks: List[TimeBlock] = []

        # 생산성 기록
        self.focus_sessions: List[Dict[str, Any]] = []
        self.daily_logs: Dict[str, Dict[str, Any]] = {}

        # 설정
        self.config = {
            "work_start_time": "09:00",
            "work_end_time": "18:00",
            "focus_duration_minutes": 25,  # 포모도로
            "break_duration_minutes": 5,
            "long_break_after": 4,  # 4세션 후 긴 휴식
            "long_break_duration": 15,
            "meeting_buffer_minutes": 15,
            "default_reminder_minutes": 30,
            "weekend_work": False
        }

        # 한국 공휴일 (2024년)
        self.holidays = {
            "2024-01-01": "신정",
            "2024-02-09": "설날 연휴",
            "2024-02-10": "설날",
            "2024-02-11": "설날 연휴",
            "2024-02-12": "대체공휴일",
            "2024-03-01": "삼일절",
            "2024-04-10": "국회의원선거일",
            "2024-05-05": "어린이날",
            "2024-05-06": "대체공휴일",
            "2024-05-15": "부처님오신날",
            "2024-06-06": "현충일",
            "2024-08-15": "광복절",
            "2024-09-16": "추석 연휴",
            "2024-09-17": "추석",
            "2024-09-18": "추석 연휴",
            "2024-10-03": "개천절",
            "2024-10-09": "한글날",
            "2024-12-25": "크리스마스"
        }

    async def initialize(self) -> bool:
        """초기화"""
        self.logger.info("시간 관리 에이전트 초기화 중...")

        # 이벤트 핸들러 등록
        self.on("event_reminder", self._on_event_reminder)
        self.on("todo_due", self._on_todo_due)

        # 스케줄러 시작
        await self._schedule_time_tasks()

        return True

    def get_capabilities(self) -> List[str]:
        """기능 목록"""
        return [
            "calendar_management",    # 일정 관리
            "todo_management",       # 할 일 관리
            "time_blocking",         # 시간 블록
            "habit_tracking",        # 습관 트래킹
            "focus_sessions",        # 집중 세션
            "productivity_analysis", # 생산성 분석
            "schedule_optimization", # 일정 최적화
            "reminder_management",   # 알림 관리
            "travel_planning",       # 이동 계획
            "time_report"           # 시간 리포트
        ]

    async def process_task(self, task: Task) -> Any:
        """작업 처리"""
        task_handlers = {
            "add_event": self._add_event,
            "add_todo": self._add_todo,
            "complete_todo": self._complete_todo,
            "start_focus": self._start_focus_session,
            "analyze_productivity": self._analyze_productivity,
            "optimize_schedule": self._optimize_schedule,
            "weekly_review": self._weekly_review,
            "daily_plan": self._generate_daily_plan
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
            "get_today_schedule": self._handle_today_schedule,
            "get_todo_list": self._handle_todo_list,
            "monthly_report": self._handle_monthly_report,
            "availability_check": self._handle_availability
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

    # ========== 캘린더 관리 ==========

    async def _add_event(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """일정 추가"""
        event = CalendarEvent(
            id=f"event_{datetime.now().timestamp()}",
            title=metadata.get("title", ""),
            event_type=EventType(metadata.get("type", "meeting")),
            start_time=datetime.fromisoformat(metadata.get("start_time")),
            end_time=datetime.fromisoformat(metadata.get("end_time")),
            location=metadata.get("location", ""),
            description=metadata.get("description", ""),
            attendees=metadata.get("attendees", []),
            reminder_minutes=metadata.get("reminder_minutes", 30)
        )

        # 충돌 체크
        conflicts = self._check_conflicts(event)
        if conflicts:
            self.logger.warning(f"일정 충돌 발견: {[c.title for c in conflicts]}")

        self.events[event.id] = event
        self.logger.info(f"일정 추가: {event.title} ({event.start_time})")

        # 다른 에이전트에 알림 (건강 예약이면 건강 에이전트에)
        if event.event_type == EventType.APPOINTMENT:
            await self.send_message(
                "health",
                "appointment_scheduled",
                {
                    "title": event.title,
                    "datetime": event.start_time.isoformat(),
                    "location": event.location
                }
            )

        return {
            "added": True,
            "event_id": event.id,
            "conflicts": [c.title for c in conflicts] if conflicts else None
        }

    def _check_conflicts(self, new_event: CalendarEvent) -> List[CalendarEvent]:
        """일정 충돌 체크"""
        conflicts = []
        for event in self.events.values():
            if event.id == new_event.id:
                continue
            # 시간 겹침 체크
            if (new_event.start_time < event.end_time and
                new_event.end_time > event.start_time):
                conflicts.append(event)
        return conflicts

    def get_events_for_date(self, target_date: date) -> List[CalendarEvent]:
        """특정 날짜 일정 조회"""
        events = []
        for event in self.events.values():
            if event.start_time.date() == target_date:
                events.append(event)
        return sorted(events, key=lambda e: e.start_time)

    def find_free_slots(self, target_date: date,
                       duration_minutes: int) -> List[Dict[str, Any]]:
        """빈 시간대 찾기"""
        work_start = datetime.combine(
            target_date,
            datetime.strptime(self.config["work_start_time"], "%H:%M").time()
        )
        work_end = datetime.combine(
            target_date,
            datetime.strptime(self.config["work_end_time"], "%H:%M").time()
        )

        events = self.get_events_for_date(target_date)
        events = sorted(events, key=lambda e: e.start_time)

        free_slots = []
        current = work_start

        for event in events:
            if event.start_time > current:
                gap = (event.start_time - current).total_seconds() / 60
                if gap >= duration_minutes:
                    free_slots.append({
                        "start": current.isoformat(),
                        "end": event.start_time.isoformat(),
                        "duration_minutes": gap
                    })
            current = max(current, event.end_time)

        # 마지막 이벤트 후
        if current < work_end:
            gap = (work_end - current).total_seconds() / 60
            if gap >= duration_minutes:
                free_slots.append({
                    "start": current.isoformat(),
                    "end": work_end.isoformat(),
                    "duration_minutes": gap
                })

        return free_slots

    # ========== 할 일 관리 ==========

    async def _add_todo(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """할 일 추가"""
        todo = TodoItem(
            id=f"todo_{datetime.now().timestamp()}",
            title=metadata.get("title", ""),
            description=metadata.get("description", ""),
            priority=TodoPriority(metadata.get("priority", "not_urgent_important")),
            due_date=date.fromisoformat(metadata["due_date"]) if metadata.get("due_date") else None,
            estimated_minutes=metadata.get("estimated_minutes", 30),
            tags=metadata.get("tags", []),
            project=metadata.get("project", "")
        )

        self.todos[todo.id] = todo
        self.logger.info(f"할 일 추가: {todo.title}")

        return {
            "added": True,
            "todo_id": todo.id,
            "priority": todo.priority.value
        }

    async def _complete_todo(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """할 일 완료"""
        todo_id = metadata.get("todo_id")
        todo = self.todos.get(todo_id)

        if not todo:
            return {"success": False, "error": "할 일을 찾을 수 없습니다"}

        todo.status = "completed"
        todo.completed_at = datetime.now()
        todo.actual_minutes = metadata.get("actual_minutes", todo.estimated_minutes)

        self.logger.info(f"할 일 완료: {todo.title}")

        return {
            "success": True,
            "title": todo.title,
            "estimated_minutes": todo.estimated_minutes,
            "actual_minutes": todo.actual_minutes
        }

    def get_pending_todos(self, priority: Optional[TodoPriority] = None) -> List[TodoItem]:
        """대기 중인 할 일 조회"""
        todos = [t for t in self.todos.values() if t.status == "pending"]

        if priority:
            todos = [t for t in todos if t.priority == priority]

        # 우선순위 순 정렬
        priority_order = {
            TodoPriority.URGENT_IMPORTANT: 0,
            TodoPriority.NOT_URGENT_IMPORTANT: 1,
            TodoPriority.URGENT_NOT_IMPORTANT: 2,
            TodoPriority.NOT_URGENT_NOT_IMPORTANT: 3
        }
        return sorted(todos, key=lambda t: (priority_order[t.priority], t.due_date or date.max))

    # ========== 집중 세션 (포모도로) ==========

    async def _start_focus_session(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """집중 세션 시작"""
        task_name = metadata.get("task", "집중 작업")
        duration = metadata.get("duration", self.config["focus_duration_minutes"])

        session = {
            "id": f"focus_{datetime.now().timestamp()}",
            "task": task_name,
            "duration_minutes": duration,
            "started_at": datetime.now().isoformat(),
            "completed": False
        }

        self.focus_sessions.append(session)
        self.logger.info(f"집중 세션 시작: {task_name} ({duration}분)")

        # 다른 에이전트에 방해 금지 알림
        await self.broadcast(
            "focus_mode_started",
            {
                "duration_minutes": duration,
                "ends_at": (datetime.now() + timedelta(minutes=duration)).isoformat()
            }
        )

        return {
            "started": True,
            "session_id": session["id"],
            "duration_minutes": duration,
            "break_after": self.config["break_duration_minutes"]
        }

    def get_focus_stats(self, days: int = 7) -> Dict[str, Any]:
        """집중 세션 통계"""
        cutoff = datetime.now() - timedelta(days=days)

        recent_sessions = [
            s for s in self.focus_sessions
            if datetime.fromisoformat(s["started_at"]) >= cutoff
        ]

        completed = [s for s in recent_sessions if s.get("completed")]

        total_minutes = sum(s["duration_minutes"] for s in completed)

        return {
            "total_sessions": len(recent_sessions),
            "completed_sessions": len(completed),
            "total_focus_minutes": total_minutes,
            "avg_daily_minutes": total_minutes / days if days else 0,
            "completion_rate": len(completed) / len(recent_sessions) * 100 if recent_sessions else 0
        }

    # ========== 생산성 분석 ==========

    async def _analyze_productivity(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """생산성 분석"""
        days = metadata.get("days", 7)

        # 할 일 완료율
        completed_todos = [
            t for t in self.todos.values()
            if t.status == "completed" and t.completed_at and
            t.completed_at >= datetime.now() - timedelta(days=days)
        ]

        # 예상 vs 실제 시간
        time_accuracy = []
        for todo in completed_todos:
            if todo.actual_minutes and todo.estimated_minutes:
                accuracy = todo.actual_minutes / todo.estimated_minutes
                time_accuracy.append(accuracy)

        avg_accuracy = sum(time_accuracy) / len(time_accuracy) if time_accuracy else 1.0

        # 집중 시간
        focus_stats = self.get_focus_stats(days)

        # 일정 준수율
        past_events = [
            e for e in self.events.values()
            if e.start_time.date() <= date.today() and
            e.start_time >= datetime.now() - timedelta(days=days)
        ]

        analysis = {
            "period_days": days,
            "todos_completed": len(completed_todos),
            "avg_time_accuracy": avg_accuracy,
            "time_accuracy_interpretation": (
                "과소 추정 경향" if avg_accuracy > 1.2 else
                "과대 추정 경향" if avg_accuracy < 0.8 else
                "적절한 추정"
            ),
            "focus_stats": focus_stats,
            "events_count": len(past_events),
            "productivity_score": self._calculate_productivity_score(
                len(completed_todos), focus_stats, avg_accuracy
            ),
            "recommendations": []
        }

        # 권장 사항
        if focus_stats.get("avg_daily_minutes", 0) < 60:
            analysis["recommendations"].append(
                "집중 시간이 부족합니다. 하루 최소 2시간의 딥워크를 권장합니다."
            )

        if avg_accuracy > 1.3:
            analysis["recommendations"].append(
                "작업 시간을 자주 과소 추정하고 있습니다. 버퍼 시간을 추가하세요."
            )

        return analysis

    def _calculate_productivity_score(self, todos_completed: int,
                                      focus_stats: Dict[str, Any],
                                      time_accuracy: float) -> int:
        """생산성 점수 계산 (0-100)"""
        score = 50  # 기본 점수

        # 할 일 완료 점수
        score += min(todos_completed * 2, 20)

        # 집중 시간 점수
        focus_minutes = focus_stats.get("total_focus_minutes", 0)
        score += min(focus_minutes / 60, 20)  # 최대 20점

        # 시간 추정 정확도 점수
        if 0.8 <= time_accuracy <= 1.2:
            score += 10

        return min(100, max(0, int(score)))

    # ========== 일정 최적화 ==========

    async def _optimize_schedule(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """일정 최적화"""
        target_date = date.fromisoformat(metadata.get("date", str(date.today())))

        events = self.get_events_for_date(target_date)
        todos = self.get_pending_todos()

        optimizations = []

        # 1. 회의 사이 버퍼 체크
        for i, event in enumerate(events[:-1]):
            next_event = events[i + 1]
            gap = (next_event.start_time - event.end_time).total_seconds() / 60

            if 0 < gap < self.config["meeting_buffer_minutes"]:
                optimizations.append({
                    "type": "buffer_warning",
                    "message": f"'{event.title}'과 '{next_event.title}' 사이 여유 시간이 {gap:.0f}분입니다",
                    "recommendation": "최소 15분의 버퍼를 권장합니다"
                })

        # 2. 긴급 할 일에 시간 할당
        urgent_todos = [t for t in todos if t.priority == TodoPriority.URGENT_IMPORTANT]
        free_slots = self.find_free_slots(target_date, 30)

        for todo in urgent_todos:
            suitable_slot = next(
                (s for s in free_slots if s["duration_minutes"] >= todo.estimated_minutes),
                None
            )
            if suitable_slot:
                optimizations.append({
                    "type": "todo_scheduling",
                    "todo": todo.title,
                    "suggested_time": suitable_slot["start"],
                    "duration": todo.estimated_minutes
                })

        # 3. 집중 시간 확보
        deep_work_needed = 120  # 2시간
        large_slots = [s for s in free_slots if s["duration_minutes"] >= 60]

        if sum(s["duration_minutes"] for s in large_slots) < deep_work_needed:
            optimizations.append({
                "type": "focus_time_warning",
                "message": "집중 작업 시간이 부족합니다",
                "available_minutes": sum(s["duration_minutes"] for s in large_slots),
                "recommended_minutes": deep_work_needed
            })

        return {
            "date": str(target_date),
            "events_count": len(events),
            "pending_todos": len(todos),
            "optimizations": optimizations,
            "free_slots": free_slots
        }

    # ========== 일일/주간 계획 ==========

    async def _generate_daily_plan(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """일일 계획 생성"""
        target_date = date.fromisoformat(metadata.get("date", str(date.today())))

        # 공휴일 체크
        is_holiday = str(target_date) in self.holidays
        holiday_name = self.holidays.get(str(target_date))

        events = self.get_events_for_date(target_date)
        todos = self.get_pending_todos()

        # 오늘 마감 할 일
        today_due = [t for t in todos if t.due_date == target_date]

        plan = {
            "date": str(target_date),
            "day_of_week": ["월", "화", "수", "목", "금", "토", "일"][target_date.weekday()],
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "schedule": [
                {
                    "time": e.start_time.strftime("%H:%M"),
                    "title": e.title,
                    "type": e.event_type.value,
                    "duration_minutes": int((e.end_time - e.start_time).total_seconds() / 60)
                }
                for e in events
            ],
            "todos_due_today": [
                {
                    "title": t.title,
                    "priority": t.priority.value,
                    "estimated_minutes": t.estimated_minutes
                }
                for t in today_due
            ],
            "top_priorities": [
                {"title": t.title, "priority": t.priority.value}
                for t in todos[:3]
            ],
            "focus_time_available": sum(
                s["duration_minutes"]
                for s in self.find_free_slots(target_date, 30)
                if s["duration_minutes"] >= 60
            )
        }

        return plan

    async def _weekly_review(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """주간 리뷰"""
        # 지난 주 분석
        productivity = await self._analyze_productivity({"days": 7})

        # 습관 현황
        habit_stats = {}
        for habit in self.habits.values():
            recent_completions = len([
                d for d in habit.completion_history
                if d >= date.today() - timedelta(days=7)
            ])
            habit_stats[habit.name] = {
                "target": habit.target_count * 7 if habit.frequency == "daily" else habit.target_count,
                "completed": recent_completions,
                "streak": habit.current_streak
            }

        # 다음 주 미리보기
        next_week_events = []
        for i in range(7):
            target = date.today() + timedelta(days=i+1)
            events = self.get_events_for_date(target)
            if events:
                next_week_events.append({
                    "date": str(target),
                    "events_count": len(events),
                    "key_events": [e.title for e in events[:3]]
                })

        return {
            "week_ending": str(date.today()),
            "productivity": productivity,
            "habits": habit_stats,
            "next_week_preview": next_week_events,
            "summary": f"생산성 점수: {productivity['productivity_score']}점 | "
                      f"완료 할일: {productivity['todos_completed']}개"
        }

    # ========== 이벤트 핸들러 ==========

    async def _on_event_reminder(self, event) -> None:
        """일정 알림"""
        event_title = event.data.get("title")
        minutes_until = event.data.get("minutes_until")
        self.logger.info(f"일정 알림: {event_title} - {minutes_until}분 후")

    async def _on_todo_due(self, event) -> None:
        """할 일 마감 알림"""
        todo_title = event.data.get("title")
        self.logger.info(f"할 일 마감: {todo_title}")

    # ========== 핸들러 함수 ==========

    async def _handle_today_schedule(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """오늘 일정 요청 처리"""
        return await self._generate_daily_plan({"date": str(date.today())})

    async def _handle_todo_list(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """할 일 목록 요청 처리"""
        todos = self.get_pending_todos()
        return {
            "pending_count": len(todos),
            "todos": [
                {
                    "id": t.id,
                    "title": t.title,
                    "priority": t.priority.value,
                    "due_date": str(t.due_date) if t.due_date else None,
                    "estimated_minutes": t.estimated_minutes
                }
                for t in todos[:10]
            ]
        }

    async def _handle_monthly_report(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """월간 리포트 요청 처리"""
        productivity = await self._analyze_productivity({"days": 30})
        return {
            "summary": f"이번 달 생산성 점수: {productivity['productivity_score']}점",
            "productivity": productivity
        }

    async def _handle_availability(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """가용 시간 확인 요청 처리"""
        target_date = date.fromisoformat(content.get("date", str(date.today())))
        duration = content.get("duration_minutes", 60)
        return {
            "date": str(target_date),
            "free_slots": self.find_free_slots(target_date, duration)
        }

    async def _schedule_time_tasks(self) -> None:
        """시간 관리 작업 스케줄링"""
        # 매일 아침 일일 계획
        await self.add_task(
            "daily_plan",
            "일일 계획 생성",
            Priority.HIGH
        )
