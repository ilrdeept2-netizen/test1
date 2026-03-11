#!/usr/bin/env python3
"""
AI News Digest - AI/LLM 서비스 뉴스 수집기
매일 아침 8시에 주요 AI 서비스들의 업데이트, 새 기능, 뉴스를 수집하여 제공합니다.
"""

import feedparser
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import re


@dataclass
class NewsItem:
    """뉴스 항목 데이터 클래스"""
    title: str
    link: str
    source: str
    published: Optional[str]
    summary: Optional[str]
    category: str  # LLM, Cloud AI, Open Source, Research, etc.


class AINewsDigest:
    """AI/LLM 뉴스 수집 및 다이제스트 생성 클래스"""

    # 주요 AI 회사 및 서비스 RSS 피드
    RSS_FEEDS = {
        # LLM 제공업체
        "OpenAI": {
            "url": "https://openai.com/blog/rss.xml",
            "category": "LLM",
            "backup_url": "https://openai.com/news"
        },
        "Anthropic": {
            "url": "https://www.anthropic.com/rss.xml",
            "category": "LLM",
            "backup_url": "https://www.anthropic.com/news"
        },
        "Google AI": {
            "url": "https://blog.google/technology/ai/rss/",
            "category": "LLM",
            "backup_url": "https://blog.google/technology/ai/"
        },
        "Google DeepMind": {
            "url": "https://deepmind.google/blog/rss.xml",
            "category": "Research",
            "backup_url": "https://deepmind.google/discover/blog/"
        },
        "Meta AI": {
            "url": "https://ai.meta.com/blog/rss/",
            "category": "LLM",
            "backup_url": "https://ai.meta.com/blog/"
        },
        "Microsoft AI": {
            "url": "https://blogs.microsoft.com/ai/feed/",
            "category": "Cloud AI",
            "backup_url": "https://blogs.microsoft.com/ai/"
        },

        # 오픈소스 및 연구
        "Hugging Face": {
            "url": "https://huggingface.co/blog/feed.xml",
            "category": "Open Source",
            "backup_url": "https://huggingface.co/blog"
        },
        "Stability AI": {
            "url": "https://stability.ai/blog/rss.xml",
            "category": "Open Source",
            "backup_url": "https://stability.ai/blog"
        },
        "Mistral AI": {
            "url": "https://mistral.ai/feed.xml",
            "category": "LLM",
            "backup_url": "https://mistral.ai/news/"
        },

        # AI 뉴스 미디어
        "The Verge AI": {
            "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
            "category": "News",
            "backup_url": "https://www.theverge.com/ai-artificial-intelligence"
        },
        "TechCrunch AI": {
            "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "category": "News",
            "backup_url": "https://techcrunch.com/category/artificial-intelligence/"
        },
        "Ars Technica AI": {
            "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
            "category": "News",
            "backup_url": "https://arstechnica.com/ai/"
        },
        "VentureBeat AI": {
            "url": "https://venturebeat.com/category/ai/feed/",
            "category": "News",
            "backup_url": "https://venturebeat.com/category/ai/"
        },

        # 연구 및 학술
        "arXiv AI": {
            "url": "https://rss.arxiv.org/rss/cs.AI",
            "category": "Research",
            "backup_url": "https://arxiv.org/list/cs.AI/recent"
        },
        "Papers With Code": {
            "url": "https://paperswithcode.com/latest",
            "category": "Research",
            "backup_url": "https://paperswithcode.com/"
        },
    }

    # 추가 웹 스크래핑 소스
    WEB_SOURCES = {
        "OpenAI Changelog": "https://platform.openai.com/docs/changelog",
        "Anthropic Docs": "https://docs.anthropic.com/",
        "Cohere": "https://cohere.com/blog",
        "Perplexity": "https://blog.perplexity.ai/",
    }

    def __init__(self, days_back: int = 1):
        """
        초기화

        Args:
            days_back: 며칠 전까지의 뉴스를 수집할지 (기본값: 1일)
        """
        self.days_back = days_back
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.news_items: List[NewsItem] = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def fetch_rss_feed(self, name: str, feed_info: dict) -> List[NewsItem]:
        """RSS 피드에서 뉴스 수집"""
        items = []
        try:
            feed = feedparser.parse(feed_info["url"])

            if feed.bozo and not feed.entries:
                print(f"  ⚠ {name}: RSS 피드 파싱 실패, 건너뜁니다")
                return items

            for entry in feed.entries[:10]:  # 최근 10개만
                # 발행일 확인
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date < self.cutoff_date:
                        continue
                    published = pub_date.strftime("%Y-%m-%d %H:%M")
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                    if pub_date < self.cutoff_date:
                        continue
                    published = pub_date.strftime("%Y-%m-%d %H:%M")

                # 요약 추출
                summary = None
                if hasattr(entry, 'summary'):
                    # HTML 태그 제거
                    soup = BeautifulSoup(entry.summary, 'html.parser')
                    summary = soup.get_text()[:300] + "..." if len(soup.get_text()) > 300 else soup.get_text()

                item = NewsItem(
                    title=entry.title,
                    link=entry.link,
                    source=name,
                    published=published,
                    summary=summary,
                    category=feed_info["category"]
                )
                items.append(item)

        except Exception as e:
            print(f"  ⚠ {name}: 오류 발생 - {str(e)[:50]}")

        return items

    def fetch_all_feeds(self) -> None:
        """모든 RSS 피드에서 병렬로 뉴스 수집"""
        print("\n📡 RSS 피드에서 뉴스 수집 중...\n")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self.fetch_rss_feed, name, info): name
                for name, info in self.RSS_FEEDS.items()
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    items = future.result()
                    self.news_items.extend(items)
                    if items:
                        print(f"  ✓ {name}: {len(items)}개 뉴스 수집")
                except Exception as e:
                    print(f"  ✗ {name}: 수집 실패 - {e}")

    def categorize_news(self) -> Dict[str, List[NewsItem]]:
        """뉴스를 카테고리별로 분류"""
        categorized = {
            "🤖 LLM 업데이트": [],
            "☁️ 클라우드 AI": [],
            "🔓 오픈소스": [],
            "🔬 연구/논문": [],
            "📰 AI 뉴스": [],
        }

        category_map = {
            "LLM": "🤖 LLM 업데이트",
            "Cloud AI": "☁️ 클라우드 AI",
            "Open Source": "🔓 오픈소스",
            "Research": "🔬 연구/논문",
            "News": "📰 AI 뉴스",
        }

        for item in self.news_items:
            cat_key = category_map.get(item.category, "📰 AI 뉴스")
            categorized[cat_key].append(item)

        return categorized

    def generate_digest(self) -> str:
        """뉴스 다이제스트 생성"""
        today = datetime.now().strftime("%Y년 %m월 %d일")

        digest = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    🌅 AI 뉴스 다이제스트                          ║
║                       {today}                              ║
╚══════════════════════════════════════════════════════════════════╝

"""

        categorized = self.categorize_news()

        for category, items in categorized.items():
            if not items:
                continue

            digest += f"\n{'='*60}\n"
            digest += f"  {category}\n"
            digest += f"{'='*60}\n\n"

            # 중복 제거 (같은 제목)
            seen_titles = set()
            unique_items = []
            for item in items:
                title_key = item.title.lower()[:50]
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_items.append(item)

            for item in unique_items[:10]:  # 카테고리당 최대 10개
                digest += f"  📌 {item.title}\n"
                digest += f"     출처: {item.source}"
                if item.published:
                    digest += f" | {item.published}"
                digest += "\n"
                if item.summary:
                    # 요약 정리
                    summary = item.summary.replace('\n', ' ').strip()
                    summary = re.sub(r'\s+', ' ', summary)
                    if len(summary) > 150:
                        summary = summary[:150] + "..."
                    digest += f"     {summary}\n"
                digest += f"     🔗 {item.link}\n\n"

        # 통계
        digest += f"\n{'='*60}\n"
        digest += f"  📊 통계\n"
        digest += f"{'='*60}\n"
        digest += f"  • 총 수집된 뉴스: {len(self.news_items)}개\n"
        for category, items in categorized.items():
            if items:
                digest += f"  • {category}: {len(items)}개\n"
        digest += f"  • 수집 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return digest

    def generate_markdown(self) -> str:
        """마크다운 형식의 다이제스트 생성"""
        today = datetime.now().strftime("%Y년 %m월 %d일")

        md = f"""# 🌅 AI 뉴스 다이제스트

**{today}** 기준 최신 AI/LLM 뉴스

---

"""

        categorized = self.categorize_news()

        for category, items in categorized.items():
            if not items:
                continue

            md += f"## {category}\n\n"

            # 중복 제거
            seen_titles = set()
            unique_items = []
            for item in items:
                title_key = item.title.lower()[:50]
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_items.append(item)

            for item in unique_items[:10]:
                md += f"### [{item.title}]({item.link})\n"
                md += f"**출처:** {item.source}"
                if item.published:
                    md += f" | **발행:** {item.published}"
                md += "\n\n"
                if item.summary:
                    summary = item.summary.replace('\n', ' ').strip()
                    summary = re.sub(r'\s+', ' ', summary)
                    if len(summary) > 200:
                        summary = summary[:200] + "..."
                    md += f"> {summary}\n\n"
                md += "---\n\n"

        # 통계
        md += f"## 📊 수집 통계\n\n"
        md += f"| 항목 | 수량 |\n"
        md += f"|------|------|\n"
        md += f"| 총 뉴스 | {len(self.news_items)}개 |\n"
        for category, items in categorized.items():
            if items:
                md += f"| {category} | {len(items)}개 |\n"
        md += f"\n수집 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return md

    def save_digest(self, output_dir: str = ".") -> tuple:
        """다이제스트를 파일로 저장"""
        today = datetime.now().strftime("%Y%m%d")

        # 텍스트 버전
        txt_path = os.path.join(output_dir, f"ai_news_{today}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_digest())

        # 마크다운 버전
        md_path = os.path.join(output_dir, f"ai_news_{today}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_markdown())

        return txt_path, md_path

    def run(self, save_file: bool = False, output_dir: str = ".") -> str:
        """뉴스 다이제스트 실행"""
        print("\n" + "="*60)
        print("🌅 AI 뉴스 다이제스트 시작")
        print("="*60)
        print(f"수집 기간: 최근 {self.days_back}일")

        self.fetch_all_feeds()

        digest = self.generate_digest()

        if save_file:
            txt_path, md_path = self.save_digest(output_dir)
            print(f"\n📁 파일 저장됨:")
            print(f"   - {txt_path}")
            print(f"   - {md_path}")

        return digest


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='AI/LLM 뉴스 다이제스트 - 매일 아침 AI 관련 최신 뉴스를 수집합니다.'
    )
    parser.add_argument(
        '-d', '--days',
        type=int,
        default=1,
        help='수집할 기간 (일 단위, 기본값: 1)'
    )
    parser.add_argument(
        '-s', '--save',
        action='store_true',
        help='결과를 파일로 저장'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='.',
        help='출력 디렉토리 (기본값: 현재 디렉토리)'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='조용한 모드 (파일 저장만)'
    )

    args = parser.parse_args()

    digest = AINewsDigest(days_back=args.days)
    result = digest.run(save_file=args.save, output_dir=args.output)

    if not args.quiet:
        print(result)


if __name__ == "__main__":
    main()
