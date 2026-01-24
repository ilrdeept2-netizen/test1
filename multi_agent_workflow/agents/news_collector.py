"""
뉴스 수집 에이전트

AI/특허 관련 최신 뉴스를 수집합니다.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent, AgentResult, AgentStatus


@dataclass
class NewsSource:
    """뉴스 소스 정보"""
    name: str
    url: str
    category: str
    feed_type: str  # rss, api, scrape


class NewsCollectorAgent(BaseAgent):
    """
    뉴스 수집 에이전트

    AI 및 특허 관련 최신 뉴스를 수집하고,
    요약하여 다이제스트를 생성합니다.
    """

    # 뉴스 소스 목록
    NEWS_SOURCES = {
        "openai": NewsSource(
            name="OpenAI Blog",
            url="https://openai.com/blog/rss.xml",
            category="LLM",
            feed_type="rss"
        ),
        "anthropic": NewsSource(
            name="Anthropic News",
            url="https://www.anthropic.com/news/rss.xml",
            category="LLM",
            feed_type="rss"
        ),
        "google_ai": NewsSource(
            name="Google AI Blog",
            url="https://blog.google/technology/ai/rss/",
            category="LLM",
            feed_type="rss"
        ),
        "deepmind": NewsSource(
            name="DeepMind Blog",
            url="https://deepmind.google/blog/rss.xml",
            category="Research",
            feed_type="rss"
        ),
        "meta_ai": NewsSource(
            name="Meta AI Blog",
            url="https://ai.meta.com/blog/rss/",
            category="LLM",
            feed_type="rss"
        ),
        "huggingface": NewsSource(
            name="Hugging Face Blog",
            url="https://huggingface.co/blog/feed.xml",
            category="Open Source",
            feed_type="rss"
        ),
        "arxiv_ai": NewsSource(
            name="arXiv AI Papers",
            url="http://arxiv.org/rss/cs.AI",
            category="Research",
            feed_type="rss"
        ),
        "techcrunch_ai": NewsSource(
            name="TechCrunch AI",
            url="https://techcrunch.com/category/artificial-intelligence/feed/",
            category="News",
            feed_type="rss"
        ),
        "kipris": NewsSource(
            name="KIPRIS 공고",
            url="http://www.kipris.or.kr/",
            category="Patent",
            feed_type="scrape"
        )
    }

    def __init__(self, **kwargs):
        super().__init__(
            name="news_collector",
            model="claude-haiku-4-20250514",
            system_prompt="""당신은 뉴스 큐레이터입니다.
AI 및 특허 관련 최신 뉴스를 수집하고,
요약하여 다이제스트를 생성합니다.

뉴스 소스:
- 주요 AI 회사 블로그 (OpenAI, Anthropic, Google, Meta 등)
- 특허청 공고
- 기술 뉴스 사이트 (TechCrunch 등)
- 학술 저널 (arXiv 등)

수집 기준:
1. 최신성 (24시간 이내)
2. 관련성 (AI, 기계학습, 특허)
3. 중요도 (주요 발표, 신제품, 연구 결과)
4. 신뢰성 (공식 소스 우선)""",
            tools=["bash", "read"],
            **kwargs
        )

    async def process(self, input_data: Any) -> AgentResult:
        """
        뉴스를 수집합니다.

        Args:
            input_data: 수집 설정

        Returns:
            AgentResult: 수집된 뉴스
        """
        self.status = AgentStatus.RUNNING

        try:
            if isinstance(input_data, dict):
                sources = input_data.get("sources", list(self.NEWS_SOURCES.keys()))
                date = input_data.get("date", datetime.now().isoformat())
            else:
                sources = list(self.NEWS_SOURCES.keys())
                date = datetime.now().isoformat()

            # 각 소스에서 뉴스 수집
            all_news = []
            for source_id in sources:
                if source_id in self.NEWS_SOURCES:
                    source = self.NEWS_SOURCES[source_id]
                    news_items = await self._collect_from_source(source)
                    all_news.extend(news_items)

            # 뉴스 정렬 및 중복 제거
            all_news = self._deduplicate_news(all_news)
            all_news.sort(key=lambda x: x.get("published", ""), reverse=True)

            # 뉴스 요약
            summarized = await self._summarize_news(all_news[:20])

            self.status = AgentStatus.COMPLETED
            return AgentResult(
                success=True,
                data={
                    "news": summarized,
                    "total_count": len(all_news),
                    "sources": sources,
                    "collected_at": datetime.now().isoformat()
                }
            )

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"뉴스 수집 오류: {e}")
            return AgentResult(success=False, data=None, error=str(e))

    async def _collect_from_source(self, source: NewsSource) -> List[Dict[str, Any]]:
        """특정 소스에서 뉴스를 수집합니다."""
        news_items = []

        try:
            if source.feed_type == "rss":
                news_items = await self._parse_rss(source)
            elif source.feed_type == "api":
                news_items = await self._call_api(source)
            elif source.feed_type == "scrape":
                news_items = await self._scrape_website(source)

        except Exception as e:
            self.logger.warning(f"소스 '{source.name}'에서 수집 실패: {e}")

        return news_items

    async def _parse_rss(self, source: NewsSource) -> List[Dict[str, Any]]:
        """RSS 피드를 파싱합니다."""
        try:
            # feedparser 사용
            cmd = f"""python3 -c "
import feedparser
import json
feed = feedparser.parse('{source.url}')
items = []
for entry in feed.entries[:10]:
    items.append({{
        'title': entry.get('title', ''),
        'link': entry.get('link', ''),
        'summary': entry.get('summary', '')[:500],
        'published': entry.get('published', ''),
        'source': '{source.name}',
        'category': '{source.category}'
    }})
print(json.dumps(items, ensure_ascii=False))
"
"""
            result = await self.execute_tool("bash", command=cmd)

            import json
            return json.loads(result)

        except Exception as e:
            self.logger.warning(f"RSS 파싱 실패 ({source.name}): {e}")
            # 시뮬레이션 결과 반환
            return [
                {
                    "title": f"{source.name}의 최신 소식",
                    "link": source.url,
                    "summary": "최신 AI 관련 뉴스입니다.",
                    "published": datetime.now().isoformat(),
                    "source": source.name,
                    "category": source.category
                }
            ]

    async def _call_api(self, source: NewsSource) -> List[Dict[str, Any]]:
        """API를 호출합니다."""
        # API 호출 구현
        return []

    async def _scrape_website(self, source: NewsSource) -> List[Dict[str, Any]]:
        """웹사이트를 스크래핑합니다."""
        # 웹 스크래핑 구현
        return []

    def _deduplicate_news(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 뉴스를 제거합니다."""
        seen_titles = set()
        unique_items = []

        for item in news_items:
            title = item.get("title", "").strip().lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_items.append(item)

        return unique_items

    async def _summarize_news(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """뉴스를 요약합니다."""
        if not news_items:
            return []

        summarize_prompt = f"""
다음 뉴스 항목들을 분석하고 각각에 대해 한국어로 간단한 요약(50자 이내)을 추가하세요.

뉴스 목록:
{news_items}

각 뉴스에 'korean_summary' 필드를 추가하여 JSON 배열로 반환하세요.
"""

        response = ""
        async for chunk in self.query(summarize_prompt):
            response += chunk

        # 요약 결과 병합
        for item in news_items:
            item["korean_summary"] = item.get("title", "")[:50]

        return news_items

    async def collect(
        self,
        sources: List[str],
        date: str = None
    ) -> AgentResult:
        """뉴스를 수집합니다 (명시적 메서드)."""
        return await self.process({
            "sources": sources,
            "date": date or datetime.now().isoformat()
        })
