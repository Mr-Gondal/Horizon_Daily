"""Daily Digest Bot — entry point.

Collects competitions, world news, ideas/perspectives, and daily knowledge,
then sends everything to your Telegram chat.

Run locally:
    export TELEGRAM_BOT_TOKEN=...
    export TELEGRAM_CHAT_ID=...
    python src/main.py

Or do a dry run without sending:
    python src/main.py --dry-run
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from config import TZ_LABEL, TZ_OFFSET_HOURS
from fetchers import ai, competitions, ideas, knowledge, news


def build_digest() -> str:
    local_now = datetime.now(timezone(timedelta(hours=TZ_OFFSET_HOURS)))
    date_line = local_now.strftime(f"%A, %d %B %Y · %I:%M %p {TZ_LABEL}")

    header = (
        "☀️ <b>YOUR DAILY DIGEST</b>\n"
        f"📅 {date_line}\n"
        "════════════════════════"
    )

    sections = []
    for name, builder in (
        ("competitions", competitions.get_section),
        ("ai", ai.get_section),
        ("news", news.get_section),
        ("ideas", ideas.get_section),
        ("knowledge", knowledge.get_section),
    ):
        try:
            section = builder()
            if section:
                sections.append(section)
                print(f"[main] section '{name}' ok ({len(section)} chars)")
            else:
                print(f"[main] section '{name}' returned nothing")
        except Exception as e:  # noqa: BLE001
            print(f"[main] section '{name}' crashed: {e}")

    footer = "════════════════════════\n✨ <i>Go learn something, build something, meet someone. See you tomorrow!</i>"

    return "\n\n".join([header, *sections, footer])


def main() -> None:
    digest = build_digest()

    if "--dry-run" in sys.argv:
        # Strip HTML-ish output for terminal preview
        print("\n" + "=" * 60 + "\nDRY RUN — digest preview below\n" + "=" * 60)
        print(digest)
        return

    from telegram_sender import send

    send(digest)
    print("Digest delivered ✔")


if __name__ == "__main__":
    main()
