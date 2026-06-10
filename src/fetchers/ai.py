"""AI corner: latest AI news + AI-focused hackathons (with free credits).

Sources:
  * TechCrunch AI + The Verge AI  - AI news via RSS
  * lablab.ai                     - AI hackathons; sponsors usually give
                                    participants FREE API credits (OpenAI,
                                    Gemini, AMD, IBM, etc.)
  * Devpost (AI theme filter)     - extra AI hackathons w/ sponsor credits
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from config import (
    MAX_AI_HACKATHONS,
    MAX_AI_NEWS,
    REQUEST_TIMEOUT,
    TZ_OFFSET_HOURS,
    USER_AGENT,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}
LOCAL_TZ = timezone(timedelta(hours=TZ_OFFSET_HOURS))

AI_NEWS_FEEDS = [
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
]


# ---------------------------------------------------------------------------
# AI news
# ---------------------------------------------------------------------------
def fetch_ai_news() -> list[str]:
    items: list[str] = []
    per_feed = max(1, MAX_AI_NEWS // len(AI_NEWS_FEEDS))
    for source, url in AI_NEWS_FEEDS:
        try:
            feed = feedparser.parse(url, agent=USER_AGENT)
            for entry in feed.entries[:per_feed]:
                title = html.escape(entry.get("title", "").strip())
                link = entry.get("link", "")
                if title and link:
                    items.append(
                        f"🤖 <a href=\"{link}\">{title}</a> — <i>{source}</i>"
                    )
        except Exception as e:  # noqa: BLE001
            print(f"[ai] news feed {source} failed: {e}")
    return items[:MAX_AI_NEWS]


# ---------------------------------------------------------------------------
# lablab.ai AI hackathons (free credits for participants!)
#
# lablab.ai is a Next.js app-router site; upcoming/ongoing events are streamed
# into the page inside self.__next_f.push() chunks. We decode those chunks and
# pull out event name / slug / start / end dates.
# ---------------------------------------------------------------------------
def fetch_lablab() -> list[str]:
    lines: list[str] = []
    try:
        r = requests.get(
            "https://lablab.ai/ai-hackathons",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        chunks = re.findall(
            r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', r.text, re.S
        )
        blob = "".join(chunks).encode().decode("unicode_escape", errors="ignore")

        now = datetime.now(timezone.utc)
        seen: set[str] = set()
        events: list[tuple[datetime, str, str, datetime]] = []

        for m in re.finditer(r'"endAt":"([^"]+)","startAt":"([^"]+)"', blob):
            try:
                end = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
                start = datetime.fromisoformat(m.group(2).replace("Z", "+00:00"))
            except ValueError:
                continue
            if end < now:  # already finished
                continue

            # The event name appears shortly before the dates, the slug after.
            back = blob[max(0, m.start() - 6000): m.start()]
            fwd = blob[m.start(): m.start() + 1500]
            names = re.findall(r'"name":"([^"]{4,80})"', back)
            slug_m = re.search(r'"slug":"([a-z0-9-]+)"', fwd)
            if not names or not slug_m:
                continue
            name, slug = names[-1], slug_m.group(1)
            if slug in seen:
                continue
            seen.add(slug)
            events.append((start, name, slug, end))

        events.sort(key=lambda e: e[0])

        for start, name, slug, end in events[:MAX_AI_HACKATHONS]:
            status = (
                "🟢 LIVE NOW"
                if start <= now <= end
                else f"🗓 starts {start.astimezone(LOCAL_TZ).strftime('%d %b')}"
            )
            url = f"https://lablab.ai/event/{slug}"
            lines.append(
                f"⚡ <a href=\"{url}\">{html.escape(name)}</a>\n"
                f"     {status} · ends {end.astimezone(LOCAL_TZ).strftime('%d %b %Y')}"
            )
    except Exception as e:  # noqa: BLE001
        print(f"[ai] lablab.ai failed: {e}")
    return lines


# ---------------------------------------------------------------------------
# Devpost — AI-themed hackathons (theme id 6 = Machine Learning/AI).
# Sponsors here frequently hand out free API credits (Google Cloud, OpenAI,
# AWS, etc.) to everyone who registers.
# ---------------------------------------------------------------------------
def fetch_devpost_ai() -> list[str]:
    lines: list[str] = []
    try:
        r = requests.get(
            "https://devpost.com/api/hackathons",
            params={
                "challenge_type[]": "online",
                "status[]": "open",
                "themes[]": "Machine Learning/AI",
            },
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        for h in r.json().get("hackathons", [])[:4]:
            title = html.escape(h.get("title", "AI Hackathon"))
            url = h.get("url", "")
            prize = re.sub(r"<[^>]+>", "", h.get("prize_amount", "") or "")
            time_left = (h.get("time_left_to_submission", "") or "").strip()
            line = f"⚡ <a href=\"{url}\">{title}</a>"
            details = []
            if prize:
                details.append(f"💰 {html.escape(prize)}")
            if time_left:
                details.append(f"⏳ {html.escape(time_left)}")
            if details:
                line += "\n     " + " · ".join(details)
            lines.append(line)
    except Exception as e:  # noqa: BLE001
        print(f"[ai] Devpost AI failed: {e}")
    return lines


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def get_section() -> str:
    news = fetch_ai_news()
    lablab = fetch_lablab()
    devpost_ai = fetch_devpost_ai()

    parts: list[str] = []

    if news:
        parts.append("<b>📡 Latest AI News</b>")
        parts.extend(news)

    if lablab:
        if parts:
            parts.append("")
        parts.append(
            "<b>⚡ AI Hackathons on lablab.ai</b>\n"
            "<i>(sponsors usually give participants free API credits — "
            "OpenAI, Gemini, IBM, AMD &amp; more)</i>"
        )
        parts.extend(lablab)

    if devpost_ai:
        if parts:
            parts.append("")
        parts.append(
            "<b>🧪 AI Hackathons on Devpost</b>\n"
            "<i>(many include free sponsor credits for registrants)</i>"
        )
        parts.extend(devpost_ai)

    if not parts:
        return ""

    header = "🤖 <b>AI CORNER — NEWS, HACKATHONS & FREE CREDITS</b>\n" + "─" * 22
    return header + "\n\n" + "\n\n".join(parts)
