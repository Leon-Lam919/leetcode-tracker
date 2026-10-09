# LeetCode Tracker

![CI](https://github.com/OWNER/leetcode-tracker/actions/workflows/ci.yml/badge.svg)
<!-- Replace OWNER with your GitHub username after pushing. -->

A small full-stack app for a simple habit: **solve one LeetCode problem a day.**
It shows whether today is done, keeps your streak, draws a 90-day heatmap, and
stores notes on each solve so you can review problems later.

![Screenshot](docs/screenshot.png)
<!-- Screenshot placeholder: add docs/screenshot.png. -->

## Features
- **Today banner:** ✅ done / ❌ not yet, current streak 🔥 and best streak
- **Sync now:** pulls your last 20 accepted submissions from LeetCode (safe to click twice)
- **Manual add:** paste a problem URL or slug, for older solves or when LeetCode is down
- **Notes:** time spent, confidence (1–3), free-text notes, "needs review" flag
- **Heatmap and stats:** 90-day grid, totals by difficulty, top topics
- **Filters:** by difficulty, topic, or needs-review
- Works on a phone (375px) and in dark mode

## Stack
| Layer | Tools |
|---|---|
| Backend | Python 3.12, FastAPI, SQLModel on SQLite, httpx, loguru |
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

## Run in development
Two terminals:
```bash
# 1) Backend on http://localhost:8000
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# 2) Frontend on http://localhost:5173
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. Vite forwards `/api` to the backend, so there is no CORS setup in dev.
API docs (Swagger) are at http://localhost:8000/docs.

## Run with Docker
```bash
docker compose up --build
```
Open http://localhost:5173. nginx serves the built frontend and forwards `/api` to the backend
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
   │     health · solves · stats · sync
   ├── services/    the actual logic
   │     streaks.py          pure functions, no DB (easy to test)
   │     stats.py            totals + heatmap
   │     solves.py           add / edit / delete / list
   │     sync.py             LeetCode → DB, idempotent
   │     leetcode_client.py  the ONLY file that talks to LeetCode
   │     clock.py            "what day is it?" in your TZ
   ├── models/      tables.py (DB) and schemas.py (API shapes)
   └── db.py        SQLite engine + session per request
          ▼
     backend/data/tracker.db
```

**Data model.** `problem` (one row per LeetCode problem) and `solve` (one row per day you
solved it). A problem can be solved many times, but only once per day: `(problem_id,
solved_date)` is unique. `solved_date` is your *local* date, computed once when the solve
is saved, so a late-night solve counts for the day you were in.

**API.** `GET /api/health`, `GET|POST /api/solves`, `PATCH|DELETE /api/solves/{id}`,
`GET /api/stats`, `GET /api/heatmap?days=90`, `POST /api/sync`. See `PLAN.md` §5 or `/docs`.

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
