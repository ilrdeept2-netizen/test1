# -*- coding: utf-8 -*-
"""
특허 업무 자동화 패키지
Patent Application Automation System
"""

from .prompts import PatentPrompts
from .ai_service import (
    AIServiceManager,
    AIServiceBase,
    OpenAIService,
    AnthropicService,
    GoogleAIService,
    AIResponse,
    PATENT_SYSTEM_PROMPTS
)
from .specification_writer import (
    SpecificationWriter,
    SpecificationSection,
    SpecificationContent,
    PatentSpecification
)
from .drawing_generator import (
    DrawingGenerator,
    Drawing,
    DrawingElement,
    SymbolSystem
)
from .oa_response import (
    OAResponseHandler,
    RejectionType,
    CitedReference,
    RejectionReason,
    AmendedClaim,
    OAResponseDocument
)
from .claims_writer import (
    ClaimsWriter,
    Claim,
    ClaimsSet
)

__version__ = "1.0.0"
__author__ = "Patent Automation System"

__all__ = [
    # Prompts
    "PatentPrompts",

    # AI Service
    "AIServiceManager",
    "AIServiceBase",
    "OpenAIService",
    "AnthropicService",
    "GoogleAIService",
    "AIResponse",
    "PATENT_SYSTEM_PROMPTS",

    # Specification
    "SpecificationWriter",
    "SpecificationSection",
    "SpecificationContent",
    "PatentSpecification",

    # Drawing
    "DrawingGenerator",
    "Drawing",
    "DrawingElement",
    "SymbolSystem",

    # OA Response
    "OAResponseHandler",
    "RejectionType",
    "CitedReference",
    "RejectionReason",
    "AmendedClaim",
    "OAResponseDocument",

    # Claims
    "ClaimsWriter",
    "Claim",
    "ClaimsSet",
]
