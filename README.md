# LeetCode Tracker

[![CI](https://github.com/Leon-Lam919/leetcode-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/Leon-Lam919/leetcode-tracker/actions/workflows/ci.yml)
[![Daily reminder](https://github.com/Leon-Lam919/leetcode-tracker/actions/workflows/daily-reminder.yml/badge.svg)](https://github.com/Leon-Lam919/leetcode-tracker/actions/workflows/daily-reminder.yml)

A full-stack app that helps with one habit: **solving one LeetCode problem every day.**

It syncs your accepted submissions from LeetCode, shows whether today is done, and tracks your
streak. It brings solved problems back for review with spaced repetition, and tracks your
progress through the NeetCode 150 patterns. If you haven't solved anything by the evening, it
sends a reminder to your phone.

<!-- Screenshots: add docs/today.png and docs/patterns.png, then uncomment.
![Today tab](docs/today.png)
![Patterns tab](docs/patterns.png)
-->

## Features

**Daily habit**
- **Today banner:** ✅ done or ❌ not yet, with your current 🔥 streak and best streak
- **Sync from LeetCode:** pulls your recent accepted submissions. Safe to click twice: it never duplicates a solve.
- **90-day heatmap:** one square per day, plus totals by difficulty and topic
- **Phone reminders:** a push notification through [ntfy](https://ntfy.sh) if today isn't done. It can come from the app itself or from a free GitHub Actions job that runs even when your computer is off.

**Learning, not just counting**
- **One-click rating:** new solves show up on a "Rate today's solves" card. Click **Again / Good / Easy**, optionally flag it for review and pick a time chip, and it's saved.
- **Review queue:** spaced repetition brings each problem back after 1, 3, 7, 14 and 30 days. Low-confidence solves come back sooner.
- **NeetCode 150 checklist:** progress bars for all 18 patterns, so you can see which ones you haven't practised
- **Solution notes:** your approach, your code, and its time and space complexity for each solve, to revise before interviews

**Built to be used:** works at phone width (375px), supports dark mode, and has filters by difficulty, topic and needs-review. If LeetCode is down, you can add a solve by hand by pasting the problem URL.

## Tech stack

| Layer | Tools | Why |
|---|---|---|
| Backend | Python 3.12, FastAPI, SQLModel on SQLite | Typed models, automatic API docs at `/docs`, and a database that's a single file |
| Background jobs | APScheduler, httpx, ntfy | Auto-sync and the evening reminder run inside the app, with no extra services |
| Frontend | React 19, Vite 7, Tailwind CSS 3.4 | Fast dev server; the heatmap is plain CSS grid with no chart library |
| Tests | pytest + respx, Vitest + React Testing Library | 141 backend and 37 frontend tests. Tests never touch the network: LeetCode and ntfy are faked. |
| CI/CD | GitHub Actions | Lint, test and build run on every push. A scheduled job sends the daily reminder. |
| Infra | Docker Compose, nginx | One command runs everything. nginx serves the frontend and forwards `/api` to the backend. |

## How it works

```
Browser (React)  ──fetch /api──▶  FastAPI
                                    ├── routers/    HTTP only: validate input, call a service, return status codes
                                    ├── services/   the logic, kept small and testable
                                    │     leetcode_client.py   the ONLY file that talks to LeetCode
                                    │     sync.py              LeetCode → database, idempotent
                                    │     streaks.py           pure functions: streak math
                                    │     review_schedule.py   pure functions: spaced repetition
                                    │     scheduler.py         auto-sync + evening reminder
                                    │     notify.py            ntfy push notifications
                                    ├── migrations.py   numbered schema upgrades, run on startup
                                    └── SQLite  backend/data/tracker.db

GitHub Actions (daily, 8:30pm + 10:30pm Chicago)
   └── scripts/daily_check.py  →  LeetCode: solved today?  →  no: push to phone
```

**Design choices worth noting:**
- **Timezones:** times are stored in UTC and converted to your local date once, when a solve is saved. A solve at 11:30pm counts for the day you were in.
- **One file talks to LeetCode:** LeetCode has no official API, so all calls to its GraphQL endpoint live in one module. If LeetCode changes it, that's the only file to fix.
- **Pure functions for tricky logic:** streaks and review scheduling never touch the database, which makes their edge cases easy to test.
- **Safe upgrades:** a `schema_version` table and ordered migrations upgrade an existing database without losing data.

**Data model:**
- `problem`: one row per LeetCode problem
- `solve`: one row per day you solved it
- `review`: each problem's spaced-repetition schedule
- `pattern_problem`: the NeetCode 150
- `meta`: app state, such as the last sync time

## Quick start

```bash
git clone https://github.com/Leon-Lam919/leetcode-tracker.git
cd leetcode-tracker
cp .env.example .env        # then set LEETCODE_USERNAME and TZ
```

**With Docker:**
```bash
docker compose up --build   # open http://localhost:5174
```

**Without Docker** (two terminals):
```bash
# Backend: http://localhost:8000 (API docs at /docs)
cd backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend: http://localhost:5174
cd frontend
npm install
npm run dev
```

**Tests and lint:**
```bash
cd backend && pytest && ruff check .
cd frontend && npm test -- --run && npm run lint
```

## Configuration

All settings live in `.env` (see `.env.example`).

| Variable | Default | Meaning |
|---|---|---|
| `LEETCODE_USERNAME` | (required) | Your public LeetCode username |
| `TZ` | `America/Chicago` | Your IANA timezone, e.g. `America/Chicago`. Decides what "today" means. |
| `DATABASE_URL` | `sqlite:///./data/tracker.db` | Path to the SQLite file, relative to `backend/` |
| `DAILY_GOAL` | `1` | Solves needed for a day to count toward the streak |
| `ENABLE_SCHEDULER` | `false` | `true` turns on auto-sync and the in-app reminder |
| `SYNC_INTERVAL_HOURS` | `3` | Hours between automatic syncs |
| `REMINDER_TIME` | `20:00` | When the in-app reminder checks, in 24-hour time in `TZ` |
| `NTFY_SERVER` / `NTFY_TOPIC` | `https://ntfy.sh` / empty | Where reminders go. An empty topic means no notifications. |
| `CORS_ORIGINS` | `http://localhost:5174` | Other browser apps allowed to call the API, comma-separated |

## Phone reminders

There are two options. **Use one, not both**, or you'll get two notifications.

**Option 1: GitHub Actions** (recommended; works with your computer off):
1. Install the ntfy app on your phone and subscribe to a long, hard-to-guess topic name. ntfy.sh topics are public, so anyone who knows the name can read them.
2. In the repo on GitHub, go to **Settings → Secrets and variables → Actions**.
   - Add the secret `NTFY_TOPIC`.
   - Add the variable `LEETCODE_USERNAME`.
   - Optionally add the variable `TZ`.
3. Go to **Actions → Daily reminder → Run workflow**, tick `force`, and run it. Your phone should buzz.

Notes:
- Scheduled runs use UTC and can start 5–30 minutes late.
- GitHub pauses scheduled workflows after 60 days without a commit. Re-enable it from the Actions tab.
- To test locally without sending anything: `cd backend && LEETCODE_USERNAME=you python scripts/daily_check.py --dry-run`

**Option 2: in-app.** Set `ENABLE_SCHEDULER=true` and `NTFY_TOPIC` in `.env`, restart the backend, then test with `curl -X POST http://localhost:8000/api/notify/test`. This only works while the backend is running.

## Limits of the LeetCode API

- LeetCode only exposes your **last 20** accepted submissions. Sync regularly, and add older solves by hand.
- Your profile must show recent submissions publicly, or sync finds nothing.
- An unknown username shows "user not found" (HTTP 502).

## How this was built

This is my **AI-agent-built** project. My other project, a personal dashboard, I write by hand.

Here the roles were split like this:
- **I** wrote the specs, set the rules for the agents, and reviewed every result.
- **Claude Code agents** wrote the code, in small steps that each had to pass tests before being committed.

The specs are in the repo:
- [`PLAN.md`](PLAN.md): the MVP. Data model, API, streak rules, and a definition of done.
- [`PLAN_V2.md`](PLAN_V2.md): review queue, NeetCode 150, reminders, migrations
- [`PLAN_V3.md`](PLAN_V3.md): one-click rating
- [`PLAN_V4.md`](PLAN_V4.md): the GitHub Actions reminder

[`LEARNING.md`](LEARNING.md) lists the engineering skill each build step uses.

What I practised:
- Writing specs precise enough for someone else to build from
- Setting limits: no pushes, no paid services, never touch my other repo
- Checking work against a definition of done instead of trusting "it's finished"

## Roadmap

- [ ] Deploy to my Raspberry Pi
- [ ] Add screenshots
