# -*- coding: utf-8 -*-
"""
특허 명세서 작성 모듈
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import re

from .prompts import PatentPrompts
from .ai_service import AIServiceManager, PATENT_SYSTEM_PROMPTS, AIResponse


class SpecificationSection(Enum):
    """명세서 섹션 열거형"""
    TECHNICAL_FIELD = "기술분야"
    BACKGROUND = "발명의 배경이 되는 기술"
    PROBLEM = "해결하고자 하는 과제"
    SOLUTION = "과제의 해결 수단"
    EFFECT = "발명의 효과"
    DRAWING_DESCRIPTION = "도면의 간단한 설명"
    DETAILED_DESCRIPTION = "발명을 실시하기 위한 구체적인 내용"
    SYMBOL_DESCRIPTION = "부호의 설명"


@dataclass
class SpecificationContent:
    """명세서 내용 데이터 클래스"""
    section: SpecificationSection
    content: str
    version: int = 1
    is_final: bool = False
    notes: str = ""


@dataclass
class PatentSpecification:
    """특허 명세서 전체 데이터 클래스"""
    title: str = ""
    invention_name: str = ""
    sections: Dict[str, SpecificationContent] = field(default_factory=dict)
    drawings: List[Dict] = field(default_factory=list)
    symbol_system: Dict[str, str] = field(default_factory=dict)
    claims: List[str] = field(default_factory=list)
    abstract: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "title": self.title,
            "invention_name": self.invention_name,
            "sections": {k: {"section": v.section.value, "content": v.content,
                           "version": v.version, "is_final": v.is_final}
                        for k, v in self.sections.items()},
            "drawings": self.drawings,
            "symbol_system": self.symbol_system,
            "claims": self.claims,
            "abstract": self.abstract,
            "metadata": self.metadata
        }

    def to_formatted_text(self) -> str:
        """포맷된 텍스트로 변환"""
        output = []

        if self.invention_name:
            output.append(f"【발명의 명칭】\n{self.invention_name}\n")

        section_order = [
            SpecificationSection.TECHNICAL_FIELD,
            SpecificationSection.BACKGROUND,
            SpecificationSection.PROBLEM,
            SpecificationSection.SOLUTION,
            SpecificationSection.EFFECT,
            SpecificationSection.DRAWING_DESCRIPTION,
            SpecificationSection.DETAILED_DESCRIPTION,
            SpecificationSection.SYMBOL_DESCRIPTION
        ]

        for section in section_order:
            if section.name in self.sections:
                content = self.sections[section.name]
                output.append(f"【{section.value}】\n{content.content}\n")

        if self.claims:
            output.append("【청구범위】")
            for i, claim in enumerate(self.claims, 1):
                output.append(f"【청구항 {i}】\n{claim}\n")

        if self.abstract:
            output.append(f"【요약서】\n{self.abstract}\n")

        return "\n".join(output)


class SpecificationWriter:
    """특허 명세서 작성 클래스"""

    def __init__(self, ai_manager: Optional[AIServiceManager] = None):
        self.ai_manager = ai_manager or AIServiceManager()
        self.prompts = PatentPrompts()
        self.specification = PatentSpecification()

    def set_invention_info(self, title: str, name: str = ""):
        """발명 정보 설정"""
        self.specification.title = title
        self.specification.invention_name = name or title

    def set_symbol_system(self, symbols: Dict[str, str]):
        """부호체계 설정"""
        self.specification.symbol_system = symbols

    def set_drawings(self, drawings: List[Dict]):
        """도면 정보 설정"""
        self.specification.drawings = drawings

    def _apply_writing_style(self, text: str) -> str:
        """서술 방식 적용"""
        # 접속사 제거
        connectors = ['그리고', '게다가', '나아가', '또한', '이처럼', '따라서', '그러므로', '그러나']
        for conn in connectors:
            text = re.sub(rf'\s*{conn}\s*,?\s*', ' ', text)

        # 지시어 최소화 (문맥에 따라 유지해야 할 경우도 있어 완전 제거는 안 함)
        # '상기'는 특허 명세서에서 자주 사용되므로 유지

        return text.strip()

    def write_section(self, section: SpecificationSection, context: str,
                     provider: str = None, additional_prompt: str = "") -> AIResponse:
        """명세서 섹션 작성"""

        # 섹션별 프롬프트 구성
        prompts_to_use = []
        system_prompt = PATENT_SYSTEM_PROMPTS["specification"]

        if section == SpecificationSection.TECHNICAL_FIELD:
            base_prompt = f"""
다음 발명에 대한 【기술분야】를 작성해주세요.

발명 정보:
{context}

작성 지침:
- 본 발명이 속하는 기술분야를 간결하게 기술
- 1-2문장으로 작성
"""

        elif section == SpecificationSection.BACKGROUND:
            base_prompt = f"""
다음 발명에 대한 【발명의 배경이 되는 기술】을 작성해주세요.

발명 정보:
{context}

작성 지침:
- 최소한도의 핵심적인 내용만 기재
- 본 발명의 권리범위에 영향을 주지 않도록 간결하게 작성
- 종래 기술의 문제점 암시 정도만 언급
"""

        elif section == SpecificationSection.PROBLEM:
            base_prompt = f"""
다음 발명에 대한 【해결하고자 하는 과제】를 작성해주세요.

발명 정보:
{context}

작성 지침:
- 간단히 핵심 단락만 작성
- 발명이 해결하고자 하는 기술적 과제를 명확히 기술
- 1-2 단락으로 간결하게
"""

        elif section == SpecificationSection.EFFECT:
            base_prompt = f"""
다음 발명에 대한 【발명의 효과】를 작성해주세요.

발명 정보:
{context}

작성 지침:
- 본 발명의 효과를 상세하게 작성
- 구체적인 기술적 효과를 모두 열거
- 추상적 표현 대신 구체적인 현상/결과 위주로 서술
"""

        elif section == SpecificationSection.DRAWING_DESCRIPTION:
            drawings_info = "\n".join([f"도 {d.get('number', i+1)}: {d.get('description', '')}"
                                       for i, d in enumerate(self.specification.drawings)])
            base_prompt = f"""
다음 도면들에 대한 【도면의 간단한 설명】을 작성해주세요.

도면 목록:
{drawings_info}

발명 정보:
{context}

작성 지침:
- 각 도면이 무엇을 나타내는지 간결하게 기술
- "도 X는 ~을 나타내는 도면이다." 형식으로 작성
"""

        elif section == SpecificationSection.DETAILED_DESCRIPTION:
            symbol_info = "\n".join([f"{k}: {v}" for k, v in self.specification.symbol_system.items()])
            base_prompt = f"""
다음 발명에 대한 【발명을 실시하기 위한 구체적인 내용】을 작성해주세요.

발명 정보:
{context}

부호체계:
{symbol_info}

작성 지침:
- 아주 상세하고 구체적으로 작성
- 구성요소가 왜 그 위치에 있어야 하는지 '필연적 이유'와 '발명의 효과'를 중심으로 인과관계 서술
- 도면 번호와 부호를 적극 활용
- 동작/메커니즘/효과 측면에서 기술적 묘사
"""

        elif section == SpecificationSection.SYMBOL_DESCRIPTION:
            symbol_info = "\n".join([f"{k}: {v}" for k, v in self.specification.symbol_system.items()])
            base_prompt = f"""
다음 부호체계에 대한 【부호의 설명】을 작성해주세요.

부호체계:
{symbol_info}

작성 지침:
- "부호 - 명칭" 형식으로 나열
"""

        else:
            base_prompt = f"""
【{section.value}】 항목을 작성해주세요.

발명 정보:
{context}
"""

        # 서술 방식 지침 추가
        full_prompt = base_prompt + "\n\n" + PatentPrompts.WRITING_STYLE_TRANSLATION_FRIENDLY

        if additional_prompt:
            full_prompt += f"\n\n추가 지침:\n{additional_prompt}"

        # AI 호출
        response = self.ai_manager.generate(
            full_prompt,
            provider=provider,
            system_prompt=system_prompt,
            max_tokens=4096
        )

        # 서술 방식 적용
        processed_content = self._apply_writing_style(response.content)

        # 섹션 저장
        self.specification.sections[section.name] = SpecificationContent(
            section=section,
            content=processed_content
        )

        return response

    def write_all_sections(self, context: str, provider: str = None) -> Dict[str, AIResponse]:
        """모든 섹션 작성"""
        sections_to_write = [
            SpecificationSection.TECHNICAL_FIELD,
            SpecificationSection.BACKGROUND,
            SpecificationSection.PROBLEM,
            SpecificationSection.EFFECT,
            SpecificationSection.DRAWING_DESCRIPTION,
            SpecificationSection.DETAILED_DESCRIPTION
        ]

        results = {}
        for section in sections_to_write:
            response = self.write_section(section, context, provider)
            results[section.name] = response

        return results

    def review_section(self, section: SpecificationSection, provider: str = None) -> AIResponse:
        """섹션 검토 및 보완"""
        if section.name not in self.specification.sections:
            raise ValueError(f"섹션이 존재하지 않습니다: {section.value}")

        current_content = self.specification.sections[section.name].content

        prompt = f"""
다음 특허 명세서 섹션을 검토하고 보완해주세요.

현재 【{section.value}】 내용:
{current_content}

검토 지침:
1. 추가하거나 보완할 수정 사항 확인
2. 본 발명의 차별성 있는 핵심특징에 대한 기술적 묘사 보완
3. 동작/메커니즘/효과 측면 보강
4. 정확히 삽입될 단락 위치 명시

{PatentPrompts.WRITING_STYLE_TRANSLATION_FRIENDLY}
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["specification"],
            max_tokens=4096
        )

        return response

    def supplement_from_inventor_draft(self, inventor_draft: str, provider: str = None) -> AIResponse:
        """발명자 초안 검토 및 보완"""
        current_spec = self.specification.to_formatted_text()

        prompt = f"""
{PatentPrompts.INVENTOR_DRAFT_COMPARISON}

발명자 제공 원본 초안:
{inventor_draft}

현재 작성된 명세서:
{current_spec}

검토 지침:
1. 발명자가 제공한 원본 초안과 대조
2. 특허 등록 및 권리 범위 방어에 유리한 구체적 특징 내용이 누락되거나 축소된 부분 확인
3. 발명자가 보내준 내용 중 살릴 내용 파악
4. 추가하거나 보완할 내용을 단락 형태로 작성
"""

        response = self.ai_manager.generate(
            prompt,
            provider=provider,
            system_prompt=PATENT_SYSTEM_PROMPTS["specification"],
            max_tokens=4096
        )

        return response

    def get_specification(self) -> PatentSpecification:
        """현재 명세서 반환"""
        return self.specification

    def export_to_text(self) -> str:
        """텍스트로 내보내기"""
        return self.specification.to_formatted_text()

    def export_to_json(self) -> str:
        """JSON으로 내보내기"""
        return json.dumps(self.specification.to_dict(), ensure_ascii=False, indent=2)
