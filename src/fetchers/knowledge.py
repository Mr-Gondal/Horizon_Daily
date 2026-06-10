"""Daily knowledge: quote of the day, a random fact, 'on this day' history,
and a creative prompt to spark your creativity.
"""

from __future__ import annotations

import html
import random
from datetime import datetime, timezone

import requests

from config import MAX_ON_THIS_DAY, REQUEST_TIMEOUT, USER_AGENT

HEADERS = {"User-Agent": USER_AGENT}

CREATIVE_PROMPTS = [
    "Write 100 words about a world where everyone can hear each other's thoughts for one hour a day.",
    "Sketch or describe an everyday object redesigned for a person living on Mars.",
    "Combine two unrelated industries (e.g. farming + gaming) and invent a startup idea.",
    "Photograph (or imagine) something ordinary from an angle nobody usually sees.",
    "Explain a complex topic you know to an imaginary 8-year-old in 5 sentences.",
    "Invent a new word for a feeling that has no name, and define it.",
    "Take today's top news story and write an optimistic version of it set in 2050.",
    "Design a tradition for a holiday that doesn't exist yet.",
    "Write a 6-word story about a stranger you saw today.",
    "List 10 uses for a paperclip that have nothing to do with paper.",
    "Describe your city to someone who has never seen a city before.",
    "If you could add one new rule to the world for 24 hours, what would it be and why?",
    "Turn the last conversation you had into a short comic strip plot.",
    "Imagine your favourite app shut down forever. Design its replacement, but better.",
    "Pick a random object near you and write its autobiography in 5 sentences.",
    "What would a library look like in a world without writing? Describe it.",
    "Merge two of your hobbies into a brand-new sport. Write its rules.",
    "Write a letter from your 80-year-old self to you, today.",
    "Redesign the umbrella. It hasn't fundamentally changed in 3,000 years.",
    "Invent a museum exhibit for an emotion. What's inside?",
]


def fetch_quote() -> str:
    try:
        r = requests.get(
            "https://zenquotes.io/api/today",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        q = r.json()[0]
        return f"💬 <i>“{html.escape(q['q'])}”</i>\n     — {html.escape(q['a'])}"
    except Exception as e:  # noqa: BLE001
        print(f"[knowledge] quote failed: {e}")
        return ""


def fetch_fact() -> str:
    try:
        r = requests.get(
            "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return f"🤯 <b>Did you know?</b> {html.escape(r.json()['text'])}"
    except Exception as e:  # noqa: BLE001
        print(f"[knowledge] fact failed: {e}")
        return ""


def fetch_on_this_day() -> str:
    try:
        now = datetime.now(timezone.utc)
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month:02d}/{now.day:02d}",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        events = r.json().get("events", [])
        if not events:
            return ""
        # Mix of recent and older history
        events.sort(key=lambda e: e.get("year", 0), reverse=True)
        picks = events[:: max(1, len(events) // MAX_ON_THIS_DAY)][:MAX_ON_THIS_DAY]
        lines = ["📜 <b>On this day in history:</b>"]
        for ev in picks:
            year = ev.get("year", "?")
            text = html.escape(ev.get("text", ""))
            lines.append(f"  • <b>{year}</b> — {text}")
        return "\n".join(lines)
    except Exception as e:  # noqa: BLE001
        print(f"[knowledge] on-this-day failed: {e}")
        return ""


def creative_prompt() -> str:
    # Deterministic per day so reruns on the same day give the same prompt
    day_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    rng = random.Random(day_seed)
    prompt = rng.choice(CREATIVE_PROMPTS)
    return f"🎨 <b>Creative spark of the day:</b>\n<i>{html.escape(prompt)}</i>"


def get_section() -> str:
    parts = [p for p in (fetch_quote(), fetch_fact(), fetch_on_this_day(), creative_prompt()) if p]
    if not parts:
        return ""
    header = "📚 <b>DAILY KNOWLEDGE & CREATIVITY</b>\n" + "─" * 22
    return header + "\n\n" + "\n\n".join(parts)
