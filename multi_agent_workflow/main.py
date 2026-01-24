#!/usr/bin/env python3
"""
멀티 에이전트 워크플로우 시스템

Claude Agent SDK 기반의 특허 자동화 멀티 에이전트 시스템입니다.

사용법:
    python main.py [command] [options]

명령어:
    run         - 워크플로우 실행
    interactive - 대화형 모드
    status      - 에이전트 상태 확인
    demo        - 데모 실행
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# 경로 설정
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from agents import (
    OrchestratorAgent,
    PatentAnalyzerAgent,
    PatentSearcherAgent,
    DocumentProcessorAgent,
    ReportGeneratorAgent,
    NewsCollectorAgent,
    QualityValidatorAgent,
)
from agents.orchestrator import WorkflowStep, WorkflowContext


def setup_logging(level: str = "INFO") -> None:
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ]
    )


def load_config() -> dict:
    """설정 파일 로드"""
    config_path = ROOT_DIR / "config" / "settings.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


class MultiAgentSystem:
    """멀티 에이전트 시스템"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.logger = logging.getLogger("MultiAgentSystem")

        # 오케스트레이터 초기화
        self.orchestrator = OrchestratorAgent()

        # 에이전트들 초기화 및 등록
        self._init_agents()

        # 워크플로우 등록
        self._init_workflows()

    def _init_agents(self) -> None:
        """에이전트들을 초기화합니다."""
        agents = [
            PatentAnalyzerAgent(),
            PatentSearcherAgent(),
            DocumentProcessorAgent(),
            ReportGeneratorAgent(),
            NewsCollectorAgent(),
            QualityValidatorAgent(),
        ]

        for agent in agents:
            self.orchestrator.register_agent(agent)
            self.logger.info(f"에이전트 등록: {agent.name}")

    def _init_workflows(self) -> None:
        """워크플로우를 등록합니다."""
        # 특허 출원 지원 워크플로우
        patent_application_steps = [
            WorkflowStep(
                id="parse_document",
                agent_name="document_processor",
                action="parse",
                input_mapping={"file": "${input.invention_document}"},
            ),
            WorkflowStep(
                id="search_prior_art",
                agent_name="patent_searcher",
                action="search",
                input_mapping={
                    "content": "${steps.parse_document.output}",
                    "field": "${input.technology_field}"
                },
                depends_on=["parse_document"],
                parallel=True,
            ),
            WorkflowStep(
                id="analyze_patents",
                agent_name="patent_analyzer",
                action="analyze",
                input_mapping={"patents": "${steps.search_prior_art.output}"},
                depends_on=["search_prior_art"],
            ),
            WorkflowStep(
                id="generate_draft",
                agent_name="report_generator",
                action="generate_patent_draft",
                input_mapping={
                    "invention": "${steps.parse_document.output}",
                    "prior_art": "${steps.analyze_patents.output}"
                },
                depends_on=["parse_document", "analyze_patents"],
            ),
            WorkflowStep(
                id="validate",
                agent_name="quality_validator",
                action="validate",
                input_mapping={
                    "document": "${steps.generate_draft.output}",
                    "type": "patent_specification"
                },
                depends_on=["generate_draft"],
            ),
        ]

        self.orchestrator.register_workflow(
            "patent_application_support",
            patent_application_steps
        )

        # 일일 동향 리포트 워크플로우
        daily_report_steps = [
            WorkflowStep(
                id="collect_news",
                agent_name="news_collector",
                action="collect",
                input_mapping={"sources": ["openai", "anthropic", "google_ai"]},
                parallel=True,
            ),
            WorkflowStep(
                id="search_patents",
                agent_name="patent_searcher",
                action="search_recent",
                input_mapping={"date_range": "last_24h"},
                parallel=True,
            ),
            WorkflowStep(
                id="generate_digest",
                agent_name="report_generator",
                action="generate_digest",
                input_mapping={
                    "news": "${steps.collect_news.output}",
                    "patents": "${steps.search_patents.output}"
                },
                depends_on=["collect_news", "search_patents"],
            ),
            WorkflowStep(
                id="validate",
                agent_name="quality_validator",
                action="validate",
                input_mapping={
                    "document": "${steps.generate_digest.output}",
                    "type": "daily_report"
                },
                depends_on=["generate_digest"],
            ),
        ]

        self.orchestrator.register_workflow(
            "daily_trend_report",
            daily_report_steps
        )

        self.logger.info("워크플로우 등록 완료")

    async def run_workflow(
        self,
        workflow_id: str,
        inputs: dict = None
    ):
        """워크플로우를 실행합니다."""
        context = WorkflowContext(
            workflow_id=workflow_id,
            inputs=inputs or {}
        )

        self.logger.info(f"워크플로우 실행: {workflow_id}")
        result = await self.orchestrator.process(context)

        return result

    async def interactive_mode(self) -> None:
        """대화형 모드를 실행합니다."""
        print("\n" + "="*60)
        print("  멀티 에이전트 워크플로우 시스템 - 대화형 모드")
        print("="*60)
        print("\n명령어:")
        print("  /workflow <id>  - 워크플로우 실행")
        print("  /status         - 에이전트 상태 확인")
        print("  /help           - 도움말")
        print("  /quit           - 종료")
        print("\n자연어로 질문하면 오케스트레이터가 적절한 에이전트에게 작업을 분배합니다.")
        print("-"*60 + "\n")

        while True:
            try:
                user_input = input(">>> ").strip()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    # 명령어 처리
                    parts = user_input.split()
                    command = parts[0].lower()

                    if command == "/quit":
                        print("종료합니다.")
                        break

                    elif command == "/status":
                        status = self.orchestrator.get_agent_status()
                        print("\n에이전트 상태:")
                        for name, state in status.items():
                            print(f"  - {name}: {state}")
                        print()

                    elif command == "/workflow":
                        if len(parts) > 1:
                            workflow_id = parts[1]
                            print(f"\n워크플로우 '{workflow_id}' 실행 중...")
                            result = await self.run_workflow(workflow_id)
                            print(f"결과: {result.success}")
                            if result.data:
                                print(json.dumps(result.data, indent=2, ensure_ascii=False)[:1000])
                        else:
                            print("사용법: /workflow <workflow_id>")
                            print("가능한 워크플로우: patent_application_support, daily_trend_report")

                    elif command == "/help":
                        print("\n사용 가능한 명령어:")
                        print("  /workflow <id>  - 워크플로우 실행")
                        print("  /status         - 에이전트 상태 확인")
                        print("  /quit           - 종료")
                        print("\n자연어 예시:")
                        print('  "이 특허 문서를 분석해줘"')
                        print('  "AI 관련 최신 뉴스를 알려줘"')
                        print('  "선행 기술 조사를 해줘"')
                        print()

                    else:
                        print(f"알 수 없는 명령어: {command}")

                else:
                    # 자연어 처리
                    print("\n처리 중...")
                    result = await self.orchestrator.process(user_input)
                    print(f"\n응답:")
                    if result.data:
                        if isinstance(result.data, dict):
                            analysis = result.data.get("analysis", "")
                            print(analysis[:2000] if analysis else json.dumps(result.data, indent=2, ensure_ascii=False)[:2000])
                        else:
                            print(str(result.data)[:2000])
                    print()

            except KeyboardInterrupt:
                print("\n종료합니다.")
                break
            except Exception as e:
                print(f"오류: {e}")

    def get_status(self) -> dict:
        """시스템 상태를 반환합니다."""
        return {
            "orchestrator": self.orchestrator.status.value,
            "agents": self.orchestrator.get_agent_status(),
            "workflows": list(self.orchestrator.workflows.keys()),
        }


async def demo():
    """데모 실행"""
    print("\n" + "="*60)
    print("  멀티 에이전트 워크플로우 시스템 - 데모")
    print("="*60 + "\n")

    system = MultiAgentSystem()

    # 1. 시스템 상태 확인
    print("1. 시스템 상태:")
    status = system.get_status()
    print(f"   - 오케스트레이터: {status['orchestrator']}")
    print(f"   - 등록된 에이전트: {list(status['agents'].keys())}")
    print(f"   - 등록된 워크플로우: {status['workflows']}")
    print()

    # 2. 자연어 처리 테스트
    print("2. 자연어 처리 테스트:")
    test_prompt = "인공지능 관련 선행 특허를 검색해줘"
    print(f"   입력: '{test_prompt}'")
    result = await system.orchestrator.process(test_prompt)
    print(f"   결과: {'성공' if result.success else '실패'}")
    print()

    # 3. 일일 리포트 워크플로우 테스트
    print("3. 일일 리포트 워크플로우 테스트:")
    result = await system.run_workflow("daily_trend_report")
    print(f"   결과: {'성공' if result.success else '실패'}")
    print()

    print("데모 완료!")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="멀티 에이전트 워크플로우 시스템"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="interactive",
        choices=["run", "interactive", "status", "demo"],
        help="실행할 명령"
    )
    parser.add_argument(
        "--workflow",
        "-w",
        help="실행할 워크플로우 ID"
    )
    parser.add_argument(
        "--input",
        "-i",
        help="입력 파일 경로"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨"
    )

    args = parser.parse_args()

    # 로깅 설정
    setup_logging(args.log_level)

    # 설정 로드
    config = load_config()

    # 명령 실행
    if args.command == "demo":
        asyncio.run(demo())

    elif args.command == "status":
        system = MultiAgentSystem(config)
        status = system.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.command == "run":
        if not args.workflow:
            print("오류: --workflow 옵션이 필요합니다.")
            sys.exit(1)

        system = MultiAgentSystem(config)

        inputs = {}
        if args.input:
            if os.path.exists(args.input):
                inputs["file"] = args.input
            else:
                inputs["content"] = args.input

        result = asyncio.run(system.run_workflow(args.workflow, inputs))
        print(json.dumps(result.data, indent=2, ensure_ascii=False) if result.data else result.error)

    else:  # interactive
        system = MultiAgentSystem(config)
        asyncio.run(system.interactive_mode())


if __name__ == "__main__":
    main()
