"""World news & events via RSS feeds (BBC World + Al Jazeera)."""

from __future__ import annotations

import html

import feedparser

from config import MAX_NEWS_ITEMS

FEEDS = [
    ("BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
]


def get_section() -> str:
    items: list[str] = []
    per_feed = max(1, MAX_NEWS_ITEMS // len(FEEDS))

    for source, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:per_feed]:
                title = html.escape(entry.get("title", "").strip())
                link = entry.get("link", "")
                if title and link:
                    items.append(f"📰 <a href=\"{link}\">{title}</a> — <i>{source}</i>")
        except Exception as e:  # noqa: BLE001
            print(f"[news] {source} failed: {e}")

    if not items:
        return ""

    header = "🌍 <b>WORLD NEWS & EVENTS</b>\n" + "─" * 22
    return header + "\n\n" + "\n\n".join(items[:MAX_NEWS_ITEMS])
