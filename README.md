# LeetCode Tracker

![CI](https://github.com/OWNER/leetcode-tracker/actions/workflows/ci.yml/badge.svg)
<!-- Replace OWNER with your GitHub username after pushing. -->

A small full-stack app for a simple habit: **solve one LeetCode problem a day.**
It shows whether today is done, keeps your streak, draws a 90-day heatmap, and
stores notes on each solve so you can review problems later. v2 adds interview prep:
a spaced-repetition review queue, the NeetCode 150 pattern checklist, written solutions,
and an automatic sync with an evening reminder on your phone. v3 makes rating a solve
take one click, right when it arrives.

![Screenshot](docs/screenshot.png)
<!-- Screenshot placeholders: add docs/screenshot.png (Today tab),
     docs/review-queue.png and docs/patterns.png (Patterns tab). -->

## Features
- **Today banner:** ✅ done / ❌ not yet, current streak 🔥 and best streak
- **Sync now:** pulls your last 20 accepted submissions from LeetCode (safe to click twice)
- **Manual add:** paste a problem URL or slug, for older solves or when LeetCode is down
- **Notes:** time spent, confidence (1–3), free-text notes, "needs review" flag
- **Heatmap and stats:** 90-day grid, totals by difficulty, top topics
- **Filters:** by difficulty, topic, or needs-review
- **Solutions (v2):** approach, code (Tab indents), language, time and space complexity; 📝 marks solves that have one
- **Review queue (v2):** spaced repetition per problem (1, 3, 7, 14, 30 days). Rate each review **Again / Good / Easy**; re-solving a problem on a later day counts as a review
- **Patterns tab (v2):** NeetCode 150 grouped into its 18 patterns, with progress bars and ✅ for solved problems
- **Auto-sync + reminder (v2):** syncs every few hours and, at a set time, sends a phone notification through [ntfy](https://ntfy.sh) if today isn't done yet
- **Quick rating (v3):** a "✍️ Rate today's solves" card lists recent solves with no confidence.
  One click on **Again / Good / Easy** saves the rating, the 🔁 review flag and an optional time
  chip (15 / 30 / 45 / 60+ min). "Skip" hides a row until you reload. You can also rate while adding
  a solve by hand, or with the "Rate" chip in the solves table
- **Rating sets the first review (v3):** rating a problem's first solve (before it has been reviewed)
  sets its first review: Again or Good → tomorrow, Easy → in 3 days. Otherwise changing a rating
  doesn't move the schedule
- Works on a phone (375px) and in dark mode

## Stack
| Layer | Tools |
|---|---|
| Backend | Python 3.12, FastAPI, SQLModel on SQLite, httpx, loguru, APScheduler |
| Frontend | React 19, Vite 7, Tailwind 3.4 |
| Tests | pytest + respx (backend), Vitest + React Testing Library (frontend) |
| Infra | Docker Compose, GitHub Actions |

## Setup
Copy the example env file and fill in your LeetCode username:
```bash
cp .env.example .env
```
| Variable | Meaning |
|---|---|
| `LEETCODE_USERNAME` | Your public LeetCode username |
| `TZ` | Your IANA timezone, e.g. `America/Toronto`. Decides what "today" means. The app refuses to start if it's invalid. |
| `DATABASE_URL` | SQLite file, relative to `backend/` (default `sqlite:///./data/tracker.db`) |
| `DAILY_GOAL` | Solves needed for a day to count toward the streak (default `1`) |
| `ENABLE_SCHEDULER` | `true` turns on auto-sync and the evening reminder (default `false`) |
| `SYNC_INTERVAL_HOURS` | Hours between automatic syncs (default `3`) |
| `REMINDER_TIME` | When to check and remind, 24-hour `HH:MM` in `TZ` (default `20:00`). The app refuses to start if it's invalid. |
| `NTFY_SERVER` | ntfy server (default `https://ntfy.sh`) |
| `NTFY_TOPIC` | Your ntfy topic. Empty = no notifications (default) |
| `CORS_ORIGINS` | Other browser apps allowed to call the API, comma-separated (default `http://localhost:5174`) |

Existing databases are upgraded automatically on startup (`backend/migrations.py`).
Back up `backend/data/tracker.db` before upgrading if you want an easy way back.

## Phone reminders (ntfy)
1. Install the **ntfy** app (Android / iOS) or open https://ntfy.sh in a browser.
2. Subscribe to a long, hard-to-guess topic name, e.g. `leetcode-7f3k9q2x`.
   ntfy.sh topics are **public**: anyone who knows the name can read and post to it.
3. In `.env`, set `NTFY_TOPIC=leetcode-7f3k9q2x` and `ENABLE_SCHEDULER=true`, then restart the backend.
4. Send a test: `curl -X POST http://localhost:8000/api/notify/test`. Your phone should buzz.

At `REMINDER_TIME` the app syncs first, then sends "No LeetCode yet today. 🔥 5-day streak at risk."
only if today still has no solve.

## Daily reminder (GitHub Actions)
The in-app reminder only fires while the backend is running. The **Daily reminder** workflow
(`.github/workflows/daily-reminder.yml`) runs on GitHub's servers instead, free, with no
database: at 01:30 and 03:30 UTC (8:30pm and 10:30pm Chicago in summer, an hour earlier in
winter) it runs `backend/scripts/daily_check.py`, which asks LeetCode for an accepted
submission today and sends an ntfy push if there isn't one.

Setup:
1. Create a GitHub repo and push.
2. Settings → Secrets and variables → Actions:
   - add the **secret** `NTFY_TOPIC` (your topic name; it's a secret because anyone who knows it can read it)
   - add the **variable** `LEETCODE_USERNAME=poke213`
   - optionally add the **variable** `TZ` (default `America/Chicago`)
3. Actions tab → "Daily reminder" → **Run workflow** with `force` on. Your phone should buzz.

Notes:
- **60-day rule:** GitHub disables scheduled workflows after 60 days with no commits in a
  public repo. To turn it back on: Actions tab → "Daily reminder" → **Enable workflow**
  (or push any commit).
- If you use this, turn off the in-app scheduler (`ENABLE_SCHEDULER=false`) so you don't get
  two reminders. When the Raspberry Pi deployment happens, choose one reminder.
- Scheduled runs can start 5–30 minutes late.
- It only sees your last 20 accepted submissions, so a very long streak is undercounted in the message.

Try it locally without sending anything (env vars only, no `.env` needed):
```bash
cd backend && LEETCODE_USERNAME=poke213 python scripts/daily_check.py --dry-run
```
`--force` sends even if today is done. A LeetCode failure sends "Couldn't check LeetCode
today. Solve one anyway!" and exits 1, so the run shows red.

## Run in development
Two terminals:
```bash
# 1) Backend on http://localhost:8000
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# 2) Frontend on http://localhost:5174
cd frontend
npm install
npm run dev
```
Open http://localhost:5174. Vite forwards `/api` to the backend, so the tracker's own frontend
needs no CORS setup. (It uses 5174, not Vite's default 5173, so it can run next to another app.)

### Running next to another app (e.g. a dashboard)
Another frontend that calls the tracker API directly from the browser (say on
http://localhost:5173) must be listed in `CORS_ORIGINS`:
```
CORS_ORIGINS=http://localhost:5174,http://localhost:5173
```
Restart the backend after changing it. Then run the tracker (backend on 8000, frontend on 5174)
and the other app on its own ports. Only one app can use port 8000, so give the other app's backend a different port.
API docs (Swagger) are at http://localhost:8000/docs.

## Run with Docker
```bash
docker compose up --build
```
Open http://localhost:5174. nginx serves the built frontend and forwards `/api` to the backend
container. The database is stored on your machine in `backend/data/`, so it survives restarts.

## Run tests and lint
```bash
cd backend && pytest && ruff check .
cd frontend && npm test -- --run && npm run lint
```
Backend tests never touch the network: every LeetCode call is answered by a fake
(`respx`) using JSON fixtures in `backend/tests/fixtures/`. Each test gets its own
temporary SQLite file.

## Architecture
```
Browser (React)
   │  fetch("/api/...")          src/api.js: one function per endpoint
   ▼
Vite dev proxy  /  nginx (Docker)
   ▼
FastAPI  main.py
   ├── routers/     HTTP only: parse the request, call a service, map errors to status codes
   │     health · solves · stats · sync · reviews · patterns · notify
   ├── services/    the actual logic
   │     streaks.py          pure functions, no DB (easy to test)
   │     review_schedule.py  pure spaced-repetition rule: next_state()
   │     reviews.py          review queue (due, upcoming, mark reviewed)
   │     patterns.py         NeetCode 150 seeding + progress
   │     scheduler.py        background sync + evening reminder (APScheduler)
   │     notify.py           ntfy notifications
   │     meta.py             key-value app state (last sync)
   │     stats.py            totals + heatmap
   │     solves.py           add / edit / delete / list
   │     sync.py             LeetCode → DB, idempotent
   │     leetcode_client.py  the ONLY file that talks to LeetCode
   │     clock.py            "what day is it?" in your TZ
   ├── models/      tables.py (DB) and schemas.py (API shapes)
   ├── migrations.py  numbered schema upgrades (schema_version table)
   ├── seed/        neetcode150.json (checked with scripts/verify_seed.py)
   ├── scripts/     verify_seed.py, daily_check.py (GitHub Actions reminder, no DB)
   └── db.py        SQLite engine + session per request
          ▼
     backend/data/tracker.db
```

**Data model.** `problem` (one row per LeetCode problem) and `solve` (one row per day you
solved it). A problem can be solved many times, but only once per day: `(problem_id,
solved_date)` is unique. `solved_date` is your *local* date, computed once when the solve
is saved, so a late-night solve counts for the day you were in.
v2 adds `review` (one row per problem: interval index, next review date), `pattern_list` and
`pattern_problem` (the NeetCode 150, matched to solves by slug), `meta` (last sync), and
`schema_version` (which migrations have run).

**API.** `GET /api/health`, `GET|POST /api/solves`, `PATCH|DELETE /api/solves/{id}`,
`GET /api/stats`, `GET /api/heatmap?days=90`, `POST /api/sync`, and in v2
`GET /api/reviews/due`, `GET /api/reviews/upcoming?days=7`, `POST /api/reviews/{problem_id}`
(`{"confidence": 1-3}`), `GET /api/patterns?list=neetcode150`, `POST /api/notify/test`, and in v3
`GET /api/solves/unrated?days=7` (solves with no confidence from the last N local days, newest first).
See `PLAN.md` §5, `PLAN_V2.md`, `PLAN_V3.md`, or `/docs`.

## About the LeetCode API
LeetCode has no official public API. This app uses the same GraphQL endpoint the website
uses (`https://leetcode.com/graphql`), with the `recentAcSubmissionList` and `question`
queries. The response shapes were checked with real requests before writing the client
and match what the code expects. Notes:
- Only the **last 20** accepted submissions are visible, so sync often if you solve a lot,
  and use manual add for anything older.
- A profile with no recent public accepted submissions returns an empty list, so sync adds 0.
- An unknown username returns `null`, which the app reports as "user not found" (HTTP 502).
- If LeetCode changes the API, only `backend/services/leetcode_client.py` needs fixing.

## What I learned
<!-- Draft: rewrite these in your own words. -->
- Splitting a FastAPI app into routers (HTTP) and services (logic) keeps each file small and testable.
- Writing the tricky logic (streaks) as pure functions made the tests short and obvious.
- Mocking HTTP with `respx` lets tests cover failures (timeouts, unknown users) that are hard to trigger for real.
- Timezones: store UTC, convert to a local date once, and never let the browser guess.
- Idempotent sync: a unique constraint plus "skip if it exists" makes a button safe to click twice.
- Docker multi-stage builds: Node is only needed to build the frontend, not to serve it.

See `LEARNING.md` for the skill each build step practises.
