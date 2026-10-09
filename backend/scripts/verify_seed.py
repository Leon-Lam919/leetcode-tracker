"""Check every problem in seed/neetcode150.json against LeetCode.

Run from backend/:  python scripts/verify_seed.py

It asks LeetCode about each slug, one request per second (be polite to an
unofficial API), and reports slugs that don't exist plus titles or
difficulties that don't match. It doesn't change the JSON; fix it by hand.
If LeetCode starts failing several times in a row (blocked or down), it
stops early and reports what it managed to check.
"""

import json
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))  # so `services` can be imported when run as a script

from services.leetcode_client import LeetCodeError, get_question  # noqa: E402

SEED_FILE = BACKEND / "seed" / "neetcode150.json"
SECONDS_BETWEEN_REQUESTS = 1.0
MAX_FAILURES_IN_A_ROW = 3


def main() -> int:
    entries = json.loads(SEED_FILE.read_text())
    missing, mismatched = [], []
    checked = 0
    failures_in_a_row = 0

    for number, entry in enumerate(entries, start=1):
        slug = entry["slug"]
        try:
            info = get_question(slug)
        except LeetCodeError as error:
            if "not found" in str(error):
                missing.append(slug)
                print(f"[{number}/{len(entries)}] MISSING  {slug}")
                failures_in_a_row = 0
                checked += 1
            else:
                failures_in_a_row += 1
                print(f"[{number}/{len(entries)}] ERROR    {slug}: {error}")
                if failures_in_a_row >= MAX_FAILURES_IN_A_ROW:
                    print("LeetCode keeps failing; stopping early.")
                    break
        else:
            failures_in_a_row = 0
            checked += 1
            problems = []
            if info.difficulty != entry["difficulty"]:
                problems.append(f"difficulty {entry['difficulty']} -> {info.difficulty}")
            if info.title != entry["title"]:
                problems.append(f"title {entry['title']!r} -> {info.title!r}")
            status = "MISMATCH" if problems else "ok"
            if problems:
                mismatched.append((slug, problems))
            print(f"[{number}/{len(entries)}] {status:8} {slug} {'; '.join(problems)}")
        time.sleep(SECONDS_BETWEEN_REQUESTS)

    print()
    print(f"Checked {checked} of {len(entries)} slugs.")
    print(f"Missing slugs ({len(missing)}): {', '.join(missing) or 'none'}")
    print(f"Mismatches ({len(mismatched)}):")
    for slug, problems in mismatched:
        print(f"  {slug}: {'; '.join(problems)}")
    return 1 if missing or mismatched or checked < len(entries) else 0


if __name__ == "__main__":
    sys.exit(main())
