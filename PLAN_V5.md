# LeetCode Tracker v5: Discord reminders

## 1. Context
Reminders currently go out only through ntfy (v2 in-app scheduler and v4 GitHub Actions `daily_check.py`). The owner wants something that feels more like a text message: a **Discord message** from a webhook, which pings their phone like a DM. It's free.

Discord becomes a **second channel** alongside ntfy. Every reminder goes to **every configured channel**. If neither channel is configured, nothing is sent (same as today).

## 2. Ground rules
- Create branch `build/v5` from `master`, and commit `PLAN_V5.md` first.
- **Never push.** Never access `/home/theo/dashboard`.
- **No real sends** to ntfy or Discord. Tests mock all HTTP with `respx`.
- No paid services.
- Small commits, imperative messages under 60 characters, each ending with a blank line then `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Before every commit, run `pytest`, `ruff check .`, `npm test -- --run` and `npm run lint`.
- Update the README and add one LEARNING.md row.

## 3. Config
New settings in `config.py`, `.env.example` and the README config table:

| Variable | Default | Meaning |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | empty | Channel webhook URL. Empty means Discord is off. **Treat it as a secret:** anyone with the URL can post to the channel. Never log it. |
| `DISCORD_USER_ID` | empty | Optional numeric user ID. If set, the message starts with `<@ID>`, so Discord sends a real mention ping to the phone. |

Validation:
- A non-empty webhook URL must start with `https://discord.com/api/webhooks/` or `https://discordapp.com/api/webhooks/`. Otherwise fail at startup with a clear error that does **not** print the URL.
- `DISCORD_USER_ID`, when set, must be all digits.

## 4. `services/notify.py` refactor
- Keep the public API: `send(title, message) -> bool` and `NotifyError`. Callers (the scheduler, `routers/notify.py`, `scripts/daily_check.py`) shouldn't need changes beyond config.
- Internally, split it into `_send_ntfy(title, message)` and `_send_discord(title, message)`. `send()` calls every configured channel:
  - **None configured:** log and return `False`, the same as today.
  - **At least one succeeded:** return `True`. Log any channel that failed, by channel name and without URLs.
  - **All configured channels failed:** raise `NotifyError`, listing which channels failed.

**Discord request:**
- `POST {webhook}?wait=true` with JSON:
  ```json
  {"content": "<@ID> **{title}**\n{message}",
   "username": "LeetCode Tracker",
   "allowed_mentions": {"users": ["<ID>"]}}
  ```
  Drop the mention part when there is no user ID, and then send `"allowed_mentions": {"parse": []}` so nothing else can ping.
- Keep `content` under Discord's 2000-character limit by truncating.
- Success is any 2xx. On a **429**, wait `retry_after` seconds (from the JSON body, capped at 5s) and retry **once**.
- Timeout 10s, the same as ntfy.

**`routers/notify.py`:** the "nothing configured" 400 message becomes "Set NTFY_TOPIC or DISCORD_WEBHOOK_URL in .env".

## 5. GitHub Actions
- In `daily-reminder.yml`, add these to `env`:
  - `DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}`
  - `DISCORD_USER_ID: ${{ vars.DISCORD_USER_ID }}`
- `scripts/daily_check.py`:
  - `load_env()` reads both new variables the same way it reads the ntfy ones.
  - Its "missing config" check now requires **at least one** of `NTFY_TOPIC` / `DISCORD_WEBHOOK_URL` (unless `--dry-run`). Exit code 2 is unchanged.
  - The dry-run output lists which channels it would use, never the URL.

## 6. Tests
**Backend** (respx, no network):
- Discord only → POST body shape, with and without a user ID (check `allowed_mentions`)
- Both channels → both are called
- One channel fails → `True`, and the failure is logged
- Both fail → `NotifyError`
- 429 then success → one retry
- 429 twice → failure
- Content over 2000 characters gets truncated
- An invalid webhook URL fails config validation, and the error text doesn't contain the URL
- `daily_check`: Discord-only config is accepted, neither configured exits 2, and the dry run lists channels without the URL
- The `/api/notify/test` 400 message

Existing ntfy tests must still pass unchanged, or with minimal fixture updates.

## 7. README
Add a **"Discord"** subsection under Phone reminders:
1. In your Discord server: channel → ⚙️ Edit Channel → Integrations → Webhooks → New Webhook → Copy Webhook URL.
2. Add the GitHub secret `DISCORD_WEBHOOK_URL`.
   - Locally, put it in `.env`.
   - It's a secret, because anyone with the URL can post to the channel.
3. Optional, for a real phone ping:
   - Discord Settings → Advanced → Developer Mode on.
   - Right-click your name → Copy User ID.
   - Add the variable `DISCORD_USER_ID`.
4. Test it: Actions → Daily reminder → Run workflow with `force` on.

Note that both channels can be on together, and that the server's notification settings must allow mentions to reach the phone.

## 8. Definition of done
- [ ] All checks pass, with counts reported.
- [ ] `daily_check.py --dry-run` with only `LEETCODE_USERNAME` and a **fake** `DISCORD_WEBHOOK_URL` in the environment lists Discord as a channel and doesn't print the URL.
- [ ] No real sends, no pushes, and the dashboard untouched.

## 9. Final report
1. Definition-of-done checklist with ✅/❌.
2. Test counts.
3. The owner's setup steps.
4. Deviations.
5. Anything unfinished.
