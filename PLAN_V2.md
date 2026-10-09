# LeetCode Tracker v2: Build Plan

## 1. Context
The v1 MVP is done on branch `build/mvp` (see `PLAN.md`, `README.md`, `LEARNING.md`). Sync is confirmed working: `recentAcSubmissionList` for `poke213` now returns `Two Sum`.

v2 adds five features. The goal is interview prep: re-solving problems, covering every pattern, and keeping the daily habit going. The same code-quality rules as v1 apply (`PLAN.md` §1 and §13).

## 2. Ground rules
- **Tracker:** create branch `build/v2` from `build/mvp`. Commit `PLAN_V2.md` first.
- **Dashboard (feature 5 only):** in `~/dashboard`, create branch `leetcode-widget` from `master`.
  - **Never push.** `~/dashboard/.github/workflows/deploy.yml` deploys to a Raspberry Pi on every push to `master`.
  - Don't merge, and don't touch `news-widget-feat` or any other branch.
- Small commits, imperative messages under 60 characters, each ending with a blank line then `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Run `pytest`, `npm test -- --run`, `ruff check .` and `npm run lint` before **every** commit.
- No test may hit the network or send a real notification.
- Add one line per feature to `LEARNING.md`, and update `README.md` (features, new env vars, screenshots placeholder).
- Report each change to this plan under **Deviations** in the final report.

## 3. Build order
Do schema changes first, because features 1 and 4 both add columns.

| # | Feature | Est. |
|---|---|---|
| A | Lightweight migrations + feature 4 (solution fields) | 45 min |
| B | Feature 1: review queue | 1.5 h |
| C | Feature 2: pattern checklist | 1.5 h |
| D | Feature 3: auto-sync + reminder | 1 h |
| E | Feature 5: dashboard widget | 1 h |

## 4. Migrations (`backend/migrations.py`)
`SQLModel.metadata.create_all` creates new tables but **doesn't add columns to existing ones**. The owner's DB already has data, so:
- Keep a `schema_version` table with one row.
- Keep an ordered list of migration functions. Each one is plain SQL (`ALTER TABLE ... ADD COLUMN ...`, `CREATE TABLE ...`).
- On startup, run every migration newer than the stored version inside a transaction, then bump the version.
- Running it on a fresh DB and on an existing v1 DB must both work.
- **Test:** build a v1-shaped DB in a temp file, run the migrations, and check that the new columns exist and old rows survive. Running them twice is a no-op.

Explain in `LEARNING.md` why tools like Alembic exist; this is the hand-rolled version of the same idea.

## 5. Feature 4: solution fields
New nullable columns on `solve`:

| column | type | notes |
|---|---|---|
| approach | text | e.g. "hash map of value → index, one pass" |
| code | text | |
| language | str | default `python3` |
| time_complexity | str | e.g. `O(n)` |
| space_complexity | str | |

- Add them to `SolveUpdate` and `SolveOut`, and to `PATCH /api/solves/{id}`.
- **UI:** in `NoteEditor`, add the approach field, a language select, a monospace code textarea (with tab-key indentation, if that's simple), and the two complexity fields.
- **Solve table:** a small "📝" marker when a solve has an approach or code.
- **Tests:** PATCH round-trip for the new fields, plus a NoteEditor test for the PATCH body.

## 6. Feature 1: review queue (spaced repetition)
Each solve gets a review schedule, tracked per **problem**, not per solve.

**New table `review`:**

| column | type | notes |
|---|---|---|
| problem_id | FK, unique | |
| interval_index | int | index into `INTERVALS` |
| next_review_date | date, nullable | local date; null means mastered |
| last_reviewed_date | date | |

`INTERVALS = [1, 3, 7, 14, 30]` (days). Put the logic in a pure module, `services/review_schedule.py`:

`next_state(interval_index, confidence, today) -> (new_index, next_date | None)`
- `confidence` 1 → index 0 (start over)
- `confidence` 2 or None → index + 1
- `confidence` 3 → index + 2
- Cap at `len(INTERVALS) - 1`. If the problem was **already** at the last index and confidence ≥ 2, it is mastered: `next_date = None`.
- `next_date = today + INTERVALS[new_index]`

**Triggers:**
1. **A new problem's first solve** (sync or manual) creates a review row with index 0 and `next_review_date = solved_date + 1`.
2. **Re-solving** a problem that already has a review row (it appears again in sync on a later day) counts as a review with confidence 2, or the solve's confidence if set.
3. **`POST /api/reviews/{problem_id}`** with body `{"confidence": 1-3}` marks it reviewed today, without a re-solve.
4. **Changing a solve's confidence** with PATCH doesn't reschedule. Keep it simple.

**Endpoints:**
- `GET /api/reviews/due` → problems where `next_review_date <= today`, oldest first, with title, difficulty, URL, days overdue, last confidence and the solve's approach.
- `GET /api/reviews/upcoming?days=7` → counts per day.

**Stats:** add `reviews_due` to `/api/stats`.

**UI:** a `ReviewQueue` component under `TodayBanner`:
- "🔁 3 to review today", listing each problem with buttons **Again** (1), **Good** (2) and **Easy** (3), plus a link to the problem.
- An empty state: "Nothing to review today 🎉".

Backfill existing problems on migration: one review row each, based on their latest `solved_date`.

**Tests:**
- `next_state`, every branch: each confidence value, the cap, and mastered.
- The first-solve and re-solve triggers.
- The due query, including the timezone boundary.
- The endpoint.
- A frontend test that the buttons call POST with the right confidence.

## 7. Feature 2: pattern checklist (NeetCode 150)
- **Seed file:** `backend/seed/neetcode150.json`, a list of `{"slug","title","difficulty","pattern"}` entries. It has 150 entries across the standard 18 NeetCode categories: Arrays & Hashing, Two Pointers, Sliding Window, Stack, Binary Search, Linked List, Trees, Heap / Priority Queue, Backtracking, Tries, Graphs, Advanced Graphs, 1-D Dynamic Programming, 2-D Dynamic Programming, Greedy, Intervals, Math & Geometry, and Bit Manipulation.
- **Verify slugs:** `backend/scripts/verify_seed.py` calls `leetcode_client.get_question` for each slug at **1 request per second**. It reports any slug that returns null and checks that the difficulty matches.
  - Run it once for real.
  - Fix wrong slugs and difficulties in the JSON.
  - Note in the report how many needed fixing.
  - If LeetCode blocks the run partway, keep what was verified and report it.
- **Tables:**
  - `pattern_list(id, name)`, seeded with "NeetCode 150"
  - `pattern_problem(list_id, slug, title, difficulty, pattern, position)`
  - Seed on startup only if the list is empty (idempotent).
- **Endpoint:** `GET /api/patterns?list=neetcode150` returns `[{pattern, total, solved, problems: [{slug, title, difficulty, url, solved, needs_review}]}]` in NeetCode order. "Solved" means a `solve` exists for that slug, joined on `title_slug`.
- **UI:** a `PatternChecklist` component, put on a second tab (add simple "Today" / "Patterns" tabs, with no router library).
  - One collapsible row per pattern, with a progress bar: "Two Pointers 3/5".
  - Solved problems show ✅. Unsolved ones link to LeetCode.
  - An overall progress number at the top: "23 / 150".
- **Tests:** seed idempotency, the solved join, the endpoint shape, and a frontend test for the progress bar text.

## 8. Feature 3: auto-sync + evening reminder
- **Library:** APScheduler `BackgroundScheduler`, using the `TZ` timezone. Start it in the FastAPI lifespan, and only when `ENABLE_SCHEDULER=true`. Tests always run with it off.
- **Jobs:**
  1. Sync every `SYNC_INTERVAL_HOURS` (default 3). Log the result. Catch every exception, because a failed sync must never crash the app.
  2. At `REMINDER_TIME` (default `20:00`), sync first. If `today_done` is still false, send a notification.
- **Notification:** `services/notify.py` with `send(title, message)`.
  - It POSTs to `{NTFY_SERVER}/{NTFY_TOPIC}` (default server `https://ntfy.sh`), with a `Title` header and the message as the body. Example message: "No LeetCode yet today. 🔥 5-day streak at risk." with the streak number filled in.
  - If `NTFY_TOPIC` is empty, it logs and skips.
  - Tests mock it with `respx`.
- **Last sync:** store `last_sync_at` and `last_sync_result` in a `meta` key–value table, and add both to `/api/stats`. The UI shows "Synced 12 min ago" next to the Sync button.
- **`POST /api/notify/test`:** sends a test notification so the owner can confirm their phone setup. **The agent must not call it for real.**
- **New `.env.example` keys:** `ENABLE_SCHEDULER=false`, `SYNC_INTERVAL_HOURS=3`, `REMINDER_TIME=20:00`, `NTFY_SERVER=https://ntfy.sh`, `NTFY_TOPIC=`.
  - Add a README section: install the ntfy app, subscribe to a hard-to-guess topic name (ntfy.sh topics are public), set `NTFY_TOPIC`, then hit the test endpoint.
  - Don't edit the owner's `.env` beyond appending the new keys with safe defaults (`ENABLE_SCHEDULER=false`, empty `NTFY_TOPIC`).
- **Tests:**
  - The reminder job sends only when today isn't done.
  - Sync failure is caught and logged.
  - `last_sync_at` gets updated.
  - `REMINDER_TIME` parsing rejects bad values.

## 9. Feature 5: dashboard widget (`~/dashboard`)
Before writing anything, read `~/dashboard/frontend/src/App.jsx` and `src/components/news/*` and match their structure, Tailwind style, and data fetching exactly.

- **Tracker side** (`build/v2`): add a `CORS_ORIGINS` env var (comma-separated), defaulting to `http://localhost:5173`. Document adding the dashboard's origin.
  - The tracker's frontend also uses 5173. Move the tracker's dev frontend to **5174** in `vite.config.js`, compose, and the README, so both can run at once. Update `CORS_ORIGINS` to match.
- **Dashboard side** (`leetcode-widget` branch, **frontend only**; don't modify the dashboard backend):
  - `frontend/src/components/leetcode/LeetCodeWidget.jsx` fetches `${VITE_LEETCODE_TRACKER_URL}/api/stats`.
  - It shows ✅/❌ today, the 🔥 streak, the reviews due, and a link to open the tracker.
  - It refreshes every 5 minutes.
  - When the tracker is unreachable, it shows a quiet "Tracker offline" state and doesn't break the page.
  - Add it to `App.jsx` next to the news widget.
  - Add `VITE_LEETCODE_TRACKER_URL=http://localhost:8000` to `frontend/.env.development`. Leave `.env.production` with a commented placeholder, because the Pi's tracker URL is unknown.
- **Check:** `npm run build` and `npm run lint` pass in `~/dashboard/frontend`. Run both apps locally and confirm the widget shows live data, and shows the offline state with the tracker stopped.
- In the final report, list exactly which dashboard files changed. The owner reviews dashboard code closely.

## 10. Definition of done
- [ ] All tracker tests pass, and the counts are reported. Lint is clean in both repos.
- [ ] The migration upgrades a v1 DB without data loss (tested), and the owner's real `backend/data/tracker.db` upgrades on startup.
- [ ] After a sync, Two Sum shows in the review queue tomorrow (shown in a test with a faked "today").
- [ ] Pattern tab shows 150 problems across 18 patterns. Two Sum is ✅ under Arrays & Hashing.
- [ ] With `ENABLE_SCHEDULER=true` and a short interval set temporarily, the scheduled sync runs and `last_sync_at` updates. Restore the defaults afterward.
- [ ] No real notification is sent.
- [ ] Dashboard widget shows live tracker data, and shows "Tracker offline" when the tracker is stopped.
- [ ] Nothing pushed; `~/dashboard` changes only on `leetcode-widget`.
- [ ] The README and `LEARNING.md` are updated.

## 11. Final report
1. Definition-of-done checklist with ✅/❌.
2. Test counts.
3. New env vars.
4. How to run both apps together.
5. Seed verification result (how many slugs were fixed).
6. Dashboard files changed.
7. Deviations.
8. Anything unfinished, with the error text.
