"""Daily reminder check, run by the GitHub Actions workflow (.github/workflows/daily-reminder.yml).

Run from backend/:  python scripts/daily_check.py [--dry-run] [--force]

It asks LeetCode whether you have an accepted submission today (in TZ) and,
if not, sends a reminder through ntfy and/or Discord. No database and no .env
file: everything comes from environment variables, so it runs on a fresh GitHub runner.

    LEETCODE_USERNAME    required
    TZ                   default America/Chicago
    NTFY_TOPIC           at least one of these two is required unless --dry-run
    DISCORD_WEBHOOK_URL  (a secret: the URL is never printed)
    NTFY_SERVER          default https://ntfy.sh
    DISCORD_USER_ID      optional, digits only: @mention this user for a phone ping

Exit codes: 0 = all good, 1 = LeetCode or every channel failed, 2 = bad configuration.
"""

import argparse
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))  # so `services` can be imported when run as a script

from config import DISCORD_WEBHOOK_PREFIXES, settings  # noqa: E402
from services import notify  # noqa: E402
from services.clock import to_local_date, today_local  # noqa: E402
from services.leetcode_client import LeetCodeError, get_recent_accepted  # noqa: E402
from services.streaks import current_streak  # noqa: E402

DEFAULT_TZ = "America/Chicago"
DEFAULT_NTFY_SERVER = "https://ntfy.sh"
TITLE = "LeetCode reminder"
LEETCODE_DOWN_MESSAGE = "Couldn't check LeetCode today. Solve one anyway!"


class ConfigError(Exception):
    """A required environment variable is missing or invalid."""


def load_env(dry_run: bool) -> str:
    """Copy the env vars onto the shared settings object and return the username.

    `settings` also reads the repo-root .env file. Setting every field the
    script uses straight from os.environ means a local .env can't change what
    the script does: it behaves the same on a laptop as on a GitHub runner.
    """
    username = os.environ.get("LEETCODE_USERNAME", "").strip()
    if not username:
        raise ConfigError("LEETCODE_USERNAME is not set")

    tz = os.environ.get("TZ", "").strip() or DEFAULT_TZ
    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ConfigError(f"TZ={tz!r} is not a valid IANA timezone") from error

    topic = os.environ.get("NTFY_TOPIC", "").strip()
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not topic and not webhook and not dry_run:
        raise ConfigError(
            "NTFY_TOPIC and DISCORD_WEBHOOK_URL are both unset; set at least one "
            "(use --dry-run to test without them)"
        )
    if webhook and not webhook.startswith(DISCORD_WEBHOOK_PREFIXES):
        # Never echo the URL: it's a secret.
        raise ConfigError("DISCORD_WEBHOOK_URL must start with https://discord.com/api/webhooks/")
    user_id = os.environ.get("DISCORD_USER_ID", "").strip()
    if user_id and not user_id.isdigit():
        raise ConfigError("DISCORD_USER_ID must be digits only")

    settings.tz = tz
    settings.ntfy_topic = topic
    settings.discord_webhook_url = webhook
    settings.discord_user_id = user_id
    settings.ntfy_server = os.environ.get("NTFY_SERVER", "").strip() or DEFAULT_NTFY_SERVER
    return username


def deliver(message: str, dry_run: bool) -> None:
    """Send the push, or just print it with --dry-run. Raises NotifyError."""
    if dry_run:
        channels = ", ".join(notify.configured_channels()) or "none configured"
        print(f"[dry-run] channels: {channels}")
        print(f"[dry-run] would send: {TITLE!r}: {message}")
        return
    notify.send(TITLE, message)
    print(f"Sent: {message}")


def reminder_message(streak: int) -> str:
    if streak > 0:
        return f"No LeetCode yet today. 🔥 {streak}-day streak at risk."
    return "No LeetCode yet today. Start a new streak!"


def run(username: str, dry_run: bool, force: bool) -> int:
    try:
        submissions = get_recent_accepted(username, limit=20)
    except LeetCodeError as error:
        print(f"❌ LeetCode check failed: {error}", file=sys.stderr)
        deliver(LEETCODE_DOWN_MESSAGE, dry_run)
        return 1  # red run in the Actions tab, even though the fallback push went out

    today = today_local()
    solve_dates = [to_local_date(s.solved_at) for s in submissions]
    # Only the last 20 accepted submissions are visible here, so a very long streak
    # is undercounted. That's fine for a reminder; the app has the full history.
    streak = current_streak(solve_dates, today)
    pairs = zip(submissions, solve_dates, strict=True)
    solved_today = [s.title for s, day in pairs if day == today]

    if solved_today:
        print(f"✅ solved today: {', '.join(dict.fromkeys(solved_today))}")
        if not force:
            return 0
        deliver(f"Test push (--force): already solved today, {streak}-day streak.", dry_run)
        return 0

    deliver(reminder_message(streak), dry_run)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="print, never send")
    parser.add_argument("--force", action="store_true", help="send even if today is done")
    args = parser.parse_args(argv)

    try:
        username = load_env(args.dry_run)
    except ConfigError as error:
        print(f"❌ {error}", file=sys.stderr)
        return 2

    try:
        return run(username, args.dry_run, args.force)
    except notify.NotifyError as error:
        print(f"❌ Notification failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
