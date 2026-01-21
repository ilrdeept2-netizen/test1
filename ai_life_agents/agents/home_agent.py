"""
AgentHome - 주거 관리 에이전트
Matt Schlicht의 AgentHome 컨셉을 한국 상황에 맞게 구현

기능:
- 공과금/관리비 자동 납부
- 주택 유지보수 관리
- 스마트홈 제어
- 보안 모니터링
- 청소/세탁 스케줄링
- 해충 방제
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import asyncio

from ..base_agent import BaseAgent, Task, Message, Priority


class MaintenanceType(Enum):
    PLUMBING = "plumbing"         # 배관
    ELECTRICAL = "electrical"     # 전기
    HVAC = "hvac"                # 냉난방
    APPLIANCE = "appliance"      # 가전
    STRUCTURAL = "structural"    # 구조
    PEST_CONTROL = "pest"        # 해충
    CLEANING = "cleaning"        # 청소
    GARDEN = "garden"            # 정원/발코니


class DeviceType(Enum):
    LIGHT = "light"
    THERMOSTAT = "thermostat"
    LOCK = "lock"
    CAMERA = "camera"
    DOORBELL = "doorbell"
    SENSOR = "sensor"
    APPLIANCE = "appliance"
    CURTAIN = "curtain"
    AIR_PURIFIER = "air_purifier"
    ROBOT_VACUUM = "robot_vacuum"


@dataclass
class UtilityBill:
    """공과금"""
    id: str
    utility_type: str  # electricity, gas, water, internet, phone
    amount: Decimal
    usage: float
    usage_unit: str
    billing_period: str
    due_date: date
    status: str = "pending"
    auto_pay: bool = True


@dataclass
class MaintenanceRequest:
    """유지보수 요청"""
    id: str
    maintenance_type: MaintenanceType
    description: str
    urgency: str = "normal"  # urgent, normal, low
    status: str = "pending"  # pending, scheduled, in_progress, completed
    scheduled_date: Optional[datetime] = None
    vendor: str = ""
    estimated_cost: Decimal = Decimal("0")
    actual_cost: Optional[Decimal] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class SmartDevice:
    """스마트홈 기기"""
    id: str
    name: str
    device_type: DeviceType
    location: str  # living_room, bedroom, kitchen, etc.
    status: str = "online"
    current_state: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class HomeEvent:
    """집 관련 이벤트"""
    id: str
    event_type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


class AgentHome(BaseAgent):
    """
    주거 관리 에이전트

    한국 맞춤 기능:
    - 아파트 관리비 분석
    - 한국전력/도시가스 사용량 모니터링
    - 숨고/당근마켓 업체 비교
    - 스마트홈 (삼성 SmartThings, LG ThinQ 등)
    - 쿠팡/마켓컬리 생필품 자동 주문
    """

    def __init__(self, agent_id: str = "home"):
        super().__init__(
            agent_id=agent_id,
            name="AgentHome",
            description="주거 및 가정 관리 에이전트"
        )

        # 데이터 저장소
        self.utility_bills: Dict[str, UtilityBill] = {}
        self.maintenance_requests: Dict[str, MaintenanceRequest] = {}
        self.smart_devices: Dict[str, SmartDevice] = {}
        self.home_events: List[HomeEvent] = []
        self.inventory: Dict[str, Dict[str, Any]] = {}  # 생필품 재고

        # 집 정보
        self.home_profile = {
            "type": "apartment",  # apartment, house, officetel
            "size_sqm": 84,
            "rooms": 3,
            "floor": 15,
            "move_in_date": "2022-03-01",
            "lease_type": "jeonse",  # jeonse, monthly, owned
            "lease_end_date": "2024-02-28",
            "management_office_phone": "02-1234-5678"
        }

        # 설정
        self.config = {
            "auto_pay_utilities": True,
            "energy_saving_mode": True,
            "security_alerts": True,
            "auto_order_supplies": True,
            "cleaning_schedule": "weekly",
            "target_temperature": 24,
            "away_mode": False
        }

        # 공과금 히스토리 (에너지 사용량 분석용)
        self.utility_history: Dict[str, List[Dict[str, Any]]] = {
            "electricity": [],
            "gas": [],
            "water": []
        }

    async def initialize(self) -> bool:
        """초기화"""
        self.logger.info("주거 에이전트 초기화 중...")

        # 이벤트 핸들러 등록
        self.on("motion_detected", self._on_motion_detected)
        self.on("device_offline", self._on_device_offline)
        self.on("energy_spike", self._on_energy_spike)
        self.on("supply_low", self._on_supply_low)

        # 스케줄러 시작
        await self._schedule_home_tasks()

        return True

    def get_capabilities(self) -> List[str]:
        """기능 목록"""
        return [
            "utility_management",      # 공과금 관리
            "maintenance_scheduling",  # 유지보수 스케줄링
            "smart_home_control",     # 스마트홈 제어
            "security_monitoring",    # 보안 모니터링
            "energy_optimization",    # 에너지 최적화
            "cleaning_scheduling",    # 청소 스케줄링
            "supply_management",      # 생필품 관리
            "vendor_coordination",    # 업체 조율
            "lease_management",       # 임대 관리
            "home_report"            # 주거 리포트
        ]

    async def process_task(self, task: Task) -> Any:
        """작업 처리"""
        task_handlers = {
            "pay_utility": self._pay_utility,
            "schedule_maintenance": self._schedule_maintenance,
            "control_device": self._control_device,
            "check_security": self._check_security,
            "optimize_energy": self._optimize_energy,
            "order_supplies": self._order_supplies,
            "find_vendor": self._find_vendor,
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
            "get_utility_summary": self._handle_utility_summary,
            "get_home_status": self._handle_home_status,
            "monthly_report": self._handle_monthly_report,
            "device_status": self._handle_device_status
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

    # ========== 공과금 관리 ==========

    def add_utility_bill(self, bill: UtilityBill) -> None:
        """공과금 추가"""
        self.utility_bills[bill.id] = bill

        # 히스토리에 추가
        if bill.utility_type in self.utility_history:
            self.utility_history[bill.utility_type].append({
                "amount": float(bill.amount),
                "usage": bill.usage,
                "period": bill.billing_period,
                "date": datetime.now().isoformat()
            })

        self.logger.info(
            f"공과금 등록: {bill.utility_type} - {bill.amount:,}원 "
            f"({bill.usage}{bill.usage_unit})"
        )

    async def _pay_utility(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """공과금 납부"""
        bill_id = metadata.get("bill_id")
        bill = self.utility_bills.get(bill_id)

        if not bill:
            return {"success": False, "error": "청구서를 찾을 수 없습니다"}

        # 납부 처리
        self.logger.info(
            f"공과금 납부: {bill.utility_type} - {bill.amount:,}원"
        )
        bill.status = "paid"

        # 재정 에이전트에 알림
        await self.send_message(
            "finance",
            "utility_paid",
            {
                "type": bill.utility_type,
                "amount": float(bill.amount),
                "usage": bill.usage
            }
        )

        return {
            "success": True,
            "utility": bill.utility_type,
            "amount": float(bill.amount)
        }

    def analyze_utility_usage(self, utility_type: str,
                             months: int = 12) -> Dict[str, Any]:
        """공과금 사용량 분석"""
        history = self.utility_history.get(utility_type, [])[-months:]

        if not history:
            return {"no_data": True}

        amounts = [h["amount"] for h in history]
        usages = [h["usage"] for h in history]

        avg_amount = sum(amounts) / len(amounts)
        avg_usage = sum(usages) / len(usages)

        # 전월 대비
        if len(history) >= 2:
            mom_change = (amounts[-1] - amounts[-2]) / amounts[-2] * 100
        else:
            mom_change = 0

        # 전년 동월 대비
        if len(history) >= 12:
            yoy_change = (amounts[-1] - amounts[-12]) / amounts[-12] * 100
        else:
            yoy_change = 0

        return {
            "utility_type": utility_type,
            "months_analyzed": len(history),
            "avg_monthly_amount": avg_amount,
            "avg_monthly_usage": avg_usage,
            "latest_amount": amounts[-1] if amounts else 0,
            "latest_usage": usages[-1] if usages else 0,
            "mom_change_pct": mom_change,
            "yoy_change_pct": yoy_change,
            "trend": "increasing" if mom_change > 10 else "decreasing" if mom_change < -10 else "stable"
        }

    # ========== 유지보수 관리 ==========

    async def _schedule_maintenance(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """유지보수 스케줄링"""
        request = MaintenanceRequest(
            id=f"maint_{datetime.now().timestamp()}",
            maintenance_type=MaintenanceType(metadata.get("type")),
            description=metadata.get("description", ""),
            urgency=metadata.get("urgency", "normal")
        )

        self.maintenance_requests[request.id] = request
        self.logger.info(
            f"유지보수 요청: {request.maintenance_type.value} - {request.description}"
        )

        # 업체 찾기
        if metadata.get("find_vendor", True):
            vendor_result = await self._find_vendor({
                "service_type": request.maintenance_type.value,
                "urgency": request.urgency
            })
            request.vendor = vendor_result.get("recommended_vendor", "")
            request.estimated_cost = Decimal(str(vendor_result.get("estimated_cost", 0)))

        return {
            "scheduled": True,
            "request_id": request.id,
            "vendor": request.vendor,
            "estimated_cost": float(request.estimated_cost)
        }

    async def _find_vendor(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        업체 찾기

        한국 서비스 연동:
        - 숨고
        - 당근마켓
        - 오늘의집
        """
        service_type = metadata.get("service_type")
        urgency = metadata.get("urgency", "normal")

        # 시뮬레이션된 업체 데이터
        vendors = {
            "plumbing": [
                {"name": "행복배관", "rating": 4.8, "price": 80000, "available": True},
                {"name": "서울설비", "rating": 4.5, "price": 70000, "available": True},
            ],
            "electrical": [
                {"name": "스파크전기", "rating": 4.9, "price": 100000, "available": True},
                {"name": "번개전기", "rating": 4.6, "price": 90000, "available": True},
            ],
            "pest": [
                {"name": "세스코", "rating": 4.7, "price": 150000, "available": True},
                {"name": "렌토킬", "rating": 4.5, "price": 130000, "available": True},
            ],
            "cleaning": [
                {"name": "미소", "rating": 4.6, "price": 50000, "available": True},
                {"name": "대리주부", "rating": 4.4, "price": 45000, "available": True},
            ]
        }

        available_vendors = vendors.get(service_type, [])

        if not available_vendors:
            return {"found": False, "message": "해당 서비스 업체를 찾을 수 없습니다"}

        # 평점 순 정렬
        sorted_vendors = sorted(available_vendors, key=lambda x: x["rating"], reverse=True)
        recommended = sorted_vendors[0]

        return {
            "found": True,
            "recommended_vendor": recommended["name"],
            "estimated_cost": recommended["price"],
            "rating": recommended["rating"],
            "alternatives": sorted_vendors[1:3]
        }

    # ========== 스마트홈 제어 ==========

    def register_device(self, device: SmartDevice) -> None:
        """스마트 기기 등록"""
        self.smart_devices[device.id] = device
        self.logger.info(f"기기 등록: {device.name} ({device.location})")

    async def _control_device(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """스마트 기기 제어"""
        device_id = metadata.get("device_id")
        action = metadata.get("action")
        params = metadata.get("params", {})

        device = self.smart_devices.get(device_id)
        if not device:
            return {"success": False, "error": "기기를 찾을 수 없습니다"}

        # 제어 실행 (시뮬레이션)
        self.logger.info(f"기기 제어: {device.name} - {action}")

        # 상태 업데이트
        if action == "turn_on":
            device.current_state["power"] = True
        elif action == "turn_off":
            device.current_state["power"] = False
        elif action == "set_temperature":
            device.current_state["temperature"] = params.get("temperature")
        elif action == "set_brightness":
            device.current_state["brightness"] = params.get("brightness")

        device.last_updated = datetime.now()

        return {
            "success": True,
            "device": device.name,
            "action": action,
            "new_state": device.current_state
        }

    async def set_home_mode(self, mode: str) -> Dict[str, Any]:
        """
        홈 모드 설정

        모드:
        - home: 재실
        - away: 외출
        - sleep: 취침
        - vacation: 휴가
        """
        actions = []

        if mode == "away":
            self.config["away_mode"] = True

            # 조명 끄기
            for device in self.smart_devices.values():
                if device.device_type == DeviceType.LIGHT:
                    await self._control_device({
                        "device_id": device.id,
                        "action": "turn_off"
                    })
                    actions.append(f"{device.name} 끔")

            # 온도 조절 (에너지 절약)
            for device in self.smart_devices.values():
                if device.device_type == DeviceType.THERMOSTAT:
                    await self._control_device({
                        "device_id": device.id,
                        "action": "set_temperature",
                        "params": {"temperature": 18}
                    })
                    actions.append(f"{device.name} 18도로 설정")

            # 보안 카메라 활성화
            for device in self.smart_devices.values():
                if device.device_type == DeviceType.CAMERA:
                    await self._control_device({
                        "device_id": device.id,
                        "action": "turn_on"
                    })
                    actions.append(f"{device.name} 녹화 시작")

        elif mode == "home":
            self.config["away_mode"] = False

            # 적절한 온도로 복원
            for device in self.smart_devices.values():
                if device.device_type == DeviceType.THERMOSTAT:
                    await self._control_device({
                        "device_id": device.id,
                        "action": "set_temperature",
                        "params": {"temperature": self.config["target_temperature"]}
                    })
                    actions.append(f"{device.name} {self.config['target_temperature']}도로 설정")

        elif mode == "sleep":
            # 조명 끄기
            for device in self.smart_devices.values():
                if device.device_type == DeviceType.LIGHT:
                    await self._control_device({
                        "device_id": device.id,
                        "action": "turn_off"
                    })

            # 취침 온도 설정
            for device in self.smart_devices.values():
                if device.device_type == DeviceType.THERMOSTAT:
                    await self._control_device({
                        "device_id": device.id,
                        "action": "set_temperature",
                        "params": {"temperature": 22}  # 취침 적정 온도
                    })

        self.logger.info(f"홈 모드 변경: {mode}")

        return {
            "mode": mode,
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }

    # ========== 보안 모니터링 ==========

    async def _check_security(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """보안 상태 체크"""
        status = {
            "overall": "secure",
            "devices": [],
            "recent_events": [],
            "alerts": []
        }

        # 보안 기기 상태 확인
        for device in self.smart_devices.values():
            if device.device_type in [DeviceType.CAMERA, DeviceType.LOCK, DeviceType.SENSOR]:
                device_status = {
                    "device": device.name,
                    "type": device.device_type.value,
                    "status": device.status,
                    "last_updated": device.last_updated.isoformat()
                }
                status["devices"].append(device_status)

                if device.status != "online":
                    status["alerts"].append(f"{device.name} 오프라인")
                    status["overall"] = "warning"

        # 최근 이벤트
        security_events = [
            e for e in self.home_events[-20:]
            if e.event_type in ["motion_detected", "door_opened", "door_locked"]
        ]
        status["recent_events"] = [
            {
                "type": e.event_type,
                "description": e.description,
                "timestamp": e.timestamp.isoformat()
            }
            for e in security_events
        ]

        return status

    # ========== 에너지 최적화 ==========

    async def _optimize_energy(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        에너지 사용 최적화

        - 전력 피크 시간 회피
        - 대기전력 차단
        - 효율적인 냉난방
        """
        optimizations = []

        # 1. 미사용 기기 대기전력 차단
        for device in self.smart_devices.values():
            if (device.device_type == DeviceType.APPLIANCE and
                device.current_state.get("power") and
                device.current_state.get("idle_minutes", 0) > 30):

                await self._control_device({
                    "device_id": device.id,
                    "action": "turn_off"
                })
                optimizations.append({
                    "action": "standby_power_cut",
                    "device": device.name,
                    "estimated_savings_kwh": 0.5
                })

        # 2. 스마트 온도 조절
        current_hour = datetime.now().hour
        if 23 <= current_hour or current_hour < 6:  # 심야 시간
            for device in self.smart_devices.values():
                if device.device_type == DeviceType.THERMOSTAT:
                    # 심야 전력 활용
                    optimizations.append({
                        "action": "night_heating",
                        "device": device.name,
                        "description": "심야 전력 활용 예열"
                    })

        # 3. 전력 사용량 분석 기반 권장
        electricity_analysis = self.analyze_utility_usage("electricity")
        if electricity_analysis.get("trend") == "increasing":
            optimizations.append({
                "action": "usage_warning",
                "description": "전기 사용량이 증가 추세입니다",
                "recommendation": "에너지 절약 모드 활성화 권장"
            })

        # 재정 에이전트에 절약 정보 공유
        total_savings = sum(o.get("estimated_savings_kwh", 0) for o in optimizations)
        if total_savings > 0:
            await self.send_message(
                "finance",
                "energy_savings",
                {
                    "estimated_kwh_saved": total_savings,
                    "estimated_cost_saved": total_savings * 120  # kWh당 120원 가정
                }
            )

        return {
            "optimizations_applied": optimizations,
            "total_estimated_savings_kwh": total_savings
        }

    # ========== 생필품 관리 ==========

    def update_inventory(self, item: str, quantity: int,
                        threshold: int = 2) -> None:
        """재고 업데이트"""
        self.inventory[item] = {
            "quantity": quantity,
            "threshold": threshold,
            "last_updated": datetime.now().isoformat()
        }

    async def _order_supplies(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        생필품 자동 주문

        한국 서비스 연동:
        - 쿠팡 로켓배송
        - 마켓컬리
        - SSG
        """
        items_to_order = []

        # 재고 부족 아이템 확인
        for item, info in self.inventory.items():
            if info["quantity"] <= info["threshold"]:
                items_to_order.append({
                    "item": item,
                    "current_quantity": info["quantity"],
                    "order_quantity": info["threshold"] * 3  # 여유있게 주문
                })

        if not items_to_order:
            return {"ordered": False, "message": "주문할 품목이 없습니다"}

        # 주문 실행 (시뮬레이션)
        order = {
            "order_id": f"order_{datetime.now().timestamp()}",
            "items": items_to_order,
            "total_estimated_cost": sum(
                item["order_quantity"] * 5000 for item in items_to_order
            ),  # 품목당 5000원 가정
            "service": "쿠팡 로켓배송",
            "estimated_delivery": (datetime.now() + timedelta(days=1)).isoformat()
        }

        self.logger.info(
            f"생필품 주문: {len(items_to_order)}개 품목 - "
            f"{order['total_estimated_cost']:,}원"
        )

        # 재정 에이전트에 알림
        await self.send_message(
            "finance",
            "supply_order_placed",
            {
                "order_id": order["order_id"],
                "amount": order["total_estimated_cost"],
                "items_count": len(items_to_order)
            }
        )

        return {"ordered": True, "order": order}

    # ========== 리포트 ==========

    async def _generate_monthly_report(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """월간 주거 리포트"""
        report = {
            "summary": "",
            "generated_at": datetime.now().isoformat(),
            "utilities": {},
            "maintenance": {},
            "energy": {},
            "security": {},
            "recommendations": []
        }

        # 공과금 분석
        for utility_type in ["electricity", "gas", "water"]:
            report["utilities"][utility_type] = self.analyze_utility_usage(utility_type, 3)

        # 유지보수 현황
        pending = len([r for r in self.maintenance_requests.values() if r.status == "pending"])
        completed = len([r for r in self.maintenance_requests.values() if r.status == "completed"])
        total_cost = sum(
            r.actual_cost or r.estimated_cost
            for r in self.maintenance_requests.values()
            if r.status == "completed"
        )

        report["maintenance"] = {
            "pending_requests": pending,
            "completed_this_month": completed,
            "total_cost": float(total_cost)
        }

        # 에너지 절약
        report["energy"] = await self._optimize_energy({})

        # 보안 현황
        report["security"] = await self._check_security({})

        # 요약 생성
        total_utility = sum(
            report["utilities"].get(u, {}).get("latest_amount", 0)
            for u in ["electricity", "gas", "water"]
        )
        report["summary"] = f"이번 달 공과금: {total_utility:,.0f}원 | 유지보수: {completed}건 완료"

        # 권장 사항
        if report["utilities"].get("electricity", {}).get("trend") == "increasing":
            report["recommendations"].append("전기 사용량이 증가하고 있습니다. 절전 모드를 확인하세요.")

        if pending > 0:
            report["recommendations"].append(f"{pending}건의 유지보수 요청이 대기 중입니다.")

        return report

    # ========== 이벤트 핸들러 ==========

    async def _on_motion_detected(self, event) -> None:
        """움직임 감지"""
        if self.config["away_mode"]:
            self.logger.warning(f"외출 중 움직임 감지: {event.data}")

            # 긴급 알림
            await self.broadcast(
                "security_alert",
                {
                    "type": "motion_detected",
                    "location": event.data.get("location"),
                    "timestamp": datetime.now().isoformat()
                },
                message_type="alert"
            )

    async def _on_device_offline(self, event) -> None:
        """기기 오프라인"""
        device_name = event.data.get("device_name")
        self.logger.warning(f"기기 오프라인: {device_name}")

    async def _on_energy_spike(self, event) -> None:
        """에너지 급증"""
        self.logger.warning(f"에너지 급증 감지: {event.data}")

        # 재정 에이전트에 알림
        await self.send_message(
            "finance",
            "utility_spike_alert",
            {
                "type": "electricity",
                "current_usage": event.data.get("current_usage"),
                "normal_usage": event.data.get("normal_usage")
            }
        )

    async def _on_supply_low(self, event) -> None:
        """생필품 부족"""
        item = event.data.get("item")
        self.logger.info(f"생필품 부족: {item}")

        if self.config["auto_order_supplies"]:
            await self._order_supplies({})

    # ========== 핸들러 함수 ==========

    async def _handle_utility_summary(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """공과금 요약 요청 처리"""
        summary = {}
        for utility_type in ["electricity", "gas", "water"]:
            summary[utility_type] = self.analyze_utility_usage(utility_type, 6)
        return summary

    async def _handle_home_status(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """홈 상태 요청 처리"""
        return {
            "mode": "away" if self.config["away_mode"] else "home",
            "devices_online": len([d for d in self.smart_devices.values() if d.status == "online"]),
            "devices_total": len(self.smart_devices),
            "pending_maintenance": len([r for r in self.maintenance_requests.values() if r.status == "pending"]),
            "security": await self._check_security({})
        }

    async def _handle_monthly_report(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """월간 리포트 요청 처리"""
        return await self._generate_monthly_report(content)

    async def _handle_device_status(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """기기 상태 요청 처리"""
        return {
            "devices": [
                {
                    "id": d.id,
                    "name": d.name,
                    "type": d.device_type.value,
                    "location": d.location,
                    "status": d.status,
                    "state": d.current_state
                }
                for d in self.smart_devices.values()
            ]
        }

    async def _schedule_home_tasks(self) -> None:
        """주거 관리 작업 스케줄링"""
        # 매일 에너지 최적화
        if self.config["energy_saving_mode"]:
            await self.add_task(
                "optimize_energy",
                "에너지 사용 최적화",
                Priority.NORMAL
            )

        # 매주 청소 스케줄
        if self.config["cleaning_schedule"] == "weekly":
            await self.add_task(
                "schedule_cleaning",
                "주간 청소 스케줄링",
                Priority.LOW
            )
