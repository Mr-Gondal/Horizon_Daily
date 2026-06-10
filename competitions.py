"""Fetch upcoming competitions you can join from anywhere in the world.

Sources:
  * Codeforces  - competitive programming contests (online, worldwide)
  * Devpost     - online hackathons (filterable, open worldwide)
  * LeetCode    - upcoming coding contests (online, worldwide)
"""

from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone

import requests

from config import (
    MAX_CODING_CONTESTS,
    MAX_HACKATHONS,
    REQUEST_TIMEOUT,
    TZ_LABEL,
    TZ_OFFSET_HOURS,
    USER_AGENT,
)

HEADERS = {"User-Agent": USER_AGENT}
LOCAL_TZ = timezone(timedelta(hours=TZ_OFFSET_HOURS))


def _fmt_ts(ts: int) -> str:
    """Unix timestamp -> human readable local time."""
    dt = datetime.fromtimestamp(ts, tz=LOCAL_TZ)
    return dt.strftime(f"%a, %d %b %Y %I:%M %p {TZ_LABEL}")


# ---------------------------------------------------------------------------
# Codeforces
# ---------------------------------------------------------------------------
def fetch_codeforces() -> list[str]:
    lines: list[str] = []
    try:
        r = requests.get(
            "https://codeforces.com/api/contest.list?gym=false",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "OK":
            return lines

        upcoming = [c for c in data["result"] if c.get("phase") == "BEFORE"]
        # Soonest first
        upcoming.sort(key=lambda c: c.get("startTimeSeconds", 0))

        for c in upcoming[:MAX_CODING_CONTESTS]:
            name = html.escape(c.get("name", "Unknown contest"))
            start = c.get("startTimeSeconds")
            dur_h = c.get("durationSeconds", 0) / 3600
            when = _fmt_ts(start) if start else "TBA"
            url = f"https://codeforces.com/contests/{c.get('id')}"
            lines.append(
                f"🏆 <a href=\"{url}\">{name}</a>\n"
                f"     🕐 {when} · ⏱ {dur_h:.1f}h"
            )
    except Exception as e:  # noqa: BLE001
        print(f"[competitions] Codeforces failed: {e}")
    return lines


# ---------------------------------------------------------------------------
# LeetCode
# ---------------------------------------------------------------------------
def fetch_leetcode() -> list[str]:
    lines: list[str] = []
    try:
        query = {
            "query": (
                "{ upcomingContests { title titleSlug startTime duration } }"
            )
        }
        r = requests.post(
            "https://leetcode.com/graphql",
            json=query,
            headers={**HEADERS, "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        contests = r.json().get("data", {}).get("upcomingContests", []) or []
        contests.sort(key=lambda c: c.get("startTime", 0))
        for c in contests[:3]:
            name = html.escape(c.get("title", "LeetCode Contest"))
            when = _fmt_ts(c["startTime"]) if c.get("startTime") else "TBA"
            url = f"https://leetcode.com/contest/{c.get('titleSlug', '')}"
            lines.append(f"🏆 <a href=\"{url}\">{name}</a>\n     🕐 {when}")
    except Exception as e:  # noqa: BLE001
        print(f"[competitions] LeetCode failed: {e}")
    return lines


# ---------------------------------------------------------------------------
# Devpost (online hackathons — tech, AI, creative, design, social good...)
# ---------------------------------------------------------------------------
def fetch_devpost() -> list[str]:
    lines: list[str] = []
    try:
        r = requests.get(
            "https://devpost.com/api/hackathons",
            params={"challenge_type[]": "online", "status[]": "open"},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        hackathons = r.json().get("hackathons", [])

        for h in hackathons[:MAX_HACKATHONS]:
            title = html.escape(h.get("title", "Hackathon"))
            url = h.get("url", "https://devpost.com/hackathons")
            prize = h.get("prize_amount", "")
            # prize_amount comes with embedded HTML like <span>$10,000</span>
            if prize:
                import re

                prize = re.sub(r"<[^>]+>", "", prize)
            deadline = (
                h.get("submission_period_dates", "") or ""
            ).strip()
            themes = ", ".join(
                t.get("name", "") for t in (h.get("themes") or [])[:3]
            )

            line = f"🌐 <a href=\"{url}\">{title}</a>"
            details = []
            if prize:
                details.append(f"💰 {html.escape(prize)}")
            if deadline:
                details.append(f"📅 {html.escape(deadline)}")
            if details:
                line += "\n     " + " · ".join(details)
            if themes:
                line += f"\n     🏷 {html.escape(themes)}"
            lines.append(line)
    except Exception as e:  # noqa: BLE001
        print(f"[competitions] Devpost failed: {e}")
    return lines


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def get_section() -> str:
    cf = fetch_codeforces()
    lc = fetch_leetcode()
    dp = fetch_devpost()

    parts: list[str] = []

    if cf or lc:
        parts.append("<b>⚔️ Coding Contests (online, open worldwide)</b>")
        parts.extend(cf + lc)

    if dp:
        if parts:
            parts.append("")
        parts.append("<b>🚀 Online Hackathons (join from Pakistan 🇵🇰)</b>")
        parts.extend(dp)

    if not parts:
        return ""

    header = "🏁 <b>COMPETITIONS YOU CAN JOIN</b>\n" + "─" * 22
    return header + "\n\n" + "\n\n".join(parts)
