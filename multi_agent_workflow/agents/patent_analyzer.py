"""
특허 분석 에이전트

특허 문서를 분석하고 핵심 내용을 추출합니다.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentResult, AgentStatus


@dataclass
class PatentAnalysis:
    """특허 분석 결과"""
    title: str
    abstract: str
    claims: List[str]
    technology_field: str
    key_features: List[str]
    prior_art_references: List[str]
    ipc_codes: List[str]


class PatentAnalyzerAgent(BaseAgent):
    """
    특허 분석 에이전트

    특허 명세서의 구조를 분석하고, 청구항을 해석하며,
    기술 분야를 분류합니다.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="patent_analyzer",
            model="claude-sonnet-4-20250514",
            system_prompt="""당신은 특허 분석 전문가입니다.
특허 명세서의 구조를 분석하고, 청구항을 해석하며,
기술 분야를 분류하는 역할을 합니다.

분석 항목:
- 발명의 명칭 및 기술 분야
- 청구항 범위 및 종속 관계
- 핵심 기술 요소
- 선행 기술과의 차별점

한국 특허 명세서의 표준 구조:
1. 발명의 명칭
2. 기술분야
3. 발명의 배경이 되는 기술
4. 발명의 내용
5. 도면의 간단한 설명
6. 발명을 실시하기 위한 구체적인 내용
7. 청구범위
8. 요약서""",
            tools=["read", "grep", "bash"],
            **kwargs
        )

    async def process(self, input_data: Any) -> AgentResult:
        """
        특허 문서를 분석합니다.

        Args:
            input_data: 특허 문서 내용 또는 파일 경로

        Returns:
            AgentResult: 분석 결과
        """
        self.status = AgentStatus.RUNNING

        try:
            # 입력 타입에 따라 처리
            if isinstance(input_data, str):
                if input_data.endswith(('.docx', '.pdf', '.txt')):
                    content = await self.execute_tool("read", file_path=input_data)
                else:
                    content = input_data
            elif isinstance(input_data, dict):
                content = input_data.get("content", "")
            else:
                content = str(input_data)

            # 특허 분석 수행
            analysis = await self._analyze_patent(content)

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data=analysis,
                metadata={"type": "patent_analysis"}
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"특허 분석 오류: {e}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def _analyze_patent(self, content: str) -> Dict[str, Any]:
        """특허 내용을 분석합니다."""
        analysis_prompt = f"""
다음 특허 문서를 분석하여 구조화된 정보를 추출하세요.

특허 문서:
{content[:10000]}  # 길이 제한

다음 항목을 추출하세요:
1. 발명의 명칭
2. 기술 분야
3. 요약
4. 청구항 목록 (각 청구항의 범위와 종속 관계 포함)
5. 핵심 기술 요소
6. 선행 기술 참조
7. IPC 분류 코드

JSON 형식으로 응답하세요.
"""

        response = ""
        async for chunk in self.query(analysis_prompt):
            response += chunk

        # 기본 분석 결과 구성
        analysis = {
            "title": self._extract_title(content),
            "technology_field": self._extract_tech_field(content),
            "abstract": self._extract_abstract(content),
            "claims": self._extract_claims(content),
            "key_features": [],
            "prior_art_references": [],
            "ipc_codes": self._extract_ipc_codes(content),
            "ai_analysis": response
        }

        return analysis

    def _extract_title(self, content: str) -> str:
        """발명의 명칭을 추출합니다."""
        patterns = [
            r"발명의\s*명칭[:\s]*(.+?)(?:\n|$)",
            r"제목[:\s]*(.+?)(?:\n|$)",
            r"Title[:\s]*(.+?)(?:\n|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "제목 없음"

    def _extract_tech_field(self, content: str) -> str:
        """기술 분야를 추출합니다."""
        patterns = [
            r"기술\s*분야[:\s]*(.+?)(?:\n\n|\n[가-힣])",
            r"Technical\s*Field[:\s]*(.+?)(?:\n\n|\n[A-Z])",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:500]
        return "분류 없음"

    def _extract_abstract(self, content: str) -> str:
        """요약을 추출합니다."""
        patterns = [
            r"요약서?[:\s]*(.+?)(?:\n\n|\n청구)",
            r"Abstract[:\s]*(.+?)(?:\n\n|\nClaim)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:1000]
        return ""

    def _extract_claims(self, content: str) -> List[str]:
        """청구항을 추출합니다."""
        claims = []
        patterns = [
            r"청구항\s*(\d+)[.:\s]*(.+?)(?=청구항\s*\d+|$)",
            r"Claim\s*(\d+)[.:\s]*(.+?)(?=Claim\s*\d+|$)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            if matches:
                for num, text in matches:
                    claims.append({
                        "number": int(num),
                        "text": text.strip()[:500],
                        "type": "independent" if "항에 있어서" not in text else "dependent"
                    })
                break

        return claims

    def _extract_ipc_codes(self, content: str) -> List[str]:
        """IPC 분류 코드를 추출합니다."""
        pattern = r"[A-H]\d{2}[A-Z]\s*\d+/\d+"
        matches = re.findall(pattern, content)
        return list(set(matches))

    async def analyze_claims(self, patent_data: Dict[str, Any]) -> Dict[str, Any]:
        """청구항을 상세 분석합니다."""
        claims = patent_data.get("claims", [])

        analysis_prompt = f"""
다음 청구항들을 분석하세요:

{claims}

분석 항목:
1. 각 청구항의 범위 (넓은 범위/좁은 범위)
2. 독립항과 종속항 관계
3. 핵심 구성요소
4. 권리 범위 추정
"""

        response = ""
        async for chunk in self.query(analysis_prompt):
            response += chunk

        return {
            "claims": claims,
            "analysis": response
        }

    async def compare(
        self,
        claims_data: Dict[str, Any],
        technology_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """청구항과 기술을 비교 분석합니다."""
        compare_prompt = f"""
다음 특허 청구항과 기술을 비교 분석하세요.

청구항 분석:
{claims_data}

자사 기술:
{technology_data}

비교 항목:
1. 각 청구항 요소와 기술 요소의 대응 관계
2. 침해 가능성 (높음/중간/낮음)
3. 회피 가능 요소
4. 권장 조치사항
"""

        response = ""
        async for chunk in self.query(compare_prompt):
            response += chunk

        return {
            "comparison_result": response,
            "risk_level": self._assess_risk(response)
        }

    def _assess_risk(self, analysis: str) -> str:
        """침해 위험도를 평가합니다."""
        high_risk_keywords = ["높음", "high", "침해", "위반"]
        low_risk_keywords = ["낮음", "low", "회피", "상이"]

        analysis_lower = analysis.lower()

        high_count = sum(1 for kw in high_risk_keywords if kw in analysis_lower)
        low_count = sum(1 for kw in low_risk_keywords if kw in analysis_lower)

        if high_count > low_count:
            return "high"
        elif low_count > high_count:
            return "low"
        else:
            return "medium"
