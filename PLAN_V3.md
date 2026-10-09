# LeetCode Tracker v3: Build Plan

## 1. Context
v2 is on branch `build/v2` (see `PLAN_V2.md`, `README.md`, `LEARNING.md`). This is the owner's **agent-built** project: agents write the code, and the owner writes specs and reviews.

v3 adds two things:
- **A. Quick rating:** logging confidence and "needs review" is too slow today. You have to open a solve, find the fields in `NoteEditor`, and save. Synced solves arrive with no confidence, so their review schedule ignores how the solve actually went. Rating should take **one click**, right when a solve arrives.
- **B. AI solution review (Cancelled by owner):** paste your code and Claude reviews it for correctness and complexity, and suggests a better approach. It acts as a mentor, so it gives hints first and the full solution only on request.

Deployment comes later. Don't add deploy config.

## 2. Ground rules
- Create branch `build/v3` from `build/v2`. Commit `PLAN_V3.md` first.
- **Never push.** Never access `/home/theo/dashboard` in any way.
- Small commits, imperative messages under 60 characters, each ending with a blank line then `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Before **every** commit, run `pytest`, `npm test -- --run`, `ruff check .`, `npm run lint` and `npm run build`.
- No test may hit the network. That includes LeetCode, ntfy and the Anthropic API.
- **Back up** (only if a migration is added) `backend/data/tracker.db` to `backend/data/tracker.db.v2.bak` before the first new migration runs against it.
- Update `README.md` (features, env vars, cost note) and add one line per step to `LEARNING.md`.
- Report each change to this plan under **Deviations** in the final report.

## 3. Feature A: quick rating
### A1. Rating sets the first review interval
Today, PATCHing `confidence` never reschedules (PLAN_V2 §6, trigger 4). Change that in **one case only**: if the solve is its problem's **first** solve, and that review has not been marked reviewed since (`last_reviewed_date` is still the solve date), then setting or changing `confidence` recomputes the first schedule as if the solve had that confidence:
- 1 → index 0 (+1 day)
- 2 → index 0 (+1 day)
- 3 → index 1 (+3 days)

In every other case PATCH still doesn't reschedule. Put the rule in `services/reviews.py` as a small named function with a docstring explaining why.

**Tests:** each confidence on a first solve; a re-solve doesn't reschedule; already reviewed doesn't reschedule.

### A2. Endpoint for unrated solves
`GET /api/solves/unrated?days=7` returns solves with `confidence IS NULL` from the last N local days, newest first, in SolveOut shape.

### A3. `RateSolveCard` component (frontend)
- Shows right under `TodayBanner`, **above** `ReviewQueue`, only when there are unrated solves: "✍️ Rate today's solves (2)".
- One compact row per unrated solve:
  - title (linked) + difficulty badge
  - **Again / Good / Easy** buttons, reusing the same labels and colours as `ReviewQueue` (move the `BUTTONS` constant to a shared `src/ratings.js`)
  - a "🔁 flag for review" toggle
  - optional time chips **15 / 30 / 45 / 60+ min**
- **One click on Again, Good or Easy saves everything** with one PATCH (confidence + needs_review + time if a chip was picked). Then the row disappears and stats, the heatmap and reviews refetch.
- "Skip" hides the row for this session only.
- After **Sync now** adds solves, the card appears automatically, because the refetch after sync already runs.

### A4. Rate while adding manually
`AddSolveForm` gets the same three rating buttons and the review toggle, inline and optional. If a rating is picked, the POST body includes `confidence` and `needs_review`. **Enter** still submits with no rating.

### A5. Inline rating in the table
In `SolveTable`, an unrated row shows a small "Rate" chip in the confidence column. Clicking it expands the same three buttons in place, without opening `NoteEditor`.

**Frontend tests:**
- The card renders only when there are unrated solves.
- Clicking Good sends PATCH with `{confidence: 2, needs_review: false}`, plus `time_spent_min` when a chip was picked.
- Skip hides the row.
- AddSolveForm includes the rating in the POST body only when one is picked.

## 4. Feature B: AI solution review **(Cancelled by owner)**
> Cancelled by owner: no API spend. Nothing in this section is built. Kept for reference only.

### B1. SDK and config
- Add `anthropic` to `requirements.txt`, pinned to the current release.
- **Model:** `claude-opus-5-5`. Don't change it to another model.
- **Credentials:** the SDK reads `ANTHROPIC_API_KEY` from the **process environment**. `pydantic-settings` loads `.env` into the settings object, not into `os.environ`.
  - Add an optional `anthropic_api_key` setting.
  - Build the client with `anthropic.Anthropic(api_key=settings.anthropic_api_key)` when it is set, and plain `anthropic.Anthropic()` otherwise, which also picks up an `ant auth login` profile.
- **New `.env.example` keys:**
  - `ANTHROPIC_API_KEY=`
  - `AI_REVIEW_EFFORT=medium`
  - `AI_REVIEW_DAILY_LIMIT=10`

  Append the same keys to the owner's `.env`, with `ANTHROPIC_API_KEY` empty. Don't change anything else in it.

### B2. Problem description
- Extend `leetcode_client.get_question` to also request `content`, which is the problem statement as HTML.
- Add a nullable `description` column to `problem` (new migration). Store the statement as plain text: strip the tags with the standard library (`html.parser`), and don't add a new dependency.
- Fill it in lazily: when an AI review needs it and it's null, fetch it then.
- If the fetch fails, review without it and say so in the prompt.
- Update the fixtures to include `content`.

### B3. Service: `services/ai_review.py`
- Use `client.messages.parse(...)` with a Pydantic `output_format`, so you get a validated object back with no hand-parsing.

  ```python
  class AIReview(BaseModel):
      verdict: Literal["correct", "likely_bug", "incorrect", "unsure"]
      summary: str                 # 1-2 sentences
      time_complexity: str         # e.g. "O(n)"
      space_complexity: str
      complexity_matches_user: bool | None   # None if the user gave none
      issues: list[str]            # concrete bugs or edge cases, max 5
      hints: list[str]             # nudges toward a better solution, without giving it away, max 3
      better_approach: str | None  # name + 1-3 sentence idea, or None if already optimal
      improved_solution: str | None  # full code in the same language, or None
      interview_tip: str           # one tip on how to explain this in an interview
  ```

- `output_config={"effort": settings.ai_review_effort}`. Set it explicitly, because this model defaults to `medium`.
- `max_tokens=16000`. Don't send a `thinking` parameter (adaptive is the default on this model).
- **Refusal fallbacks:** this skill's default for `claude-opus-5-5` is server-side fallbacks with `betas=["server-side-fallback-2026-07-01"]` and `fallbacks="default"`, through the **beta** client (`client.beta.messages.parse`).
  - If that combination is rejected by the installed SDK or the API, drop fallbacks and use plain `client.messages.parse`, and record it as a Deviation.
  - Either way, **check `stop_reason` before using the output.** A `"refusal"` becomes a clear error ("Claude declined to review this. Try rewording your notes.") and is never treated as a review.
  - `"max_tokens"` becomes a "review was cut off" error.
- **System prompt** (keep it short and stable, so it can be cached later): a senior engineer reviewing a junior's LeetCode solution, as a mentor.
  - Judge correctness carefully.
  - Give hints before answers.
  - Be specific: name the line or the case that breaks.
  - Use plain language.
  - Fill `improved_solution` only if a meaningfully better solution exists.
- **User message:** problem title, difficulty, statement (or "statement unavailable"), language, the user's code, and the user's own approach and complexities if given.
- **Errors:** catch the typed exceptions most specific first (`AuthenticationError` → `RateLimitError` → `APIStatusError` → `APIConnectionError`), and raise one `AIReviewError(message, status)` that the router maps to an HTTP status.
- **Testability:** the service takes the client as a parameter (dependency injection). Tests pass a fake object with a `messages.parse` (or `beta.messages.parse`) method that returns canned responses. **Tests must never construct a real client.**

### B4. Storage
New table `ai_review`, added as a migration:

| column | type | notes |
|---|---|---|
| id | int PK | |
| solve_id | FK → solve.id | |
| created_at | datetime UTC | |
| model | str | `response.model`, which may be a fallback model |
| effort | str | |
| result | text (JSON) | the AIReview |
| input_tokens | int | from `response.usage` |
| output_tokens | int | |
| request_id | str | `response._request_id`, for debugging |

Deleting a solve deletes its reviews.

### B5. Endpoints
| Method | Path | Behaviour |
|---|---|---|
| POST | `/api/solves/{id}/ai-review` | 404 if no such solve; **400** if the solve has no `code`; **429** if `AI_REVIEW_DAILY_LIMIT` reviews already ran today (local date); **503** with "Set ANTHROPIC_API_KEY in .env" if there are no credentials; **502** on API errors or a refusal. On success, saves the review and returns `{review: AIReview, model, created_at, input_tokens, output_tokens, est_cost_usd}` |
| GET | `/api/solves/{id}/ai-review` | The latest saved review, or 404 |
| GET | `/api/ai-review/usage` | `{today_count, daily_limit, total_input_tokens, total_output_tokens, est_cost_usd_total}` |

`est_cost_usd` uses $4 per million input tokens and $20 per million output tokens, kept as named constants with a comment saying where they come from. Label it an estimate.

### B6. UI
- In `NoteEditor`, under the code box, add an **"🤖 Review my solution"** button.
  - It is disabled when the code is empty. It **saves first**, then reviews, so the review always uses the saved code.
  - While it runs: a spinner and "Reviewing… (can take ~30s)". A double-click must not send two requests.
- **`AIReviewPanel`** shows:
  1. A verdict badge (✅ correct / ⚠️ likely bug / ❌ incorrect / ❔ unsure) and the summary.
  2. Complexities, with a ✓ or ✗ when they match or don't match what the user wrote.
  3. Issues and hints as lists.
  4. Better approach.
  5. **Improved solution collapsed by default** behind "Show improved solution (spoiler)". The point is learning, so the user should try the hints first.
  6. The interview tip.
  7. A footer with the model, the date and the estimated cost.
- A small **"Use these complexities"** button fills the editor's complexity fields from the review, without saving automatically.
- The latest saved review loads automatically when a solve is opened.
- In `SolveTable`, show a 🤖 marker for solves that have a review.
- In `StatsPanel`, add a line: "AI reviews today: 3/10 · ~$0.12 total".

### B7. Tests
- **Backend** (fake client, no network):
  - a correct parse is stored and returned
  - a refusal gives a 502 and nothing is stored
  - max_tokens gives a 502
  - no code gives a 400
  - the daily limit gives a 429
  - no credentials gives a 503
  - an AuthenticationError maps correctly
  - the description is fetched lazily and stored (respx mocks LeetCode)
  - HTML stripping
  - the cost math
  - deleting a solve deletes its reviews
  - the migration upgrades a v2 DB
- **Frontend:**
  - the button is disabled when there's no code
  - it calls save, then review
  - the panel renders each verdict
  - the improved solution is hidden until clicked
  - "Use these complexities" fills the fields

### B8. Real API calls
- **At most 2 real Anthropic calls in total** for the whole build. Make them only if credentials resolve: `ANTHROPIC_API_KEY` is set, or `ant auth status` shows an active profile.
  - Use Two Sum with a deliberately buggy solution, then a correct one.
  - Report the verdicts, the token counts and the estimated cost.
- If no credentials resolve, don't ask for any. Finish with mocks only, and say in the report that a real review is untested.

## 5. Build order (each = 1+ commits)
| # | Step | Est. |
|---|---|---|
| 1 | A1 + A2 backend + tests | 30 min |
| 2 | Shared `ratings.js`, RateSolveCard, AddSolveForm rating, SolveTable inline rating + tests | 1 h |
| 3 | ~~Migration (problem.description, ai_review), description fetch + fixtures~~ Cancelled by owner | — |
| 4 | ~~`ai_review.py` + endpoints + tests~~ Cancelled by owner | — |
| 5 | ~~NoteEditor button, AIReviewPanel, table marker, stats line + tests~~ Cancelled by owner | — |
| 6 | ~~Real-call check (B8)~~ (Cancelled by owner), README, LEARNING.md | 20 min |

## 6. Definition of done
- [ ] All checks pass (§2), with counts reported.
- [ ] The real DB upgrades with data intact, and the `.v2.bak` backup exists. (Only if a migration is added; Feature A needs none.)
- [ ] Rating an unrated solve takes **one click** from the Today view, and the review date reflects the rating.
- [ ] Manual add with a rating stores it in one request.
- ~~The AI review works end to end with a fake client in tests, and with a real call if credentials existed (B8).~~ Cancelled by owner
- ~~The improved solution is hidden until clicked.~~ Cancelled by owner
- ~~A refusal and a missing key both show clear messages, never a crash or a blank panel.~~ Cancelled by owner
- [ ] Nothing pushed; `~/dashboard` not accessed.

## 7. Final report
1. Definition-of-done checklist with ✅/❌.
2. Test counts.
3. New env vars.
4. Real API call results, or "untested: no credentials".
5. The exact SDK call used: fallbacks on or off, and why.
6. Deviations.
7. Anything unfinished, with the error text.
