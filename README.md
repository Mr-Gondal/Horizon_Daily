# ☀️ Daily Digest Bot

A GitHub Actions–powered bot that sends you a **daily Telegram digest** with:

| Section | What you get | Sources |
|---|---|---|
| 🏁 **Competitions** | Online coding contests & hackathons you can join **from Pakistan 🇵🇰** (all online/worldwide) | Codeforces, LeetCode, Devpost |
| 🌍 **World News & Events** | Top headlines on what's happening around the globe | BBC World, Al Jazeera |
| 🧠 **Ideas & Perspectives** | Trending discussions, unique POVs, and ideas from people worldwide | Hacker News, Lobsters, r/Showerthoughts |
| 📚 **Knowledge & Creativity** | Quote of the day, a surprising fact, "on this day" history, and a daily creative prompt | ZenQuotes, Useless Facts, Wikipedia |

It runs **every day at 8:00 AM Pakistan time** automatically — no server needed, GitHub Actions does everything for free.

---

## 🚀 Setup (one time, ~5 minutes)

### 1. Create the GitHub repository
1. Create a new repo on GitHub (e.g. `daily-digest-bot`).
2. Push this folder's contents to it:
   ```bash
   cd daily-digest-bot
   git init
   git add .
   git commit -m "Initial commit: daily digest bot"
   git branch -M main
   git remote add origin https://github.com/<your-username>/daily-digest-bot.git
   git push -u origin main
   ```

### 2. Get your Telegram credentials
You already have a bot token from **@BotFather**. You also need your **chat ID**:

1. Open Telegram and **send any message to your bot** (e.g. "hi").
2. Open this URL in a browser (replace `<TOKEN>` with your bot token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Find `"chat":{"id": 123456789, ...}` in the response — that number is your **chat ID**.

> If `getUpdates` returns empty, send your bot another message and refresh.

### 3. Add GitHub secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your token from @BotFather (looks like `123456:ABC-DEF...`) |
| `TELEGRAM_CHAT_ID` | Your chat ID from step 2 |

### 4. Test it
Go to **Actions → Daily Digest → Run workflow** to trigger it manually.
Within ~1 minute you should receive your first digest on Telegram. 🎉

After that, it runs automatically **every day at 8:00 AM PKT**.

---

## 🛠 Customisation

Everything lives in [`src/config.py`](src/config.py):

- `COUNTRY` / `TZ_OFFSET_HOURS` — your location & timezone
- `MAX_*` values — how many items per section (keep the digest short or go big)

**Change the delivery time:** edit the cron in
[`.github/workflows/daily-digest.yml`](.github/workflows/daily-digest.yml).
Cron uses **UTC**, so for Pakistan (UTC+5) subtract 5 hours:

| Want digest at (PKT) | Cron line |
|---|---|
| 7:00 AM | `0 2 * * *` |
| 8:00 AM | `0 3 * * *` (current) |
| 9:00 PM | `0 16 * * *` |

**Add more sources:** drop a new file into `src/fetchers/` that exposes a
`get_section() -> str` function returning Telegram-HTML, then register it in
`src/main.py`. Good candidates: Kaggle competitions, Unstop, MLH, arXiv papers,
Product Hunt RSS, dev.to RSS.

---

## 🧪 Run locally

```bash
pip install -r requirements.txt

# Preview without sending to Telegram:
python src/main.py --dry-run

# Actually send:
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
python src/main.py
```

> On Windows (PowerShell): `$env:TELEGRAM_BOT_TOKEN="..."` etc.

---

## 📁 Project structure

```
daily-digest-bot/
├── .github/workflows/daily-digest.yml   # the daily schedule (GitHub Actions)
├── requirements.txt
└── src/
    ├── main.py               # entry point: builds & sends the digest
    ├── config.py             # all settings in one place
    ├── telegram_sender.py    # sends (and auto-splits) long messages
    └── fetchers/
        ├── competitions.py   # Codeforces + LeetCode + Devpost
        ├── news.py           # BBC + Al Jazeera RSS
        ├── ideas.py          # Hacker News + Lobsters + Showerthoughts
        └── knowledge.py      # quote, fact, history, creative prompt
```

## ⚠️ Notes

- GitHub Actions scheduled runs can be delayed by a few minutes (sometimes
  up to an hour during peak load) — that's normal for free-tier cron.
- If a source's API is temporarily down, that section is simply skipped;
  the rest of the digest still arrives.
- Scheduled workflows are automatically disabled by GitHub after **60 days
  of no repo activity** — pushing any commit re-enables them.
