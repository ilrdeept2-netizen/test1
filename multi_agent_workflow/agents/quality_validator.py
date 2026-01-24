"""
품질 검증 에이전트

출력물의 품질을 검증하고 오류를 수정합니다.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentResult, AgentStatus


@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    score: float
    issues: List[str]
    suggestions: List[str]


class QualityValidatorAgent(BaseAgent):
    """
    품질 검증 에이전트

    생성된 문서와 보고서의 품질을 검증하고,
    형식 오류, 내용 불일치 등을 감지하여 수정합니다.
    """

    # 검증 규칙
    VALIDATION_RULES = {
        "patent_specification": {
            "required_sections": [
                "발명의 명칭",
                "기술분야",
                "청구범위",
                "요약서"
            ],
            "min_claims": 1,
            "max_abstract_length": 150,
            "forbidden_words": ["절대", "완벽한", "최고의"]
        },
        "daily_report": {
            "required_sections": ["뉴스", "특허"],
            "min_items": 3,
            "max_length": 10000
        },
        "legal_document": {
            "required_sections": ["개요", "분석", "결론"],
            "formal_language": True,
            "citation_required": True
        }
    }

    def __init__(self, **kwargs):
        super().__init__(
            name="quality_validator",
            model="claude-sonnet-4-20250514",
            system_prompt="""당신은 품질 관리 전문가입니다.
생성된 문서와 보고서의 품질을 검증하고,
형식 오류, 내용 불일치 등을 감지하여 수정합니다.

검증 항목:
- 형식 규격 준수 여부
- 내용 일관성
- 법률/기술 용어 정확성
- 참조 및 인용 정확성
- 맞춤법 및 문법

검증 기준:
1. 필수 섹션 포함 여부
2. 내용의 완결성
3. 용어의 일관성
4. 형식의 표준 준수
5. 가독성""",
            tools=["read", "grep", "edit"],
            **kwargs
        )

    async def process(self, input_data: Any) -> AgentResult:
        """
        문서를 검증합니다.

        Args:
            input_data: 검증할 문서 또는 설정

        Returns:
            AgentResult: 검증 결과
        """
        self.status = AgentStatus.RUNNING

        try:
            if isinstance(input_data, dict):
                document = input_data.get("document", "")
                doc_type = input_data.get("type", "general")
            else:
                document = str(input_data)
                doc_type = "general"

            # 검증 수행
            validation = await self._validate_document(document, doc_type)

            # 수정 제안 생성
            if not validation.is_valid:
                corrected = await self._suggest_corrections(document, validation.issues)
            else:
                corrected = document

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data={
                    "is_valid": validation.is_valid,
                    "score": validation.score,
                    "issues": validation.issues,
                    "suggestions": validation.suggestions,
                    "corrected_document": corrected
                }
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"검증 오류: {e}")
            return AgentResult(success=False, data=None, error=str(e))

    async def _validate_document(
        self,
        document: str,
        doc_type: str
    ) -> ValidationResult:
        """문서를 검증합니다."""
        issues = []
        suggestions = []
        score = 100.0

        # 규칙 기반 검증
        rules = self.VALIDATION_RULES.get(doc_type, {})

        # 필수 섹션 검사
        required_sections = rules.get("required_sections", [])
        for section in required_sections:
            if section not in document:
                issues.append(f"필수 섹션 누락: {section}")
                suggestions.append(f"'{section}' 섹션을 추가하세요.")
                score -= 10

        # 금지어 검사
        forbidden_words = rules.get("forbidden_words", [])
        for word in forbidden_words:
            if word in document:
                issues.append(f"부적절한 표현: {word}")
                suggestions.append(f"'{word}'을(를) 더 객관적인 표현으로 바꾸세요.")
                score -= 5

        # 길이 검사
        max_length = rules.get("max_length")
        if max_length and len(document) > max_length:
            issues.append(f"문서가 너무 깁니다 ({len(document)} > {max_length})")
            suggestions.append("문서를 간결하게 요약하세요.")
            score -= 5

        # AI 기반 검증
        ai_validation = await self._ai_validate(document, doc_type)
        issues.extend(ai_validation.get("issues", []))
        suggestions.extend(ai_validation.get("suggestions", []))
        score -= ai_validation.get("penalty", 0)

        # 점수 보정
        score = max(0, min(100, score))

        return ValidationResult(
            is_valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=suggestions
        )

    async def _ai_validate(
        self,
        document: str,
        doc_type: str
    ) -> Dict[str, Any]:
        """AI를 사용하여 문서를 검증합니다."""
        validate_prompt = f"""
다음 {doc_type} 문서를 검토하고 품질 문제를 찾아주세요.

문서:
{document[:5000]}

검토 항목:
1. 문법 및 맞춤법 오류
2. 논리적 일관성
3. 용어의 정확성
4. 형식의 적절성
5. 내용의 완결성

발견된 문제와 개선 제안을 JSON 형식으로 반환하세요:
{{
    "issues": ["문제1", "문제2"],
    "suggestions": ["제안1", "제안2"],
    "penalty": 0-20
}}
"""

        response = ""
        async for chunk in self.query(validate_prompt):
            response += chunk

        # JSON 파싱 시도
        try:
            import json
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        return {"issues": [], "suggestions": [], "penalty": 0}

    async def _suggest_corrections(
        self,
        document: str,
        issues: List[str]
    ) -> str:
        """수정 사항을 제안합니다."""
        correction_prompt = f"""
다음 문서에서 발견된 문제를 수정하세요.

원본 문서:
{document[:5000]}

발견된 문제:
{issues}

수정된 문서를 반환하세요.
"""

        corrected = ""
        async for chunk in self.query(correction_prompt):
            corrected += chunk

        return corrected

    async def validate(
        self,
        document: Any,
        doc_type: str = "general"
    ) -> AgentResult:
        """문서를 검증합니다 (명시적 메서드)."""
        return await self.process({
            "document": document if isinstance(document, str) else str(document),
            "type": doc_type
        })

    async def batch_validate(
        self,
        documents: List[Dict[str, Any]]
    ) -> AgentResult:
        """여러 문서를 일괄 검증합니다."""
        self.status = AgentStatus.RUNNING
        results = []

        try:
            for doc_info in documents:
                doc = doc_info.get("content", "")
                doc_type = doc_info.get("type", "general")

                validation = await self._validate_document(doc, doc_type)
                results.append({
                    "document": doc_info.get("name", "unknown"),
                    "is_valid": validation.is_valid,
                    "score": validation.score,
                    "issues": validation.issues
                })

            # 전체 통계
            avg_score = sum(r["score"] for r in results) / len(results) if results else 0
            all_valid = all(r["is_valid"] for r in results)

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data={
                    "results": results,
                    "summary": {
                        "total": len(results),
                        "valid": sum(1 for r in results if r["is_valid"]),
                        "average_score": avg_score,
                        "all_valid": all_valid
                    }
                }
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            return AgentResult(success=False, data=results, error=str(e))
