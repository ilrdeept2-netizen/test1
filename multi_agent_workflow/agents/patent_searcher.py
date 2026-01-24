"""
특허 검색 에이전트

선행 기술 조사 및 유사 특허를 검색합니다.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base_agent import BaseAgent, AgentResult, AgentStatus


@dataclass
class PatentSearchResult:
    """특허 검색 결과"""
    patent_number: str
    title: str
    applicant: str
    filing_date: str
    abstract: str
    similarity_score: float
    ipc_codes: List[str]


class PatentSearcherAgent(BaseAgent):
    """
    특허 검색 에이전트

    KIPRIS API를 활용하여 선행 기술을 조사하고,
    유사 특허를 검색하여 분석합니다.
    """

    # KIPRIS API 기본 URL (실제 사용 시 API 키 필요)
    KIPRIS_API_BASE = "http://plus.kipris.or.kr/openapi/rest"

    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(
            name="patent_searcher",
            model="claude-sonnet-4-20250514",
            system_prompt="""당신은 특허 검색 전문가입니다.
KIPRIS API를 활용하여 선행 기술을 조사하고,
유사 특허를 검색하여 분석합니다.

검색 전략:
- 키워드 기반 검색
- IPC 분류 기반 검색
- 인용 관계 분석
- 유사도 점수 계산

검색 시 고려사항:
1. 핵심 기술 용어 추출
2. 동의어/유사어 확장
3. IPC 코드 매핑
4. 시간적 범위 설정""",
            tools=["read", "bash", "glob"],
            **kwargs
        )
        self.api_key = api_key

    async def process(self, input_data: Any) -> AgentResult:
        """
        특허 검색을 수행합니다.

        Args:
            input_data: 검색 쿼리 또는 문서 내용

        Returns:
            AgentResult: 검색 결과
        """
        self.status = AgentStatus.RUNNING

        try:
            if isinstance(input_data, dict):
                content = input_data.get("content", "")
                field = input_data.get("field", "")
            else:
                content = str(input_data)
                field = ""

            # 키워드 추출
            keywords = await self._extract_keywords(content)

            # 특허 검색 수행
            search_results = await self._search_patents(keywords, field)

            # 유사도 순으로 정렬
            search_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data={
                    "keywords": keywords,
                    "results": search_results,
                    "total_count": len(search_results)
                },
                metadata={"type": "patent_search"}
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"특허 검색 오류: {e}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def _extract_keywords(self, content: str) -> List[str]:
        """검색 키워드를 추출합니다."""
        keyword_prompt = f"""
다음 텍스트에서 특허 검색에 사용할 핵심 키워드를 추출하세요.

텍스트:
{content[:5000]}

추출 기준:
1. 기술적 용어
2. 발명의 핵심 개념
3. 구성 요소 명칭
4. 동작/방법 관련 용어

10개 이내의 키워드를 쉼표로 구분하여 나열하세요.
"""

        response = ""
        async for chunk in self.query(keyword_prompt):
            response += chunk

        # 키워드 파싱
        keywords = [kw.strip() for kw in response.split(",")]
        keywords = [kw for kw in keywords if kw and len(kw) > 1]

        return keywords[:10]

    async def _search_patents(
        self,
        keywords: List[str],
        field: str = ""
    ) -> List[Dict[str, Any]]:
        """특허 검색을 수행합니다."""
        results = []

        # 키워드 조합으로 검색
        search_query = " OR ".join(keywords)

        self.logger.info(f"특허 검색 쿼리: {search_query}")

        # 실제 KIPRIS API 호출 (API 키가 있는 경우)
        if self.api_key:
            api_results = await self._call_kipris_api(search_query, field)
            results.extend(api_results)
        else:
            # 시뮬레이션 결과 (API 키가 없는 경우)
            results = await self._simulate_search(keywords, field)

        return results

    async def _call_kipris_api(
        self,
        query: str,
        field: str
    ) -> List[Dict[str, Any]]:
        """KIPRIS API를 호출합니다."""
        # 실제 API 호출 구현
        # curl 명령 사용
        curl_cmd = f"""
curl -s "{self.KIPRIS_API_BASE}/patUtiModInfoSearchSevice/freeSearchInfo?searchWord={query}&apiKey={self.api_key}"
"""
        result = await self.execute_tool("bash", command=curl_cmd)

        # XML/JSON 파싱 후 결과 반환
        # (실제 구현 시 적절한 파싱 로직 추가)
        return []

    async def _simulate_search(
        self,
        keywords: List[str],
        field: str
    ) -> List[Dict[str, Any]]:
        """검색 결과를 시뮬레이션합니다 (테스트용)."""
        # AI를 사용하여 가상의 관련 특허 생성
        simulation_prompt = f"""
다음 키워드와 관련된 가상의 선행 특허 5건을 생성하세요.

키워드: {', '.join(keywords)}
기술 분야: {field or '일반'}

각 특허에 대해 다음 정보를 JSON 형식으로 제공하세요:
- patent_number: 특허번호 (10-XXXX-XXXXXXX 형식)
- title: 발명의 명칭
- applicant: 출원인
- filing_date: 출원일 (YYYY-MM-DD)
- abstract: 요약 (100자 이내)
- similarity_score: 유사도 점수 (0.0 ~ 1.0)
- ipc_codes: IPC 분류 코드 리스트

JSON 배열로 응답하세요.
"""

        response = ""
        async for chunk in self.query(simulation_prompt):
            response += chunk

        # JSON 파싱 시도
        try:
            import json
            # JSON 블록 추출
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        # 파싱 실패 시 기본 결과 반환
        return [
            {
                "patent_number": "10-2024-0000001",
                "title": f"{keywords[0] if keywords else '기술'} 관련 특허",
                "applicant": "예시 기업",
                "filing_date": "2024-01-01",
                "abstract": "관련 기술에 대한 특허입니다.",
                "similarity_score": 0.75,
                "ipc_codes": ["G06F 17/00"]
            }
        ]

    async def search_recent(
        self,
        date_range: str = "last_24h",
        fields: List[str] = None
    ) -> AgentResult:
        """최근 특허를 검색합니다."""
        self.status = AgentStatus.RUNNING

        try:
            # 날짜 범위 계산
            if date_range == "last_24h":
                start_date = datetime.now() - timedelta(days=1)
            elif date_range == "last_week":
                start_date = datetime.now() - timedelta(weeks=1)
            elif date_range == "last_month":
                start_date = datetime.now() - timedelta(days=30)
            else:
                start_date = datetime.now() - timedelta(days=1)

            fields = fields or ["인공지능"]

            # 각 분야별 검색
            all_results = []
            for field in fields:
                results = await self._search_patents([field], field)
                all_results.extend(results)

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data={
                    "date_range": date_range,
                    "start_date": start_date.isoformat(),
                    "fields": fields,
                    "results": all_results
                }
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            return AgentResult(success=False, data=None, error=str(e))

    async def fetch_by_number(self, patent_number: str) -> AgentResult:
        """특허 번호로 상세 정보를 조회합니다."""
        self.status = AgentStatus.RUNNING

        try:
            # 특허 번호 정규화
            normalized = re.sub(r'[^0-9]', '', patent_number)

            self.logger.info(f"특허 조회: {patent_number}")

            # API 호출 또는 시뮬레이션
            if self.api_key:
                # 실제 API 호출
                pass
            else:
                # 시뮬레이션
                patent_info = {
                    "patent_number": patent_number,
                    "title": "조회된 특허",
                    "applicant": "특허권자",
                    "filing_date": "2024-01-01",
                    "registration_date": "2024-06-01",
                    "abstract": "특허 요약 내용",
                    "claims": ["청구항 1", "청구항 2"],
                    "ipc_codes": ["G06F 17/00"],
                    "status": "등록"
                }

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data=patent_info,
                metadata={"type": "patent_detail"}
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            return AgentResult(success=False, data=None, error=str(e))
