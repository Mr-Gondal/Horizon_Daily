"""Send messages to Telegram, splitting long digests into multiple messages."""

from __future__ import annotations

import time

import requests

from config import REQUEST_TIMEOUT, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
MAX_LEN = 4000  # Telegram hard limit is 4096; leave margin


def _split(text: str) -> list[str]:
    """Split text into chunks <= MAX_LEN, preferring paragraph boundaries."""
    if len(text) <= MAX_LEN:
        return [text]

    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= MAX_LEN:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # A single block longer than MAX_LEN gets hard-split
            while len(block) > MAX_LEN:
                chunks.append(block[:MAX_LEN])
                block = block[MAX_LEN:]
            current = block
    if current:
        chunks.append(current)
    return chunks


def send(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set "
            "(GitHub repo secrets)."
        )

    for i, chunk in enumerate(_split(text)):
        resp = requests.post(
            API_URL,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            # Retry once without parse_mode in case of an HTML parsing issue
            print(f"Telegram error ({resp.status_code}): {resp.text}")
            resp = requests.post(
                API_URL,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": chunk,
                    "disable_web_page_preview": True,
                },
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        if i:
            time.sleep(1)  # be gentle with rate limits
        print(f"Sent chunk {i + 1} ({len(chunk)} chars)")
