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
    DEVPOST_PAGES,
    MAX_CODING_CONTESTS,
    MAX_HACKATHONS,
    MAX_UPCOMING_HACKATHONS,
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
#
# We scan several pages and TWO statuses:
#   * "open"     -> submissions in progress right now (you can still join)
#   * "upcoming" -> registration open / starting soon (get in early!)
# ---------------------------------------------------------------------------
def _fetch_devpost_pages(status: str, pages: int) -> list[dict]:
    """Fetch multiple pages of Devpost hackathons for a given status."""
    results: list[dict] = []
    for page in range(1, pages + 1):
        try:
            r = requests.get(
                "https://devpost.com/api/hackathons",
                params={
                    "challenge_type[]": "online",
                    "status[]": status,
                    "page": page,
                },
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            batch = r.json().get("hackathons", [])
            if not batch:
                break
            results.extend(batch)
        except Exception as e:  # noqa: BLE001
            print(f"[competitions] Devpost {status} page {page} failed: {e}")
            break
    return results


def _format_devpost(h: dict) -> str:
    import re

    title = html.escape(h.get("title", "Hackathon"))
    url = h.get("url", "https://devpost.com/hackathons")
    prize = h.get("prize_amount", "")
    # prize_amount comes with embedded HTML like <span>$10,000</span>
    if prize:
        prize = re.sub(r"<[^>]+>", "", prize)
    deadline = (h.get("submission_period_dates", "") or "").strip()
    time_left = (h.get("time_left_to_submission", "") or "").strip()
    org = (h.get("organization_name", "") or "").strip()
    regs = h.get("registrations_count", 0)
    themes = ", ".join(t.get("name", "") for t in (h.get("themes") or [])[:3])

    line = f"🌐 <a href=\"{url}\">{title}</a>"
    if org:
        line += f" <i>by {html.escape(org)}</i>"
    details = []
    if prize:
        details.append(f"💰 {html.escape(prize)}")
    if deadline:
        details.append(f"📅 {html.escape(deadline)}")
    if details:
        line += "\n     " + " · ".join(details)
    extras = []
    if time_left:
        extras.append(f"⏳ {html.escape(time_left)}")
    if regs:
        extras.append(f"👥 {regs:,} registered")
    if extras:
        line += "\n     " + " · ".join(extras)
    if themes:
        line += f"\n     🏷 {html.escape(themes)}"
    return line


def fetch_devpost_open() -> list[str]:
    """Hackathons whose submission window is open right now."""
    hackathons = _fetch_devpost_pages("open", DEVPOST_PAGES)
    return [_format_devpost(h) for h in hackathons[:MAX_HACKATHONS]]


def fetch_devpost_upcoming() -> list[str]:
    """Hackathons that haven't started yet — register now, start fresh."""
    hackathons = _fetch_devpost_pages("upcoming", DEVPOST_PAGES)
    return [_format_devpost(h) for h in hackathons[:MAX_UPCOMING_HACKATHONS]]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def get_section() -> str:
    cf = fetch_codeforces()
    lc = fetch_leetcode()
    dp_open = fetch_devpost_open()
    dp_upcoming = fetch_devpost_upcoming()

    parts: list[str] = []

    if cf or lc:
        parts.append("<b>⚔️ Coding Contests (online, open worldwide)</b>")
        parts.extend(cf + lc)

    if dp_upcoming:
        if parts:
            parts.append("")
        parts.append(
            "<b>📝 Registration Open — Starting Soon (be an early bird!)</b>"
        )
        parts.extend(dp_upcoming)

    if dp_open:
        if parts:
            parts.append("")
        parts.append(
            "<b>🚀 Hackathons In Progress (you can still join & submit)</b>"
        )
        parts.extend(dp_open)

    if not parts:
        return ""

    header = "🏁 <b>COMPETITIONS YOU CAN JOIN</b>\n" + "─" * 22
    return header + "\n\n" + "\n\n".join(parts)
