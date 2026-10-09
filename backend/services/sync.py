"""Pull recent accepted submissions from LeetCode into the database."""

from dataclasses import dataclass

from sqlmodel import Session

from models.tables import Problem, Solve
from services import leetcode_client
from services.clock import to_local_date
from services.problems import create_problem, find_problem
from services.solves import solve_exists

RECENT_LIMIT = 20


@dataclass
class SyncResult:
    added: int
    skipped: int


def get_or_create_problem(session: Session, slug: str) -> Problem:
    """Use the problem from the DB if we have it; otherwise ask LeetCode for its details."""
    problem = find_problem(session, slug)
    if problem:
        return problem

    info = leetcode_client.get_question(slug)
    return create_problem(session, info.title_slug, info.title, info.difficulty, info.topics)


def sync_recent(session: Session, username: str) -> SyncResult:
    """Add new solves from LeetCode. Safe to run any number of times.

    A solve is skipped if that problem already has a solve on that local date,
    so a second run adds nothing, and notes on existing solves are never touched.
    """
    submissions = leetcode_client.get_recent_accepted(username, limit=RECENT_LIMIT)

    added = 0
    skipped = 0
    for submission in submissions:
        problem = get_or_create_problem(session, submission.title_slug)
        solved_date = to_local_date(submission.solved_at)

        if solve_exists(session, problem.id, solved_date):
            skipped += 1
            continue

        session.add(
            Solve(
                problem_id=problem.id,
                solved_at=submission.solved_at,
                solved_date=solved_date,
                source="sync",
            )
        )
        session.flush()  # so the next solve_exists() check sees this row
        added += 1

    # Commit once at the end: if LeetCode fails halfway, nothing is half-saved.
    session.commit()
    return SyncResult(added=added, skipped=skipped)
