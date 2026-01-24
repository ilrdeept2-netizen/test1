"""
리포트 생성 에이전트

분석 결과를 보고서로 작성합니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentResult, AgentStatus


@dataclass
class ReportTemplate:
    """보고서 템플릿"""
    name: str
    sections: List[str]
    format: str


class ReportGeneratorAgent(BaseAgent):
    """
    리포트 생성 에이전트

    특허 분석 결과, 선행 기술 조사 결과 등을
    전문적인 보고서 형식으로 작성합니다.
    """

    # 보고서 템플릿
    TEMPLATES = {
        "prior_art": ReportTemplate(
            name="선행 기술 조사 보고서",
            sections=["개요", "조사 방법", "검색 결과", "유사도 분석", "결론", "참고문헌"],
            format="markdown"
        ),
        "infringement": ReportTemplate(
            name="특허 침해 분석 보고서",
            sections=["개요", "대상 특허", "자사 기술", "청구항 대비표", "침해 위험 평가", "권장 사항"],
            format="markdown"
        ),
        "daily_digest": ReportTemplate(
            name="일일 동향 다이제스트",
            sections=["오늘의 주요 뉴스", "새로운 특허", "기술 동향", "주목할 기업"],
            format="markdown"
        ),
        "patent_draft": ReportTemplate(
            name="특허 명세서 초안",
            sections=["발명의 명칭", "기술분야", "배경기술", "발명의 내용", "청구범위", "요약서"],
            format="hlt"
        )
    }

    def __init__(self, **kwargs):
        super().__init__(
            name="report_generator",
            model="claude-sonnet-4-20250514",
            system_prompt="""당신은 기술 문서 작성 전문가입니다.
특허 분석 결과, 선행 기술 조사 결과 등을
전문적인 보고서 형식으로 작성합니다.

보고서 유형:
- 선행 기술 조사 보고서
- 특허 침해 분석 보고서
- 기술 동향 보고서
- 일일 다이제스트
- 특허 명세서 초안

작성 원칙:
1. 명확하고 간결한 문체
2. 객관적인 분석 기반
3. 구조화된 형식
4. 전문 용어 적절히 사용
5. 시각적 요소 활용 (표, 차트 등)""",
            tools=["read", "write", "edit"],
            **kwargs
        )

    async def process(self, input_data: Any) -> AgentResult:
        """
        보고서를 생성합니다.

        Args:
            input_data: 보고서 데이터

        Returns:
            AgentResult: 생성된 보고서
        """
        self.status = AgentStatus.RUNNING

        try:
            if isinstance(input_data, dict):
                report_type = input_data.get("type", "prior_art")
                data = input_data.get("data", {})
            else:
                report_type = "prior_art"
                data = {"content": str(input_data)}

            # 템플릿 선택
            template = self.TEMPLATES.get(report_type, self.TEMPLATES["prior_art"])

            # 보고서 생성
            report = await self._generate_report(template, data)

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data={
                    "report": report,
                    "type": report_type,
                    "format": template.format,
                    "generated_at": datetime.now().isoformat()
                }
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"보고서 생성 오류: {e}")
            return AgentResult(success=False, data=None, error=str(e))

    async def _generate_report(
        self,
        template: ReportTemplate,
        data: Dict[str, Any]
    ) -> str:
        """보고서를 생성합니다."""
        generate_prompt = f"""
다음 데이터를 기반으로 '{template.name}'를 작성하세요.

데이터:
{data}

보고서 구조:
{', '.join(template.sections)}

형식: {template.format}

각 섹션에 적절한 내용을 작성하고, 전문적인 보고서 형식을 유지하세요.
"""

        report = ""
        async for chunk in self.query(generate_prompt):
            report += chunk

        return report

    async def generate_patent_draft(
        self,
        invention_data: Dict[str, Any],
        prior_art_data: Dict[str, Any]
    ) -> AgentResult:
        """특허 명세서 초안을 생성합니다."""
        self.status = AgentStatus.RUNNING

        try:
            draft_prompt = f"""
다음 발명 아이디어와 선행 기술 분석 결과를 바탕으로 특허 명세서 초안을 작성하세요.

발명 아이디어:
{invention_data}

선행 기술 분석:
{prior_art_data}

한국 특허 명세서 형식에 맞춰 다음 섹션을 작성하세요:

1. 발명의 명칭: 간결하고 기술적인 명칭
2. 기술분야: 본 발명이 속하는 기술 분야
3. 발명의 배경이 되는 기술: 선행 기술과 그 문제점
4. 발명의 내용:
   - 해결하려는 과제
   - 과제의 해결 수단
   - 발명의 효과
5. 발명을 실시하기 위한 구체적인 내용: 상세한 실시예
6. 청구범위: 독립항 및 종속항
7. 요약서: 150자 이내 요약

각 섹션을 마크다운 형식으로 작성하세요.
"""

            draft = ""
            async for chunk in self.query(draft_prompt):
                draft += chunk

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data={
                    "draft": draft,
                    "type": "patent_draft",
                    "generated_at": datetime.now().isoformat()
                }
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            return AgentResult(success=False, data=None, error=str(e))

    async def generate_infringement_report(
        self,
        comparison_data: Dict[str, Any],
        patent_data: Dict[str, Any]
    ) -> AgentResult:
        """침해 분석 보고서를 생성합니다."""
        self.status = AgentStatus.RUNNING

        try:
            report_prompt = f"""
다음 데이터를 바탕으로 특허 침해 분석 보고서를 작성하세요.

대상 특허:
{patent_data}

비교 분석 결과:
{comparison_data}

보고서 구조:
1. 요약 (Executive Summary)
2. 대상 특허 개요
3. 자사 기술 개요
4. 청구항 대비 분석표
5. 침해 위험도 평가
6. 회피 설계 가능성
7. 권장 조치사항
8. 결론

전문적이고 객관적인 분석 보고서를 작성하세요.
"""

            report = ""
            async for chunk in self.query(report_prompt):
                report += chunk

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data={
                    "report": report,
                    "risk_level": comparison_data.get("risk_level", "unknown"),
                    "type": "infringement_report",
                    "generated_at": datetime.now().isoformat()
                }
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            return AgentResult(success=False, data=None, error=str(e))

    async def generate_digest(
        self,
        news_data: Dict[str, Any],
        patents_data: Dict[str, Any]
    ) -> AgentResult:
        """일일 다이제스트를 생성합니다."""
        self.status = AgentStatus.RUNNING

        try:
            digest_prompt = f"""
다음 데이터를 바탕으로 일일 AI/특허 동향 다이제스트를 작성하세요.

AI 뉴스:
{news_data}

최근 특허:
{patents_data}

다이제스트 구조:
# 일일 AI/특허 동향 다이제스트
## 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}

### 오늘의 주요 뉴스
(뉴스 요약 3-5개)

### 새로 공개된 특허
(특허 요약 3-5개)

### 기술 동향 분석
(주요 트렌드 분석)

### 주목할 기업/기관
(주요 출원인/기업 동향)

간결하고 읽기 쉬운 형식으로 작성하세요.
"""

            digest = ""
            async for chunk in self.query(digest_prompt):
                digest += chunk

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data={
                    "digest": digest,
                    "date": datetime.now().isoformat(),
                    "type": "daily_digest"
                }
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            return AgentResult(success=False, data=None, error=str(e))
