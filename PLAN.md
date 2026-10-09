# LeetCode Tracker: Build Plan

## 1. Context
The owner is a CS grad working toward a junior dev role. Goal: solve **1 LeetCode problem per day**. The tracker shows whether today is done, keeps a streak, and stores notes so solved problems can be reviewed later.

It is also a **portfolio project**. Tests, CI, and a clear README are required, not optional. Code must be readable by a junior: short functions, plain names, and comments only where the reason isn't obvious.

## 2. Stack and versions
Mirror `~/dashboard` (FastAPI + React/Vite/Tailwind) so the owner already knows the patterns. Read `~/dashboard/backend/main.py`, `routers/`, and `services/` for style before starting. Don't modify `~/dashboard`.

| Layer | Choice |
|---|---|
| Python | 3.12 |
| Backend | FastAPI, Uvicorn, SQLModel (on SQLite), `httpx`, `loguru`, `python-dotenv`, `pydantic-settings` |
| Backend tests | pytest, `respx` (mocks httpx), FastAPI `TestClient` |
| Node | 24 LTS (in Docker and CI) |
| Frontend | React 19, Vite 7, Tailwind 3.4 |
| Frontend tests | Vitest, React Testing Library, jsdom |
| Lint | `ruff` (backend), ESLint from the Vite template (frontend) |
| Infra | Docker Compose, GitHub Actions |

Pin exact versions in `requirements.txt` and commit `package-lock.json`.

No chart or heatmap libraries. Build the heatmap with a CSS grid, because that is simpler and a better learning example.

## 3. Ports and config
- Backend: `http://localhost:8000`, all routes under `/api`
- Frontend dev: `http://localhost:5173`. The Vite dev server proxies `/api` to `:8000`, so the frontend needs no CORS setup in dev.
- Also enable FastAPI `CORSMiddleware` for `http://localhost:5173` as a fallback.

`.env.example` (committed); `.env` is gitignored:
```
LEETCODE_USERNAME=your_username
TZ=America/Toronto
DATABASE_URL=sqlite:///./data/tracker.db
DAILY_GOAL=1
```
`TZ` must be an IANA name, loaded with `zoneinfo.ZoneInfo`. Fail fast with a clear error if it is invalid.

## 4. Data model
Two tables. A problem can be solved more than once (re-solves are good practice), so solves are separate from problems.

**problem**
| column | type | notes |
|---|---|---|
| id | int PK | |
| title_slug | str, **unique** | e.g. `two-sum` |
| title | str | |
| difficulty | str | `Easy` / `Medium` / `Hard` |
| topics | str (JSON list) | e.g. `["Array","Hash Table"]` |
| url | str | `https://leetcode.com/problems/{slug}/` |

**solve**
| column | type | notes |
|---|---|---|
| id | int PK | |
| problem_id | FK → problem.id | |
| solved_at | datetime, UTC | from the LeetCode timestamp, or now() for a manual entry |
| solved_date | date | **local** date in `TZ`, computed once at insert |
| source | str | `sync` or `manual` |
| time_spent_min | int, nullable | |
| confidence | int 1–3, nullable | 1 = needed help, 3 = solved cleanly |
| notes | str, default `""` | |
| needs_review | bool, default false | |

Unique constraint: `(problem_id, solved_date)`. Solving the same problem twice in one day is one solve.

Create tables on startup with `SQLModel.metadata.create_all`. No migration tool for the MVP. The DB file lives in `backend/data/`, which is gitignored and mounted as a Docker volume.

## 5. API contract
All JSON. Errors use FastAPI's default `{"detail": ...}` shape.

| Method | Path | Body / query | Returns |
|---|---|---|---|
| GET | `/api/health` | | `{"status":"ok"}` |
| GET | `/api/solves` | `?difficulty=&topic=&needs_review=` | list of SolveOut, newest first |
| POST | `/api/solves` | SolveCreate (manual add) | SolveOut, 201. 409 if a duplicate for that day |
| PATCH | `/api/solves/{id}` | SolveUpdate (notes fields only) | SolveOut. 404 if missing |
| DELETE | `/api/solves/{id}` | | 204 |
| GET | `/api/stats` | | Stats |
| GET | `/api/heatmap` | `?days=90` | `[{"date":"2026-10-08","count":1}, ...]`, oldest first, includes zero days |
| POST | `/api/sync` | | `{"added": 2, "skipped": 18}`. 502 if LeetCode fails |

**SolveOut**
```json
{"id":1,"title":"Two Sum","title_slug":"two-sum","difficulty":"Easy",
 "topics":["Array","Hash Table"],"url":"https://leetcode.com/problems/two-sum/",
 "solved_at":"2026-10-08T14:03:00Z","solved_date":"2026-10-08","source":"sync",
 "time_spent_min":25,"confidence":2,"notes":"","needs_review":false}
```
**SolveCreate:** `title_slug` (required). The backend looks up the title, difficulty, and topics via `leetcode_client.get_question`. If that lookup fails, it accepts optional `title`, `difficulty`, and `topics` from the body instead. Optional: `solved_date` (defaults to today local) plus the note fields.

**SolveUpdate:** any of `time_spent_min`, `confidence`, `notes`, `needs_review`. Validate `confidence` in 1–3 and `time_spent_min` ≥ 0.

**Stats**
```json
{"today_done":true,"today_count":1,"daily_goal":1,
 "current_streak":5,"longest_streak":12,"total_solved":40,
 "by_difficulty":{"Easy":20,"Medium":17,"Hard":3},
 "by_topic":{"Array":15,"Hash Table":9}}
```
`total_solved` and the breakdowns count **distinct problems**, not solves.

## 6. Streak rules (`services/streaks.py`)
Pure functions taking `list[date]` and `today: date`, with no DB access, so they are easy to test.
- A day counts if it has ≥ `DAILY_GOAL` solves.
- **current_streak:** consecutive counted days ending today. If today isn't counted yet but yesterday is, the streak is still alive and counts back from yesterday (you have until midnight). If neither counts, it is 0.
- **longest_streak:** the longest run of consecutive counted days ever.
- Duplicate dates and unsorted input must be handled.

Required tests: empty list → 0/0; only today → 1/1; yesterday only → current 1; gap of 2 days → current 0; unsorted with duplicates; longest run in the past bigger than current; `DAILY_GOAL=2` with one solve in a day doesn't count.

## 7. LeetCode client (`services/leetcode_client.py`)
**All** LeetCode calls live in this one module, because the API is unofficial and may change.

- `POST https://leetcode.com/graphql`
- Headers: `Content-Type: application/json`, `Referer: https://leetcode.com`, plus a normal browser `User-Agent`
- Timeout: 10s. On failure, retry once, then raise `LeetCodeError`.

```graphql
query recentAc($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    title titleSlug timestamp
  }
}
```
`timestamp` is a **string** of Unix seconds. Convert it to UTC datetime, then to a local date with `TZ`.

```graphql
query question($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    title titleSlug difficulty topicTags { name }
  }
}
```

**Functions:** `get_recent_accepted(username, limit=20) -> list[RecentAc]` and `get_question(slug) -> QuestionInfo`.

**Sync logic** (`services/sync.py`):
1. Fetch the last 20 accepted submissions.
2. For each one: upsert the problem, calling `get_question` only if the problem isn't in the DB yet.
3. Insert the solve if `(problem_id, solved_date)` doesn't exist yet; otherwise count it as skipped.
4. Never overwrite notes on an existing solve.
5. Sync must be **idempotent**: running it twice in a row gives `added: 0` the second time.

An unknown username, or `recentAcSubmissionList` returning `null`, → `LeetCodeError("user not found")` → 502 with a clear message.

**Tests mock HTTP with `respx`. No test may hit the real network.** Save sample responses as JSON fixtures in `backend/tests/fixtures/`.

Before writing the client, make **one** real manual request (curl) with a known public username to confirm the response shape, and save it as the fixture. If the endpoint is blocked or the shape differs, adapt the client to the real shape and note it in the README. If LeetCode is unreachable entirely, finish everything else with manual add working and report the problem.

## 8. Frontend
Plain `fetch` wrappers in `src/api.js`, one function per endpoint. State is React `useState`/`useEffect` only: no Redux and no React Query. Refetch stats and the heatmap after any change.

| Component | Does |
|---|---|
| `TodayBanner` | Big ✅ "Done today" / ❌ "Not yet today", 🔥 current streak, best streak |
| `SyncButton` | Calls `/api/sync` and shows "Added 2" or the error message; disabled while running |
| `Heatmap` | 90 cells in a 7-row CSS grid (weeks as columns); colour by count; `title` tooltip shows date + count; today outlined |
| `StatsPanel` | Totals by difficulty (green/yellow/red) and the top 5 topics |
| `SolveTable` | Title links to LeetCode, difficulty badge, date, topics, confidence, review flag; click a row to open `NoteEditor` |
| `NoteEditor` | Edits time, confidence, notes, needs_review; save calls PATCH |
| `AddSolveForm` | Manual add by slug or URL (extract the slug from a pasted URL) |
| `Filters` | Difficulty, topic, needs-review |

**UI requirements:** works at 375px phone width; dark-mode friendly via Tailwind `dark:` classes; loading and error states on every fetch (no blank screens).

**Frontend tests (minimum):** TodayBanner renders both states; slug extraction from a URL; Heatmap renders 90 cells with today marked; NoteEditor calls PATCH with the right body (mock `fetch`).

## 9. Docker
- `backend/Dockerfile`: `python:3.12-slim`, install requirements, run `uvicorn main:app --host 0.0.0.0 --port 8000`
- `frontend/Dockerfile`: multi-stage. A `node:24-alpine` build stage, then an `nginx:alpine` stage serving `dist/`, with an `nginx.conf` that proxies `/api` to `backend:8000`
- `docker-compose.yml`: `backend` (env_file `.env`, volume `./backend/data:/app/data`, healthcheck on `/api/health`) and `frontend` (port `5173:80`, `depends_on` backend healthy)

## 10. CI (`.github/workflows/ci.yml`)
Triggers: push and pull_request. Two jobs on `ubuntu-latest`:
- **backend:** set up Python 3.12, `pip install -r requirements.txt`, `ruff check .`, `pytest`
- **frontend:** set up Node 24 with an npm cache, `npm ci`, `npm run lint`, `npm test -- --run`, `npm run build`

Add the CI status badge to the README.

## 11. Build order
Work on a feature branch `build/mvp`. **One commit per step.** Run that step's check before committing. Don't move on with a failing check.

| # | Step | Check before commit |
|---|---|---|
| 1 | Scaffold: `.gitignore`, `.env.example`, README stub, folder structure, `requirements.txt`, Vite app | `pip install` and `npm install` succeed |
| 2 | Config (`config.py`), DB (`db.py`), models, `/api/health` | `pytest` health test passes |
| 3 | `streaks.py` + all streak tests | `pytest tests/test_streaks.py` |
| 4 | Solve CRUD + stats + heatmap routes + tests (temp SQLite per test) | `pytest` |
| 5 | Real curl call → save fixtures; `leetcode_client.py` + `sync.py` + `/api/sync` + mocked tests (incl. idempotency, user not found) | `pytest`; one real manual sync works |
| 6 | Frontend: `api.js`, TodayBanner, SyncButton, SolveTable, NoteEditor, AddSolveForm | `npm test`, and it works in the browser against the dev backend |
| 7 | Heatmap, StatsPanel, Filters, responsive and dark-mode pass | `npm test`, check at 375px |
| 8 | Dockerfiles, nginx.conf, compose | `docker compose up --build`, app works on :5173 |
| 9 | CI workflow + lint fixes | `ruff check .`, `npm run lint` pass locally |
| 10 | README (what it does, screenshot placeholder, setup, run tests, architecture sketch, "what I learned") + `LEARNING.md` | Read it once top to bottom |

**Commit message style:** imperative, under 60 characters, e.g. `Add streak calculation with tests`.

Estimated agent time: 2–3 hours. Owner review: about 1 hour.

## 12. Definition of done
- [ ] `cd backend && pytest`: all pass, no network calls
- [ ] `cd frontend && npm test -- --run`: all pass
- [ ] `ruff check .` and `npm run lint` are clean
- [ ] `docker compose up --build`: the app loads at `http://localhost:5173`
- [ ] **Sync now** with a real username adds recent solves; running it a second time adds 0
- [ ] Banner shows ✅ when today has a solve; the streak number is correct
- [ ] Editing a note survives a page refresh and a container restart
- [ ] Manual add works with a pasted LeetCode URL
- [ ] No secrets or `.db` files in git (`git ls-files` checked)
- [ ] `LEARNING.md` has one line per step naming the skill it shows

## 13. Rules for the building agent
- Don't push to a remote or create a GitHub repo. The owner will do that.
- Don't touch any folder outside `~/leetcode-tracker` (read-only access to `~/dashboard` for style).
- If something in this plan turns out wrong (API shape, version conflict), make the smallest change that works and list each change in a **"Deviations"** section at the end of the final report.
- Final report: what works, how to run it, test counts, deviations, and anything left undone. Be honest about failures.
- If the owner hasn't set `LEETCODE_USERNAME`, use any well-known public profile only for the one manual fixture call, then leave `.env.example` with a placeholder.
