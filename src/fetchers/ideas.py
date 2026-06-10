"""Unique perspectives & ideas from people around the world.

Sources:
  * Hacker News top stories  - tech/startup/idea discussions
  * Lobsters hottest         - thoughtful tech community
  * Reddit r/Showerthoughts  - unique points of view (via RSS, more reliable
    than the JSON API from datacenter IPs)
"""

from __future__ import annotations

import html

import feedparser
import requests

from config import MAX_IDEAS_ITEMS, REQUEST_TIMEOUT, USER_AGENT

HEADERS = {"User-Agent": USER_AGENT}


def fetch_hackernews(limit: int = 4) -> list[str]:
    lines: list[str] = []
    try:
        r = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        ids = r.json()[: limit * 2]  # fetch extra in case some fail

        for sid in ids:
            if len(lines) >= limit:
                break
            try:
                item = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                ).json()
                if not item or item.get("type") != "story":
                    continue
                title = html.escape(item.get("title", ""))
                url = item.get("url") or f"https://news.ycombinator.com/item?id={sid}"
                score = item.get("score", 0)
                comments = item.get("descendants", 0)
                discuss = f"https://news.ycombinator.com/item?id={sid}"
                lines.append(
                    f"💡 <a href=\"{url}\">{title}</a>\n"
                    f"     ▲ {score} · 💬 <a href=\"{discuss}\">{comments} comments</a> · HN"
                )
            except Exception:  # noqa: BLE001
                continue
    except Exception as e:  # noqa: BLE001
        print(f"[ideas] Hacker News failed: {e}")
    return lines


def fetch_lobsters(limit: int = 2) -> list[str]:
    lines: list[str] = []
    try:
        r = requests.get(
            "https://lobste.rs/hottest.json",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        for story in r.json()[:limit]:
            title = html.escape(story.get("title", ""))
            url = story.get("url") or story.get("comments_url", "")
            score = story.get("score", 0)
            lines.append(f"💡 <a href=\"{url}\">{title}</a>\n     ▲ {score} · Lobsters")
    except Exception as e:  # noqa: BLE001
        print(f"[ideas] Lobsters failed: {e}")
    return lines


def fetch_showerthoughts(limit: int = 3) -> list[str]:
    lines: list[str] = []
    try:
        feed = feedparser.parse(
            "https://www.reddit.com/r/Showerthoughts/top/.rss?t=day",
            agent=USER_AGENT,
        )
        for entry in feed.entries[:limit]:
            title = html.escape(entry.get("title", "").strip())
            if title:
                lines.append(f"🚿 <i>{title}</i>")
    except Exception as e:  # noqa: BLE001
        print(f"[ideas] Showerthoughts failed: {e}")
    return lines


def get_section() -> str:
    items = fetch_hackernews() + fetch_lobsters() + fetch_showerthoughts()
    items = items[:MAX_IDEAS_ITEMS]
    if not items:
        return ""
    header = "🧠 <b>IDEAS & UNIQUE PERSPECTIVES</b>\n" + "─" * 22
    return header + "\n\n" + "\n\n".join(items)
