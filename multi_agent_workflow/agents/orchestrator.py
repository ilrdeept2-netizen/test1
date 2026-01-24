"""
오케스트레이터 에이전트

전체 워크플로우를 조정하고 에이전트 간 통신을 관리합니다.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from .base_agent import BaseAgent, AgentResult, AgentStatus, AgentMessage


@dataclass
class WorkflowStep:
    """워크플로우 단계 정의"""
    id: str
    agent_name: str
    action: str
    input_mapping: Dict[str, str]
    depends_on: List[str] = None
    parallel: bool = False


@dataclass
class WorkflowContext:
    """워크플로우 실행 컨텍스트"""
    workflow_id: str
    inputs: Dict[str, Any]
    step_results: Dict[str, AgentResult] = None
    status: str = "pending"

    def __post_init__(self):
        if self.step_results is None:
            self.step_results = {}


class OrchestratorAgent(BaseAgent):
    """
    오케스트레이터 에이전트

    전체 워크플로우를 조정하고 에이전트 간 작업을 분배합니다.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="orchestrator",
            system_prompt="""당신은 멀티 에이전트 시스템의 오케스트레이터입니다.
사용자의 요청을 분석하고, 적절한 에이전트에게 작업을 분배하며,
결과를 취합하여 최종 응답을 생성합니다.

사용 가능한 에이전트:
- patent_analyzer: 특허 문서 분석
- patent_searcher: 선행 기술 검색
- document_processor: 문서 형식 변환
- report_generator: 보고서 생성
- news_collector: 뉴스 수집
- quality_validator: 품질 검증

작업 분배 원칙:
1. 작업을 적절한 에이전트에게 분배
2. 의존성이 없는 작업은 병렬 실행
3. 결과를 취합하여 일관된 응답 생성""",
            tools=["read", "write", "edit", "bash", "grep", "glob"],
            **kwargs
        )

        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, List[WorkflowStep]] = {}
        self.active_contexts: Dict[str, WorkflowContext] = {}

    def register_agent(self, agent: BaseAgent) -> None:
        """에이전트를 등록합니다."""
        self.agents[agent.name] = agent
        self.logger.info(f"에이전트 등록: {agent.name}")

    def unregister_agent(self, agent_name: str) -> None:
        """에이전트 등록을 해제합니다."""
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"에이전트 등록 해제: {agent_name}")

    def register_workflow(self, workflow_id: str, steps: List[WorkflowStep]) -> None:
        """워크플로우를 등록합니다."""
        self.workflows[workflow_id] = steps
        self.logger.info(f"워크플로우 등록: {workflow_id}")

    async def process(self, input_data: Any) -> AgentResult:
        """
        사용자 요청을 처리합니다.

        Args:
            input_data: 사용자 입력 또는 워크플로우 컨텍스트

        Returns:
            AgentResult: 처리 결과
        """
        start_time = time.time()
        self.status = AgentStatus.RUNNING

        try:
            # 입력 타입에 따라 처리 방식 결정
            if isinstance(input_data, WorkflowContext):
                result = await self._execute_workflow(input_data)
            elif isinstance(input_data, str):
                result = await self._process_natural_language(input_data)
            elif isinstance(input_data, dict):
                result = await self._process_structured_input(input_data)
            else:
                result = AgentResult(
                    success=False,
                    data=None,
                    error=f"지원하지 않는 입력 타입: {type(input_data)}"
                )

            execution_time = time.time() - start_time
            result.execution_time = execution_time
            self.results.append(result)
            self.status = AgentStatus.COMPLETED

            return result

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"처리 중 오류: {e}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def _process_natural_language(self, prompt: str) -> AgentResult:
        """자연어 입력을 처리합니다."""
        # Claude를 사용하여 작업 분석 및 에이전트 할당
        analysis_prompt = f"""
다음 사용자 요청을 분석하고, 어떤 에이전트(들)에게 작업을 할당할지 결정하세요.

사용자 요청: {prompt}

사용 가능한 에이전트:
- patent_analyzer: 특허 문서 분석
- patent_searcher: 선행 기술 검색
- document_processor: 문서 형식 변환
- report_generator: 보고서 생성
- news_collector: 뉴스 수집
- quality_validator: 품질 검증

다음 형식으로 응답하세요:
1. 작업 분석:
2. 할당할 에이전트:
3. 실행 순서:
4. 예상 결과:
"""

        # Claude API 호출
        response_text = ""
        async for chunk in self.query(analysis_prompt):
            response_text += chunk

        return AgentResult(
            success=True,
            data={
                "analysis": response_text,
                "original_prompt": prompt
            }
        )

    async def _process_structured_input(self, data: dict) -> AgentResult:
        """구조화된 입력을 처리합니다."""
        workflow_id = data.get("workflow_id")
        inputs = data.get("inputs", {})

        if workflow_id and workflow_id in self.workflows:
            context = WorkflowContext(
                workflow_id=workflow_id,
                inputs=inputs
            )
            return await self._execute_workflow(context)
        else:
            return AgentResult(
                success=False,
                data=None,
                error=f"워크플로우를 찾을 수 없습니다: {workflow_id}"
            )

    async def _execute_workflow(self, context: WorkflowContext) -> AgentResult:
        """워크플로우를 실행합니다."""
        workflow_id = context.workflow_id
        steps = self.workflows.get(workflow_id)

        if not steps:
            return AgentResult(
                success=False,
                data=None,
                error=f"워크플로우를 찾을 수 없습니다: {workflow_id}"
            )

        self.active_contexts[workflow_id] = context
        context.status = "running"

        self.logger.info(f"워크플로우 실행 시작: {workflow_id}")

        try:
            # 단계별 실행
            executed_steps = set()

            while len(executed_steps) < len(steps):
                # 실행 가능한 단계 찾기
                ready_steps = []
                for step in steps:
                    if step.id in executed_steps:
                        continue

                    # 의존성 확인
                    dependencies_met = True
                    if step.depends_on:
                        for dep in step.depends_on:
                            if dep not in executed_steps:
                                dependencies_met = False
                                break

                    if dependencies_met:
                        ready_steps.append(step)

                if not ready_steps:
                    break

                # 병렬 실행 가능한 단계들 동시 실행
                parallel_steps = [s for s in ready_steps if s.parallel]
                sequential_steps = [s for s in ready_steps if not s.parallel]

                # 병렬 단계 실행
                if parallel_steps:
                    tasks = [
                        self._execute_step(step, context)
                        for step in parallel_steps
                    ]
                    results = await asyncio.gather(*tasks)
                    for step, result in zip(parallel_steps, results):
                        context.step_results[step.id] = result
                        executed_steps.add(step.id)

                # 순차 단계 실행
                for step in sequential_steps:
                    result = await self._execute_step(step, context)
                    context.step_results[step.id] = result
                    executed_steps.add(step.id)

            context.status = "completed"
            self.logger.info(f"워크플로우 실행 완료: {workflow_id}")

            return AgentResult(
                success=True,
                data=context.step_results,
                metadata={"workflow_id": workflow_id}
            )

        except Exception as e:
            context.status = "error"
            self.logger.error(f"워크플로우 실행 오류: {e}")
            return AgentResult(
                success=False,
                data=context.step_results,
                error=str(e),
                metadata={"workflow_id": workflow_id}
            )

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext
    ) -> AgentResult:
        """개별 워크플로우 단계를 실행합니다."""
        agent = self.agents.get(step.agent_name)

        if not agent:
            return AgentResult(
                success=False,
                data=None,
                error=f"에이전트를 찾을 수 없습니다: {step.agent_name}"
            )

        # 입력 매핑 해석
        step_input = self._resolve_input_mapping(step.input_mapping, context)

        self.logger.info(f"단계 실행: {step.id} (에이전트: {step.agent_name})")

        # 에이전트에 작업 전달
        result = await agent.process(step_input)

        return result

    def _resolve_input_mapping(
        self,
        mapping: Dict[str, str],
        context: WorkflowContext
    ) -> Dict[str, Any]:
        """입력 매핑을 해석합니다."""
        resolved = {}

        for key, value in mapping.items():
            if isinstance(value, str) and value.startswith("${"):
                # 변수 참조 해석
                resolved[key] = self._resolve_variable(value, context)
            else:
                resolved[key] = value

        return resolved

    def _resolve_variable(self, var_expr: str, context: WorkflowContext) -> Any:
        """변수 표현식을 해석합니다."""
        # ${input.xxx} 형식
        if var_expr.startswith("${input."):
            key = var_expr[8:-1]
            return context.inputs.get(key)

        # ${steps.xxx.output} 형식
        if var_expr.startswith("${steps."):
            parts = var_expr[8:-1].split(".")
            step_id = parts[0]
            step_result = context.step_results.get(step_id)
            if step_result and len(parts) > 1:
                return step_result.data
            return step_result

        return var_expr

    async def delegate_task(
        self,
        agent_name: str,
        task: Any
    ) -> AgentResult:
        """특정 에이전트에게 작업을 위임합니다."""
        agent = self.agents.get(agent_name)

        if not agent:
            return AgentResult(
                success=False,
                data=None,
                error=f"에이전트를 찾을 수 없습니다: {agent_name}"
            )

        self.logger.info(f"작업 위임: {agent_name}")
        return await agent.process(task)

    async def broadcast_message(self, content: Any, exclude: List[str] = None) -> None:
        """모든 에이전트에게 메시지를 브로드캐스트합니다."""
        exclude = exclude or []

        for name, agent in self.agents.items():
            if name not in exclude:
                await agent.send_message(name, content)

    def get_agent_status(self) -> Dict[str, str]:
        """모든 에이전트의 상태를 조회합니다."""
        return {
            name: agent.status.value
            for name, agent in self.agents.items()
        }

    def get_workflow_status(self, workflow_id: str) -> Optional[str]:
        """워크플로우 상태를 조회합니다."""
        context = self.active_contexts.get(workflow_id)
        return context.status if context else None
