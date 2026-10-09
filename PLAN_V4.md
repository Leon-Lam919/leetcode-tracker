# LeetCode Tracker v4: GitHub Actions daily reminder

## 1. Context
The goal is one LeetCode problem a day. The in-app evening reminder (v2, APScheduler + ntfy) only fires while the backend is running on the owner's PC.

v4 adds a **GitHub Actions scheduled workflow**. Every evening it runs on GitHub's servers, checks LeetCode for an accepted submission today (Chicago time), and sends an ntfy push if there isn't one. It works with the PC off, it's free, and it needs no database.

Later the tracker will be deployed on the owner's Raspberry Pi. When that happens, the owner picks **one** reminder (the Pi scheduler or this workflow) so they don't get two pushes. No Pi work in v4.

## 2. Ground rules
- Create branch `build/v4` from `build/v3`, and commit `PLAN_V4.md` first.
- **Never push**, and never create a remote. The repo has no remote yet; the owner will create the GitHub repo.
- Never access `/home/theo/dashboard`.
- **No paid services.** No real ntfy sends. A real LeetCode call is OK at most twice, for a manual run of the script with `--dry-run`.
- Small commits, imperative messages under 60 characters, each ending with a blank line then `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Before every commit, run `pytest`, `ruff check .`, `npm test -- --run` and `npm run lint`.
- Update the README and add one line to `LEARNING.md`.

## 3. Script: `backend/scripts/daily_check.py`
A standalone CLI. **Reuse the existing code. Don't copy it.**
- Use `services.leetcode_client.get_recent_accepted(username, limit=20)`.
- Convert the timestamps to local dates with the logic in `services/clock.py`.
- Send with `services/notify.send()`.

It must run with **no `.env` file and no database**, from environment variables only:
- `LEETCODE_USERNAME` (required)
- `TZ` (default `America/Chicago`)
- `NTFY_TOPIC` (required unless `--dry-run`)
- `NTFY_SERVER` (default `https://ntfy.sh`)

If importing `config.settings` forces a DB or other unneeded setup, restructure the smallest amount necessary and note it as a Deviation.

**Logic:**
1. Fetch recent accepted submissions. Done today = any submission whose local date equals today's local date.
2. If done: print "✅ solved today: <titles>", exit 0, send nothing.
3. If not done: work out the **current streak** from the recent-submission dates with `services/streaks.py`.
   - Note in a comment that this sees only the last 20 accepted submissions, so very long streaks are undercounted. That's fine for a reminder.
   - Send: title `LeetCode reminder`, message `No LeetCode yet today. 🔥 {n}-day streak at risk.`, or `No LeetCode yet today. Start a new streak!` when n = 0.
4. **Errors:**
   - If LeetCode fails: send a notification "Couldn't check LeetCode today. Solve one anyway!", then exit 1 so the workflow run shows red.
   - If ntfy fails: exit 1 with a clear message.
5. **Flags:**
   - `--dry-run` prints what it would send and never sends.
   - `--force` sends even if today is done. It's for testing the phone setup.

**Tests** (`tests/test_daily_check.py`), with respx mocks and the clock frozen through the existing clock helpers:
- done today → no send
- not done → send, with the streak in the message
- the streak is 0 → "Start a new streak!" message
- the timezone boundary: a solve at 11:30pm Chicago counts for that day
- a LeetCode error → fallback send + exit 1
- `--dry-run` never sends
- `--force` sends when done

## 4. Workflow: `.github/workflows/daily-reminder.yml`
```yaml
on:
  schedule:
    - cron: "30 1 * * *"   # 01:30 UTC = 8:30pm CDT / 7:30pm CST
    - cron: "30 3 * * *"   # 03:30 UTC = 10:30pm CDT / 9:30pm CST (last call)
  workflow_dispatch:
    inputs:
      force: {type: boolean, default: false, description: "Send even if already solved (test phone setup)"}
```
- **Steps:** checkout, then set up Python 3.12 with a pip cache, then install the backend requirements, then `cd backend && python scripts/daily_check.py` (add `--force` when the input is true).
- **Env:**
  - `LEETCODE_USERNAME: ${{ vars.LEETCODE_USERNAME }}`
  - `NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}`. It's a secret because anyone who knows an ntfy.sh topic can read it.
  - `TZ: ${{ vars.TZ || 'America/Chicago' }}`
- `permissions: contents: read`, `timeout-minutes: 5`, and `concurrency` so two runs can't overlap.
- **Comments** in the file must explain:
  - Cron is in UTC, so the local time shifts by an hour with daylight saving.
  - GitHub may start scheduled runs 5–30 minutes late.
  - GitHub **disables scheduled workflows after 60 days with no commits** in a public repo. The README must say how to re-enable it.

## 5. README section: "Daily reminder (GitHub Actions)"
The owner's setup steps:
1. Create a GitHub repo and push.
2. Settings → Secrets and variables → Actions:
   - add the secret `NTFY_TOPIC`
   - add the variable `LEETCODE_USERNAME=poke213`
   - optionally add the variable `TZ`
3. Actions tab → "Daily reminder" → Run workflow with `force` on, to test the phone.
4. Notes:
   - The 60-day rule.
   - Turn off the in-app scheduler (`ENABLE_SCHEDULER=false`) if you use this, so you don't get two reminders.
   - When the Pi deployment happens, choose one reminder.

## 6. Definition of done
- [ ] All checks pass, with counts reported.
- [ ] `python scripts/daily_check.py --dry-run` works with **only** environment variables (no `.env`), against real LeetCode for poke213. Report what it printed.
- [ ] The workflow YAML is valid. Check it with `actionlint` if it's installable through `pip` or `go`, or at least parse it with PyYAML. Report which.
- [ ] No sends, no pushes, no remote, and the dashboard untouched.

## 7. Final report
1. Definition-of-done checklist with ✅/❌.
2. Test counts.
3. The dry-run output.
4. The owner's exact setup steps.
5. Deviations.
6. Anything unfinished.
