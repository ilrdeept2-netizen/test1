#!/usr/bin/env python3
"""
AI News Digest Mobile Web App
모바일에서 AI/LLM 뉴스를 확인할 수 있는 웹앱
"""

from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import os
import json
from threading import Lock
import time

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# 캐시 설정
news_cache = {
    'data': [],
    'last_updated': None,
    'lock': Lock()
}
CACHE_DURATION = 30 * 60  # 30분

# RSS 피드 설정
RSS_FEEDS = {
    "OpenAI": {
        "url": "https://openai.com/blog/rss.xml",
        "category": "LLM",
        "icon": "🤖"
    },
    "Anthropic": {
        "url": "https://www.anthropic.com/rss.xml",
        "category": "LLM",
        "icon": "🧠"
    },
    "Google AI": {
        "url": "https://blog.google/technology/ai/rss/",
        "category": "LLM",
        "icon": "🔍"
    },
    "Google DeepMind": {
        "url": "https://deepmind.google/blog/rss.xml",
        "category": "Research",
        "icon": "🔬"
    },
    "Meta AI": {
        "url": "https://ai.meta.com/blog/rss/",
        "category": "LLM",
        "icon": "📘"
    },
    "Microsoft AI": {
        "url": "https://blogs.microsoft.com/ai/feed/",
        "category": "Cloud",
        "icon": "☁️"
    },
    "Hugging Face": {
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "OpenSource",
        "icon": "🤗"
    },
    "Mistral AI": {
        "url": "https://mistral.ai/feed.xml",
        "category": "LLM",
        "icon": "💨"
    },
    "The Verge AI": {
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "category": "News",
        "icon": "📰"
    },
    "TechCrunch AI": {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "News",
        "icon": "💻"
    },
    "VentureBeat AI": {
        "url": "https://venturebeat.com/category/ai/feed/",
        "category": "News",
        "icon": "📊"
    },
    "arXiv AI": {
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "category": "Research",
        "icon": "📄"
    },
}

CATEGORIES = {
    "all": {"name": "전체", "icon": "📋"},
    "LLM": {"name": "LLM", "icon": "🤖"},
    "Cloud": {"name": "클라우드", "icon": "☁️"},
    "OpenSource": {"name": "오픈소스", "icon": "🔓"},
    "Research": {"name": "연구", "icon": "🔬"},
    "News": {"name": "뉴스", "icon": "📰"},
}


def fetch_feed(name: str, info: dict, days_back: int = 3) -> list:
    """단일 RSS 피드 수집"""
    items = []
    cutoff_date = datetime.now() - timedelta(days=days_back)

    try:
        feed = feedparser.parse(info["url"])

        if feed.bozo and not feed.entries:
            return items

        for entry in feed.entries[:15]:
            published = None
            pub_datetime = None

            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_datetime = datetime(*entry.published_parsed[:6])
                published = pub_datetime.strftime("%m/%d %H:%M")
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_datetime = datetime(*entry.updated_parsed[:6])
                published = pub_datetime.strftime("%m/%d %H:%M")

            if pub_datetime and pub_datetime < cutoff_date:
                continue

            summary = ""
            if hasattr(entry, 'summary'):
                soup = BeautifulSoup(entry.summary, 'html.parser')
                summary = soup.get_text()
                summary = re.sub(r'\s+', ' ', summary).strip()
                if len(summary) > 150:
                    summary = summary[:150] + "..."

            items.append({
                "title": entry.title,
                "link": entry.link,
                "source": name,
                "icon": info["icon"],
                "category": info["category"],
                "published": published,
                "timestamp": pub_datetime.timestamp() if pub_datetime else 0,
                "summary": summary
            })
    except Exception as e:
        print(f"Error fetching {name}: {e}")

    return items


def fetch_all_news(days_back: int = 3) -> list:
    """모든 뉴스 수집 (병렬 처리)"""
    all_items = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_feed, name, info, days_back): name
            for name, info in RSS_FEEDS.items()
        }

        for future in as_completed(futures):
            try:
                items = future.result()
                all_items.extend(items)
            except Exception as e:
                print(f"Error: {e}")

    # 시간순 정렬 (최신순)
    all_items.sort(key=lambda x: x['timestamp'], reverse=True)

    # 중복 제거
    seen = set()
    unique_items = []
    for item in all_items:
        key = item['title'][:50].lower()
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    return unique_items


def get_cached_news():
    """캐시된 뉴스 반환 (필요시 갱신)"""
    with news_cache['lock']:
        now = time.time()
        if (news_cache['last_updated'] is None or
            now - news_cache['last_updated'] > CACHE_DURATION):
            print("Refreshing news cache...")
            news_cache['data'] = fetch_all_news()
            news_cache['last_updated'] = now
        return news_cache['data']


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('ai_news_app.html', categories=CATEGORIES)


@app.route('/api/news')
def api_news():
    """뉴스 API"""
    news = get_cached_news()
    return jsonify({
        'success': True,
        'data': news,
        'count': len(news),
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route('/api/news/<category>')
def api_news_category(category):
    """카테고리별 뉴스 API"""
    news = get_cached_news()
    if category != 'all':
        news = [n for n in news if n['category'] == category]
    return jsonify({
        'success': True,
        'data': news,
        'count': len(news),
        'category': category
    })


@app.route('/api/refresh')
def api_refresh():
    """강제 새로고침"""
    with news_cache['lock']:
        news_cache['data'] = fetch_all_news()
        news_cache['last_updated'] = time.time()
    return jsonify({'success': True, 'message': 'Cache refreshed'})


@app.route('/manifest.json')
def manifest():
    """PWA Manifest"""
    return jsonify({
        "name": "AI 뉴스 다이제스트",
        "short_name": "AI뉴스",
        "description": "매일 아침 AI/LLM 최신 뉴스",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#1a1a2e",
        "theme_color": "#4a90d9",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    })


@app.route('/sw.js')
def service_worker():
    """Service Worker"""
    return app.send_static_file('sw.js')


if __name__ == '__main__':
    # static 폴더 생성
    os.makedirs('static', exist_ok=True)

    print("\n" + "="*50)
    print("🌅 AI 뉴스 다이제스트 모바일 앱")
    print("="*50)
    print("\n📱 모바일에서 접속:")
    print("   http://<서버IP>:5050")
    print("\n💡 같은 네트워크의 모바일에서 접속 가능")
    print("   홈 화면에 추가하면 앱처럼 사용 가능!\n")

    app.run(host='0.0.0.0', port=5050, debug=True)
