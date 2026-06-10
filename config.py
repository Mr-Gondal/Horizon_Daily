"""Central configuration for the daily digest bot."""

import os

# ---------------------------------------------------------------------------
# Personal settings
# ---------------------------------------------------------------------------

# Your country (used to prioritise online / remote competitions that are
# open worldwide, since you participate from home).
COUNTRY = "Pakistan"
COUNTRY_CODE = "PK"

# Timezone offset from UTC in hours (Pakistan = UTC+5)
TZ_OFFSET_HOURS = 5
TZ_LABEL = "PKT"

# ---------------------------------------------------------------------------
# Telegram (come from GitHub Actions secrets)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ---------------------------------------------------------------------------
# Limits per section (keep the digest readable)
# ---------------------------------------------------------------------------
MAX_CODING_CONTESTS = 6
MAX_HACKATHONS = 6
MAX_NEWS_ITEMS = 8
MAX_IDEAS_ITEMS = 8
MAX_ON_THIS_DAY = 4

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = 20
USER_AGENT = (
    "Mozilla/5.0 (compatible; DailyDigestBot/1.0; +https://github.com)"
)
