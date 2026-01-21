"""
기본 에이전트 클래스
모든 생활 자동화 에이전트의 기반이 되는 추상 클래스입니다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import asyncio
import json
import logging
import uuid


class AgentStatus(Enum):
    """에이전트 상태"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"
    PAUSED = "paused"


class Priority(Enum):
    """작업 우선순위"""
    CRITICAL = 1  # 즉시 처리 (긴급 의료, 보안 위협)
    HIGH = 2      # 높음 (납부 기한, 중요 예약)
    NORMAL = 3    # 보통 (일상 업무)
    LOW = 4       # 낮음 (최적화, 리서치)


@dataclass
class Message:
    """에이전트 간 통신 메시지"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""  # "all"이면 브로드캐스트
    message_type: str = ""  # request, response, event, alert
    subject: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    correlation_id: Optional[str] = None  # 연관된 메시지 추적

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type,
            "subject": self.subject,
            "content": self.content,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "requires_response": self.requires_response,
            "correlation_id": self.correlation_id
        }


@dataclass
class Task:
    """에이전트가 수행하는 작업"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    agent_id: str = ""
    priority: Priority = Priority.NORMAL
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    """시스템 이벤트"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """
    모든 생활 자동화 에이전트의 기본 클래스

    특징:
    - 비동기 작업 처리
    - 이벤트 기반 통신
    - 상태 관리
    - 로깅 및 감사
    """

    def __init__(self, agent_id: str, name: str, description: str = ""):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.coordinator = None  # AgentCoordinator에서 설정

        # 작업 관리
        self.tasks: List[Task] = []
        self.task_queue: asyncio.Queue = asyncio.Queue()

        # 이벤트 핸들러
        self.event_handlers: Dict[str, List[Callable]] = {}

        # 설정 및 상태
        self.config: Dict[str, Any] = {}
        self.state: Dict[str, Any] = {}

        # 로깅
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self._setup_logging()

        # 통계
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "started_at": datetime.now()
        }

    def _setup_logging(self):
        """로깅 설정"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f'[%(asctime)s] [{self.agent_id}] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    # ========== 추상 메서드 (하위 클래스에서 구현) ==========

    @abstractmethod
    async def initialize(self) -> bool:
        """에이전트 초기화"""
        pass

    @abstractmethod
    async def process_task(self, task: Task) -> Any:
        """작업 처리"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """에이전트 기능 목록 반환"""
        pass

    # ========== 통신 메서드 ==========

    async def send_message(self, receiver: str, subject: str,
                          content: Dict[str, Any],
                          message_type: str = "request",
                          priority: Priority = Priority.NORMAL,
                          requires_response: bool = False) -> Optional[Message]:
        """다른 에이전트에게 메시지 전송"""
        message = Message(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            subject=subject,
            content=content,
            priority=priority,
            requires_response=requires_response
        )

        self.logger.info(f"메시지 전송: {receiver}에게 '{subject}'")
        self.stats["messages_sent"] += 1

        if self.coordinator:
            return await self.coordinator.route_message(message)
        return None

    async def broadcast(self, subject: str, content: Dict[str, Any],
                       message_type: str = "event") -> None:
        """모든 에이전트에게 브로드캐스트"""
        await self.send_message("all", subject, content, message_type)

    async def receive_message(self, message: Message) -> Optional[Message]:
        """메시지 수신 처리"""
        self.logger.info(f"메시지 수신: {message.sender}로부터 '{message.subject}'")
        self.stats["messages_received"] += 1

        # 메시지 타입별 처리
        if message.message_type == "request":
            response = await self.handle_request(message)
            if message.requires_response and response:
                response.correlation_id = message.id
                return response
        elif message.message_type == "event":
            await self.handle_event(Event(
                event_type=message.subject,
                source=message.sender,
                data=message.content
            ))
        elif message.message_type == "alert":
            await self.handle_alert(message)

        return None

    async def handle_request(self, message: Message) -> Optional[Message]:
        """요청 메시지 처리 (하위 클래스에서 오버라이드)"""
        return None

    async def handle_alert(self, message: Message) -> None:
        """알림 메시지 처리"""
        self.logger.warning(f"알림: {message.subject} - {message.content}")

    # ========== 이벤트 처리 ==========

    def on(self, event_type: str, handler: Callable) -> None:
        """이벤트 핸들러 등록"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def handle_event(self, event: Event) -> None:
        """이벤트 처리"""
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"이벤트 핸들러 오류: {e}")

    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """이벤트 발생"""
        event = Event(event_type=event_type, source=self.agent_id, data=data)
        await self.handle_event(event)
        await self.broadcast(event_type, data, "event")

    # ========== 작업 관리 ==========

    async def add_task(self, name: str, description: str = "",
                      priority: Priority = Priority.NORMAL,
                      scheduled_at: Optional[datetime] = None,
                      metadata: Dict[str, Any] = None) -> Task:
        """작업 추가"""
        task = Task(
            name=name,
            description=description,
            agent_id=self.agent_id,
            priority=priority,
            scheduled_at=scheduled_at,
            metadata=metadata or {}
        )
        self.tasks.append(task)
        await self.task_queue.put(task)
        self.logger.info(f"작업 추가: {name}")
        return task

    async def run_task(self, task: Task) -> Any:
        """작업 실행"""
        task.status = "running"
        self.status = AgentStatus.WORKING

        try:
            result = await self.process_task(task)
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = result
            self.stats["tasks_completed"] += 1
            self.logger.info(f"작업 완료: {task.name}")
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.stats["tasks_failed"] += 1
            self.logger.error(f"작업 실패: {task.name} - {e}")
            raise
        finally:
            self.status = AgentStatus.IDLE

    async def run(self) -> None:
        """에이전트 메인 루프"""
        self.logger.info(f"에이전트 시작: {self.name}")

        if not await self.initialize():
            self.logger.error("초기화 실패")
            return

        while True:
            try:
                task = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                await self.run_task(task)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"실행 오류: {e}")

    # ========== 유틸리티 ==========

    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 반환"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "tasks_pending": len([t for t in self.tasks if t.status == "pending"]),
            "tasks_running": len([t for t in self.tasks if t.status == "running"]),
            "stats": self.stats,
            "capabilities": self.get_capabilities()
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, status={self.status.value})>"
