"""
에이전트 코디네이터
모든 에이전트 간의 통신과 협업을 관리합니다.
"""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
import json
import logging

from .base_agent import BaseAgent, Message, Event, Priority, Task


class AgentCoordinator:
    """
    에이전트 코디네이터

    역할:
    - 에이전트 등록 및 관리
    - 메시지 라우팅
    - 협업 작업 조율
    - 시스템 모니터링
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_log: List[Message] = []
        self.event_log: List[Event] = []
        self.running = False

        # 메시지 큐 (우선순위별)
        self.message_queues: Dict[Priority, asyncio.Queue] = {
            p: asyncio.Queue() for p in Priority
        }

        # 협업 규칙
        self.collaboration_rules: List[Dict[str, Any]] = []

        # 로깅
        self.logger = logging.getLogger("coordinator")
        self._setup_logging()

    def _setup_logging(self):
        """로깅 설정"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] [Coordinator] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    # ========== 에이전트 관리 ==========

    def register_agent(self, agent: BaseAgent) -> None:
        """에이전트 등록"""
        agent.coordinator = self
        self.agents[agent.agent_id] = agent
        self.logger.info(f"에이전트 등록: {agent.name} ({agent.agent_id})")

    def unregister_agent(self, agent_id: str) -> None:
        """에이전트 등록 해제"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.logger.info(f"에이전트 해제: {agent_id}")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """에이전트 조회"""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """모든 에이전트 목록"""
        return [agent.get_status() for agent in self.agents.values()]

    # ========== 메시지 라우팅 ==========

    async def route_message(self, message: Message) -> Optional[Message]:
        """메시지 라우팅"""
        self.message_log.append(message)

        if message.receiver == "all":
            # 브로드캐스트
            await self._broadcast_message(message)
            return None
        elif message.receiver in self.agents:
            # 특정 에이전트에게 전달
            return await self._deliver_message(message)
        else:
            self.logger.warning(f"알 수 없는 수신자: {message.receiver}")
            return None

    async def _deliver_message(self, message: Message) -> Optional[Message]:
        """메시지 전달"""
        agent = self.agents[message.receiver]
        response = await agent.receive_message(message)
        return response

    async def _broadcast_message(self, message: Message) -> None:
        """브로드캐스트 메시지"""
        for agent_id, agent in self.agents.items():
            if agent_id != message.sender:
                await agent.receive_message(message)

    # ========== 협업 관리 ==========

    def add_collaboration_rule(self, trigger_event: str,
                               source_agent: str,
                               target_agent: str,
                               action: str,
                               conditions: Dict[str, Any] = None) -> None:
        """
        협업 규칙 추가

        예시:
        - 건강 이상 감지 시 -> 재정 에이전트에 보험 청구 요청
        - 급여 입금 시 -> 재정 에이전트가 자동 투자 실행
        - 전기요금 폭등 시 -> 주거 에이전트가 절전 모드 활성화
        """
        rule = {
            "id": f"rule_{len(self.collaboration_rules)}",
            "trigger_event": trigger_event,
            "source_agent": source_agent,
            "target_agent": target_agent,
            "action": action,
            "conditions": conditions or {},
            "created_at": datetime.now().isoformat()
        }
        self.collaboration_rules.append(rule)
        self.logger.info(f"협업 규칙 추가: {trigger_event} -> {action}")

    async def check_collaboration_rules(self, event: Event) -> None:
        """이벤트 발생 시 협업 규칙 확인"""
        for rule in self.collaboration_rules:
            if (rule["trigger_event"] == event.event_type and
                (rule["source_agent"] == event.source or rule["source_agent"] == "*")):

                # 조건 확인
                if self._check_conditions(rule["conditions"], event.data):
                    await self._execute_collaboration(rule, event)

    def _check_conditions(self, conditions: Dict[str, Any],
                         data: Dict[str, Any]) -> bool:
        """협업 조건 확인"""
        for key, expected in conditions.items():
            if key not in data:
                return False
            if isinstance(expected, dict):
                op = expected.get("op", "eq")
                value = expected.get("value")
                actual = data[key]

                if op == "gt" and not (actual > value):
                    return False
                elif op == "lt" and not (actual < value):
                    return False
                elif op == "eq" and actual != value:
                    return False
                elif op == "contains" and value not in actual:
                    return False
            elif data[key] != expected:
                return False
        return True

    async def _execute_collaboration(self, rule: Dict[str, Any],
                                    event: Event) -> None:
        """협업 실행"""
        target_agent = self.agents.get(rule["target_agent"])
        if target_agent:
            self.logger.info(
                f"협업 실행: {event.event_type} -> {rule['action']} "
                f"(대상: {rule['target_agent']})"
            )
            message = Message(
                sender="coordinator",
                receiver=rule["target_agent"],
                message_type="request",
                subject=rule["action"],
                content={
                    "trigger_event": event.event_type,
                    "event_data": event.data,
                    "rule_id": rule["id"]
                },
                priority=Priority.HIGH
            )
            await target_agent.receive_message(message)

    # ========== 협업 시나리오 ==========

    async def coordinate_monthly_review(self) -> Dict[str, Any]:
        """
        월간 종합 리뷰 조율
        모든 에이전트로부터 월간 보고서를 수집하고 종합합니다.
        """
        reports = {}

        for agent_id, agent in self.agents.items():
            message = Message(
                sender="coordinator",
                receiver=agent_id,
                message_type="request",
                subject="monthly_report",
                content={"month": datetime.now().month},
                requires_response=True
            )
            response = await agent.receive_message(message)
            if response:
                reports[agent_id] = response.content

        return {
            "type": "monthly_review",
            "date": datetime.now().isoformat(),
            "reports": reports,
            "summary": self._generate_summary(reports)
        }

    def _generate_summary(self, reports: Dict[str, Any]) -> str:
        """종합 요약 생성"""
        summary_parts = []

        for agent_id, report in reports.items():
            if report:
                summary_parts.append(f"- {agent_id}: {report.get('summary', 'N/A')}")

        return "\n".join(summary_parts) if summary_parts else "보고서 없음"

    async def handle_emergency(self, emergency_type: str,
                              data: Dict[str, Any]) -> None:
        """
        긴급 상황 처리

        예시:
        - 건강 응급상황 -> 모든 에이전트 알림
        - 보안 위협 -> 주거 에이전트 우선 대응
        - 금융 사기 의심 -> 재정 에이전트 계정 동결
        """
        self.logger.warning(f"긴급 상황 발생: {emergency_type}")

        alert_message = Message(
            sender="coordinator",
            receiver="all",
            message_type="alert",
            subject=f"emergency_{emergency_type}",
            content=data,
            priority=Priority.CRITICAL
        )

        await self._broadcast_message(alert_message)

    # ========== 실행 관리 ==========

    async def start(self) -> None:
        """코디네이터 및 모든 에이전트 시작"""
        self.running = True
        self.logger.info("코디네이터 시작")

        # 모든 에이전트 초기화
        for agent in self.agents.values():
            await agent.initialize()

        # 메시지 처리 루프 시작
        await self._message_loop()

    async def _message_loop(self) -> None:
        """메시지 처리 루프"""
        while self.running:
            # 우선순위 순서로 메시지 처리
            for priority in Priority:
                queue = self.message_queues[priority]
                if not queue.empty():
                    message = await queue.get()
                    await self.route_message(message)

            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        """코디네이터 중지"""
        self.running = False
        self.logger.info("코디네이터 중지")

    # ========== 모니터링 ==========

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 전체 상태"""
        return {
            "running": self.running,
            "agents_count": len(self.agents),
            "agents": self.list_agents(),
            "rules_count": len(self.collaboration_rules),
            "messages_processed": len(self.message_log),
            "events_processed": len(self.event_log)
        }

    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """메시지 히스토리"""
        return [m.to_dict() for m in self.message_log[-limit:]]

    def export_logs(self, filepath: str) -> None:
        """로그 내보내기"""
        data = {
            "messages": [m.to_dict() for m in self.message_log],
            "events": [
                {
                    "id": e.id,
                    "type": e.event_type,
                    "source": e.source,
                    "data": e.data,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in self.event_log
            ],
            "exported_at": datetime.now().isoformat()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
