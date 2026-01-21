"""
AgentHealth - 건강 관리 에이전트
Matt Schlicht의 AgentHealth 컨셉을 한국 상황에 맞게 구현

기능:
- 바이탈 모니터링 (웨어러블 연동)
- 식단 관리 및 영양 분석
- 건강검진 예약 및 관리
- 의사 소통 보조
- 복약 알림
- 운동 트래킹
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import asyncio

from ..base_agent import BaseAgent, Task, Message, Priority


class VitalType(Enum):
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE = "blood_pressure"
    BLOOD_SUGAR = "blood_sugar"
    WEIGHT = "weight"
    BODY_TEMP = "body_temp"
    OXYGEN_SAT = "oxygen_saturation"
    SLEEP_HOURS = "sleep_hours"
    STEPS = "steps"


@dataclass
class VitalRecord:
    """바이탈 기록"""
    vital_type: VitalType
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    notes: str = ""
    source: str = ""  # manual, apple_watch, galaxy_watch, etc.


@dataclass
class Medication:
    """복약 정보"""
    id: str
    name: str
    dosage: str
    frequency: str  # daily, twice_daily, weekly, etc.
    times: List[str] = field(default_factory=list)  # ["08:00", "20:00"]
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    refill_date: Optional[date] = None
    prescribing_doctor: str = ""
    pharmacy: str = ""
    notes: str = ""


@dataclass
class Meal:
    """식사 기록"""
    id: str
    meal_type: str  # breakfast, lunch, dinner, snack
    foods: List[Dict[str, Any]] = field(default_factory=list)
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    timestamp: datetime = field(default_factory=datetime.now)
    photo_url: str = ""


@dataclass
class Appointment:
    """의료 예약"""
    id: str
    doctor_name: str
    hospital: str
    department: str
    appointment_type: str  # checkup, follow_up, procedure
    scheduled_at: datetime
    notes: str = ""
    reminder_sent: bool = False
    insurance_covered: bool = True


@dataclass
class HealthGoal:
    """건강 목표"""
    id: str
    goal_type: str  # weight, steps, sleep, etc.
    target_value: float
    current_value: float = 0
    unit: str = ""
    deadline: Optional[date] = None
    progress_pct: float = 0


class AgentHealth(BaseAgent):
    """
    건강 관리 에이전트

    한국 맞춤 기능:
    - 국민건강보험 건강검진 알림
    - 실손보험 청구 자동화
    - 의료비 세액공제 정리
    - 약국 재고 확인 (약학정보원 연동)
    - 병원 예약 (네이버 예약, 똑닥 등)
    """

    def __init__(self, agent_id: str = "health"):
        super().__init__(
            agent_id=agent_id,
            name="AgentHealth",
            description="건강 및 의료 관리 에이전트"
        )

        # 데이터 저장소
        self.vitals: Dict[VitalType, List[VitalRecord]] = {t: [] for t in VitalType}
        self.medications: Dict[str, Medication] = {}
        self.meals: List[Meal] = []
        self.appointments: Dict[str, Appointment] = {}
        self.goals: Dict[str, HealthGoal] = {}

        # 건강 프로필
        self.profile = {
            "birth_year": 1990,
            "gender": "male",
            "height_cm": 175,
            "blood_type": "A+",
            "allergies": [],
            "chronic_conditions": [],
            "emergency_contact": ""
        }

        # 설정
        self.config = {
            "daily_calorie_target": 2000,
            "daily_steps_target": 10000,
            "sleep_hours_target": 7,
            "water_glasses_target": 8,
            "weight_goal": 70,
            "medication_reminders": True,
            "appointment_reminders": True,
            "vital_alerts": True
        }

        # 정상 범위 (경고 기준)
        self.normal_ranges = {
            VitalType.HEART_RATE: (60, 100),
            VitalType.BLOOD_PRESSURE: ((90, 120), (60, 80)),  # 수축기, 이완기
            VitalType.BLOOD_SUGAR: (70, 140),
            VitalType.BODY_TEMP: (36.1, 37.2),
            VitalType.OXYGEN_SAT: (95, 100),
        }

    async def initialize(self) -> bool:
        """초기화"""
        self.logger.info("건강 에이전트 초기화 중...")

        # 이벤트 핸들러 등록
        self.on("vital_recorded", self._on_vital_recorded)
        self.on("medication_time", self._on_medication_time)
        self.on("insurance_paid", self._on_insurance_paid)

        # 스케줄러 시작
        await self._schedule_health_checks()

        return True

    def get_capabilities(self) -> List[str]:
        """기능 목록"""
        return [
            "vital_monitoring",       # 바이탈 모니터링
            "medication_management",  # 복약 관리
            "diet_tracking",         # 식단 관리
            "appointment_booking",   # 예약 관리
            "health_checkup",        # 건강검진 관리
            "insurance_claim",       # 보험 청구
            "doctor_communication",  # 의사 소통
            "exercise_tracking",     # 운동 트래킹
            "sleep_analysis",        # 수면 분석
            "health_report"          # 건강 리포트
        ]

    async def process_task(self, task: Task) -> Any:
        """작업 처리"""
        task_handlers = {
            "record_vital": self._record_vital,
            "log_meal": self._log_meal,
            "check_medications": self._check_medications,
            "book_appointment": self._book_appointment,
            "analyze_health": self._analyze_health,
            "claim_insurance": self._claim_insurance,
            "generate_health_report": self._generate_health_report,
            "check_checkup_schedule": self._check_checkup_schedule
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
            "get_health_summary": self._handle_health_summary,
            "get_vitals": self._handle_get_vitals,
            "monthly_report": self._handle_monthly_report,
            "medication_status": self._handle_medication_status
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

    # ========== 바이탈 모니터링 ==========

    async def _record_vital(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """바이탈 기록"""
        vital_type = VitalType(metadata.get("type"))
        value = metadata.get("value")
        unit = metadata.get("unit", "")
        source = metadata.get("source", "manual")

        record = VitalRecord(
            vital_type=vital_type,
            value=value,
            unit=unit,
            source=source
        )

        self.vitals[vital_type].append(record)
        self.logger.info(f"바이탈 기록: {vital_type.value} = {value}{unit}")

        # 이상치 체크
        alert = self._check_vital_alert(vital_type, value)
        if alert:
            await self._handle_vital_alert(vital_type, value, alert)

        return {"recorded": True, "alert": alert}

    def _check_vital_alert(self, vital_type: VitalType,
                          value: float) -> Optional[str]:
        """바이탈 이상치 체크"""
        if vital_type not in self.normal_ranges:
            return None

        normal_range = self.normal_ranges[vital_type]

        if vital_type == VitalType.BLOOD_PRESSURE:
            # 혈압은 특별 처리 (수축기/이완기)
            return None

        low, high = normal_range
        if value < low:
            return f"낮음 (정상: {low}-{high})"
        elif value > high:
            return f"높음 (정상: {low}-{high})"
        return None

    async def _handle_vital_alert(self, vital_type: VitalType,
                                  value: float, alert: str) -> None:
        """바이탈 이상 알림 처리"""
        self.logger.warning(
            f"바이탈 경고: {vital_type.value} = {value} - {alert}"
        )

        # 심각한 경우 긴급 알림
        if vital_type == VitalType.HEART_RATE:
            if value > 150 or value < 40:
                await self.broadcast(
                    "health_emergency",
                    {
                        "type": "vital_critical",
                        "vital": vital_type.value,
                        "value": value,
                        "alert": alert
                    },
                    message_type="alert"
                )

    def get_vital_trend(self, vital_type: VitalType,
                       days: int = 30) -> Dict[str, Any]:
        """바이탈 트렌드 분석"""
        records = self.vitals.get(vital_type, [])
        cutoff = datetime.now() - timedelta(days=days)

        recent = [r for r in records if r.timestamp >= cutoff]

        if not recent:
            return {"trend": "no_data", "average": None}

        values = [r.value for r in recent]
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)

        # 트렌드 계산 (단순 선형)
        if len(values) >= 2:
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            if second_half > first_half * 1.05:
                trend = "increasing"
            elif second_half < first_half * 0.95:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "average": avg,
            "min": min_val,
            "max": max_val,
            "count": len(recent)
        }

    # ========== 복약 관리 ==========

    def add_medication(self, medication: Medication) -> None:
        """복약 추가"""
        self.medications[medication.id] = medication
        self.logger.info(f"복약 추가: {medication.name} ({medication.dosage})")

    async def _check_medications(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """복약 상태 체크"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        reminders = []
        refills_needed = []

        for med in self.medications.values():
            # 끝난 약 제외
            if med.end_date and med.end_date < now.date():
                continue

            # 복약 시간 체크
            for time in med.times:
                if self._is_time_near(current_time, time, minutes=30):
                    reminders.append({
                        "medication": med.name,
                        "dosage": med.dosage,
                        "scheduled_time": time
                    })

            # 리필 필요 체크
            if med.refill_date and med.refill_date <= now.date() + timedelta(days=7):
                refills_needed.append({
                    "medication": med.name,
                    "refill_date": med.refill_date.isoformat(),
                    "pharmacy": med.pharmacy
                })

        return {
            "reminders": reminders,
            "refills_needed": refills_needed
        }

    def _is_time_near(self, current: str, target: str, minutes: int) -> bool:
        """시간 근접 체크"""
        try:
            current_mins = int(current.split(":")[0]) * 60 + int(current.split(":")[1])
            target_mins = int(target.split(":")[0]) * 60 + int(target.split(":")[1])
            return abs(current_mins - target_mins) <= minutes
        except Exception:
            return False

    # ========== 식단 관리 ==========

    async def _log_meal(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """식사 기록"""
        meal = Meal(
            id=f"meal_{datetime.now().timestamp()}",
            meal_type=metadata.get("meal_type", "snack"),
            foods=metadata.get("foods", []),
            calories=metadata.get("calories", 0),
            protein=metadata.get("protein", 0),
            carbs=metadata.get("carbs", 0),
            fat=metadata.get("fat", 0),
            photo_url=metadata.get("photo_url", "")
        )

        self.meals.append(meal)
        self.logger.info(
            f"식사 기록: {meal.meal_type} - {meal.calories}kcal"
        )

        # 일일 칼로리 체크
        daily_calories = self._get_daily_calories()
        target = self.config["daily_calorie_target"]

        if daily_calories > target:
            await self.emit_event("calorie_exceeded", {
                "consumed": daily_calories,
                "target": target,
                "excess": daily_calories - target
            })

        return {
            "logged": True,
            "daily_total": daily_calories,
            "target": target,
            "remaining": target - daily_calories
        }

    def _get_daily_calories(self) -> float:
        """오늘 섭취 칼로리"""
        today = datetime.now().date()
        return sum(
            meal.calories for meal in self.meals
            if meal.timestamp.date() == today
        )

    def get_nutrition_summary(self, days: int = 7) -> Dict[str, Any]:
        """영양소 요약"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_meals = [m for m in self.meals if m.timestamp >= cutoff]

        if not recent_meals:
            return {"no_data": True}

        total_days = max(1, (datetime.now() - cutoff).days)

        return {
            "avg_daily_calories": sum(m.calories for m in recent_meals) / total_days,
            "avg_daily_protein": sum(m.protein for m in recent_meals) / total_days,
            "avg_daily_carbs": sum(m.carbs for m in recent_meals) / total_days,
            "avg_daily_fat": sum(m.fat for m in recent_meals) / total_days,
            "meal_count": len(recent_meals),
            "days_tracked": total_days
        }

    # ========== 예약 관리 ==========

    async def _book_appointment(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        병원 예약

        한국 서비스 연동:
        - 네이버 예약
        - 똑닥
        - 굿닥
        """
        appointment = Appointment(
            id=f"apt_{datetime.now().timestamp()}",
            doctor_name=metadata.get("doctor_name", ""),
            hospital=metadata.get("hospital", ""),
            department=metadata.get("department", ""),
            appointment_type=metadata.get("type", "checkup"),
            scheduled_at=datetime.fromisoformat(metadata.get("datetime")),
            insurance_covered=metadata.get("insurance_covered", True)
        )

        self.appointments[appointment.id] = appointment
        self.logger.info(
            f"예약 완료: {appointment.hospital} {appointment.department} "
            f"({appointment.scheduled_at})"
        )

        # 재정 에이전트에 의료비 예상 알림
        if appointment.insurance_covered:
            await self.send_message(
                "finance",
                "medical_expense_expected",
                {
                    "hospital": appointment.hospital,
                    "department": appointment.department,
                    "date": appointment.scheduled_at.isoformat(),
                    "insurance_covered": True
                }
            )

        return {
            "booked": True,
            "appointment_id": appointment.id,
            "details": {
                "hospital": appointment.hospital,
                "datetime": appointment.scheduled_at.isoformat()
            }
        }

    def get_upcoming_appointments(self, days: int = 30) -> List[Dict[str, Any]]:
        """예정된 예약"""
        now = datetime.now()
        cutoff = now + timedelta(days=days)

        upcoming = []
        for apt in self.appointments.values():
            if now <= apt.scheduled_at <= cutoff:
                upcoming.append({
                    "id": apt.id,
                    "hospital": apt.hospital,
                    "department": apt.department,
                    "doctor": apt.doctor_name,
                    "datetime": apt.scheduled_at.isoformat(),
                    "type": apt.appointment_type
                })

        return sorted(upcoming, key=lambda x: x["datetime"])

    # ========== 건강검진 관리 ==========

    async def _check_checkup_schedule(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        국민건강보험 건강검진 일정 확인

        - 일반건강검진: 2년마다 (짝수/홀수년 출생)
        - 암검진: 연령별 상이
        """
        birth_year = self.profile.get("birth_year", 1990)
        current_year = datetime.now().year
        age = current_year - birth_year

        checkups_due = []

        # 일반건강검진 (2년마다)
        is_even_birth = birth_year % 2 == 0
        is_even_year = current_year % 2 == 0
        if is_even_birth == is_even_year:
            checkups_due.append({
                "type": "일반건강검진",
                "description": "국민건강보험 일반건강검진 대상자",
                "deadline": f"{current_year}-12-31"
            })

        # 암검진 (연령별)
        gender = self.profile.get("gender", "male")

        if age >= 40:
            checkups_due.append({
                "type": "위암검진",
                "description": "40세 이상 2년마다",
                "deadline": f"{current_year}-12-31"
            })

        if age >= 50:
            checkups_due.append({
                "type": "대장암검진",
                "description": "50세 이상 매년",
                "deadline": f"{current_year}-12-31"
            })

        if gender == "female" and age >= 20:
            checkups_due.append({
                "type": "자궁경부암검진",
                "description": "20세 이상 여성 2년마다",
                "deadline": f"{current_year}-12-31"
            })

        if gender == "female" and age >= 40:
            checkups_due.append({
                "type": "유방암검진",
                "description": "40세 이상 여성 2년마다",
                "deadline": f"{current_year}-12-31"
            })

        return {
            "age": age,
            "checkups_due": checkups_due,
            "total_due": len(checkups_due)
        }

    # ========== 보험 청구 ==========

    async def _claim_insurance(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        실손보험 청구 자동화

        필요 서류:
        - 진료비 영수증
        - 진료비 세부내역서
        - 진단서 (필요시)
        """
        claim = {
            "hospital": metadata.get("hospital"),
            "treatment_date": metadata.get("treatment_date"),
            "total_amount": metadata.get("total_amount"),
            "documents": metadata.get("documents", []),
            "status": "submitted"
        }

        self.logger.info(
            f"보험 청구 제출: {claim['hospital']} - {claim['total_amount']:,}원"
        )

        # 재정 에이전트에 보험금 예상 알림
        await self.send_message(
            "finance",
            "insurance_claim_submitted",
            {
                "amount": claim["total_amount"],
                "expected_refund": claim["total_amount"] * 0.8,  # 80% 예상
                "processing_days": 7
            }
        )

        return {
            "submitted": True,
            "claim": claim,
            "expected_refund": claim["total_amount"] * 0.8
        }

    # ========== 건강 분석 ==========

    async def _analyze_health(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """종합 건강 분석"""
        analysis = {
            "vitals": {},
            "nutrition": {},
            "activity": {},
            "sleep": {},
            "recommendations": []
        }

        # 바이탈 트렌드
        for vital_type in [VitalType.HEART_RATE, VitalType.WEIGHT, VitalType.BLOOD_PRESSURE]:
            analysis["vitals"][vital_type.value] = self.get_vital_trend(vital_type)

        # 영양 분석
        analysis["nutrition"] = self.get_nutrition_summary()

        # 활동량 (걸음 수)
        steps_data = self.get_vital_trend(VitalType.STEPS, days=7)
        analysis["activity"] = {
            "avg_daily_steps": steps_data.get("average", 0),
            "target": self.config["daily_steps_target"],
            "achievement_rate": (
                steps_data.get("average", 0) / self.config["daily_steps_target"] * 100
                if steps_data.get("average") else 0
            )
        }

        # 수면 분석
        sleep_data = self.get_vital_trend(VitalType.SLEEP_HOURS, days=7)
        analysis["sleep"] = {
            "avg_hours": sleep_data.get("average", 0),
            "target": self.config["sleep_hours_target"],
            "quality": "good" if sleep_data.get("average", 0) >= 7 else "needs_improvement"
        }

        # 권장 사항 생성
        analysis["recommendations"] = self._generate_health_recommendations(analysis)

        return analysis

    def _generate_health_recommendations(self,
                                        analysis: Dict[str, Any]) -> List[str]:
        """건강 권장 사항 생성"""
        recommendations = []

        # 활동량
        activity = analysis.get("activity", {})
        if activity.get("achievement_rate", 0) < 70:
            recommendations.append(
                f"일일 걸음 수가 목표({activity.get('target', 10000)}보)에 "
                f"미달합니다. 더 많이 걸어보세요."
            )

        # 수면
        sleep = analysis.get("sleep", {})
        if sleep.get("quality") == "needs_improvement":
            recommendations.append(
                f"수면 시간이 권장량({sleep.get('target', 7)}시간)에 미달합니다. "
                "일정한 취침 시간을 유지해보세요."
            )

        # 영양
        nutrition = analysis.get("nutrition", {})
        if nutrition.get("avg_daily_protein", 0) < 50:
            recommendations.append(
                "단백질 섭취가 부족합니다. 고단백 음식을 더 드세요."
            )

        return recommendations

    # ========== 리포트 ==========

    async def _generate_health_report(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """건강 리포트 생성"""
        analysis = await self._analyze_health({})
        checkups = await self._check_checkup_schedule({})
        medications = await self._check_medications({})
        appointments = self.get_upcoming_appointments()

        report = {
            "summary": self._generate_health_summary(analysis),
            "generated_at": datetime.now().isoformat(),
            "health_analysis": analysis,
            "checkups_due": checkups["checkups_due"],
            "medications": medications,
            "upcoming_appointments": appointments,
            "goals_progress": self._get_goals_progress()
        }

        return report

    def _generate_health_summary(self, analysis: Dict[str, Any]) -> str:
        """건강 요약 생성"""
        parts = []

        activity = analysis.get("activity", {})
        if activity.get("avg_daily_steps"):
            parts.append(f"평균 일일 걸음 수: {activity['avg_daily_steps']:,.0f}보")

        sleep = analysis.get("sleep", {})
        if sleep.get("avg_hours"):
            parts.append(f"평균 수면: {sleep['avg_hours']:.1f}시간")

        return " | ".join(parts) if parts else "데이터 부족"

    def _get_goals_progress(self) -> List[Dict[str, Any]]:
        """목표 진행 상황"""
        return [
            {
                "goal": goal.goal_type,
                "target": goal.target_value,
                "current": goal.current_value,
                "progress_pct": goal.progress_pct,
                "unit": goal.unit
            }
            for goal in self.goals.values()
        ]

    # ========== 이벤트 핸들러 ==========

    async def _on_vital_recorded(self, event) -> None:
        """바이탈 기록 이벤트"""
        pass  # 이미 _record_vital에서 처리

    async def _on_medication_time(self, event) -> None:
        """복약 시간 이벤트"""
        med_name = event.data.get("medication")
        self.logger.info(f"복약 알림: {med_name}")

    async def _on_insurance_paid(self, event) -> None:
        """보험료 납부 이벤트 (재정 에이전트로부터)"""
        self.logger.info(
            f"보험료 납부 확인: {event.data.get('bill_name')} - "
            f"{event.data.get('amount'):,}원"
        )

    # ========== 핸들러 함수 ==========

    async def _handle_health_summary(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """건강 요약 요청 처리"""
        analysis = await self._analyze_health({})
        return {
            "summary": self._generate_health_summary(analysis),
            "recommendations": analysis.get("recommendations", [])
        }

    async def _handle_get_vitals(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """바이탈 조회 요청 처리"""
        vital_type = content.get("type")
        days = content.get("days", 7)

        if vital_type:
            return self.get_vital_trend(VitalType(vital_type), days)
        else:
            return {
                vt.value: self.get_vital_trend(vt, days)
                for vt in VitalType
            }

    async def _handle_monthly_report(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """월간 리포트 요청 처리"""
        return await self._generate_health_report(content)

    async def _handle_medication_status(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """복약 상태 요청 처리"""
        return await self._check_medications(content)

    async def _schedule_health_checks(self) -> None:
        """건강 체크 스케줄링"""
        # 복약 알림
        if self.config["medication_reminders"]:
            await self.add_task(
                "check_medications",
                "복약 시간 체크",
                Priority.HIGH
            )

        # 예약 알림
        if self.config["appointment_reminders"]:
            await self.add_task(
                "check_appointments",
                "예약 알림 체크",
                Priority.NORMAL
            )
