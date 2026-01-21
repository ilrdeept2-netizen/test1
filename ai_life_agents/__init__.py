"""
AI 생활 자동화 에이전트 시스템
================================
Matt Schlicht의 AgentWealth, AgentHealth, AgentHome 컨셉을 기반으로
한국 상황에 맞게 설계된 AI 생활 자동화 에이전트 프레임워크입니다.

에이전트 종류:
- AgentFinance: 재정/자산 관리 (청구서, 카드, 투자, 절약)
- AgentHealth: 건강 관리 (바이탈, 식단, 검진, 의료)
- AgentHome: 주거 관리 (공과금, 수리, 청소, 보안)
- AgentTime: 시간/일정 관리 (스케줄, 알림, 생산성)
- AgentSocial: 관계 관리 (경조사, 연락, 선물)

핵심 특징:
- 에이전트 간 실시간 통신
- 이벤트 기반 협업
- 한국 서비스 API 연동 (토스, 카카오, 네이버 등)
"""

from .base_agent import BaseAgent
from .coordinator import AgentCoordinator
from .agents import (
    AgentFinance,
    AgentHealth,
    AgentHome,
    AgentTime,
    AgentSocial
)

__version__ = "1.0.0"
__all__ = [
    "BaseAgent",
    "AgentCoordinator",
    "AgentFinance",
    "AgentHealth",
    "AgentHome",
    "AgentTime",
    "AgentSocial"
]
