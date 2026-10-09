"""The review queue: database side of spaced repetition.

The scheduling rules live in review_schedule.py (pure). This file reads and
writes the `review` table and reacts to new solves.
"""

from collections import Counter
from datetime import date, timedelta

from sqlmodel import Session, func, select

from models.schemas import ReviewDayCount, ReviewDue, ReviewOut
from models.tables import Problem, Review, Solve
from services.review_schedule import next_state


class NotInQueueError(Exception):
    """The problem has no review row (it has never been solved)."""


def find_review(session: Session, problem_id: int) -> Review | None:
    return session.exec(select(Review).where(Review.problem_id == problem_id)).first()


def to_review_out(review: Review) -> ReviewOut:
    return ReviewOut(
        problem_id=review.problem_id,
        interval_index=review.interval_index,
        next_review_date=review.next_review_date,
        last_reviewed_date=review.last_reviewed_date,
        last_confidence=review.last_confidence,
    )


def on_solve_added(
    session: Session, problem_id: int, solved_date: date, confidence: int | None
) -> None:
    """Update the schedule after a new solve is saved (sync or manual add).

    - First solve of a problem: start the schedule; review it the next day.
    - A later re-solve counts as a review (confidence None counts as "good").
    - A solve dated on or before the last review (e.g. an old one added by hand)
      doesn't change anything.
    Doesn't commit; the caller saves the solve and the review together.
    """
    review = find_review(session, problem_id)
    if review is None:
        session.add(
            Review(
                problem_id=problem_id,
                interval_index=0,
                next_review_date=solved_date + timedelta(days=1),
                last_reviewed_date=solved_date,
                last_confidence=confidence,
            )
        )
        return

    if solved_date <= review.last_reviewed_date:
        return
    apply_review(review, confidence, solved_date)
    session.add(review)


def apply_review(review: Review, confidence: int | None, day: date) -> None:
    review.interval_index, review.next_review_date = next_state(
        review.interval_index, confidence, day
    )
    review.last_reviewed_date = day
    review.last_confidence = confidence


def record_review(session: Session, problem_id: int, confidence: int, today: date) -> ReviewOut:
    """Mark a problem reviewed today without re-solving it."""
    review = find_review(session, problem_id)
    if review is None:
        raise NotInQueueError(f"Problem {problem_id} isn't in the review queue")
    apply_review(review, confidence, today)
    session.add(review)
    session.commit()
    session.refresh(review)
    return to_review_out(review)


def remove_if_unsolved(session: Session, problem_id: int) -> None:
    """After a solve is deleted: drop the review if the problem has no solves left."""
    remaining = session.exec(select(func.count()).where(Solve.problem_id == problem_id)).one()
    review = find_review(session, problem_id)
    if remaining == 0 and review is not None:
        session.delete(review)


def latest_approach(session: Session, problem_id: int) -> str | None:
    query = (
        select(Solve.approach)
        .where(Solve.problem_id == problem_id, Solve.approach.is_not(None), Solve.approach != "")
        .order_by(Solve.solved_date.desc())
    )
    return session.exec(query).first()


def due_reviews(session: Session, today: date) -> list[ReviewDue]:
    """Problems due on or before `today`, most overdue first."""
    query = (
        select(Review, Problem)
        .join(Problem)
        .where(Review.next_review_date.is_not(None), Review.next_review_date <= today)
        .order_by(Review.next_review_date, Problem.title)
    )
    return [
        ReviewDue(
            problem_id=problem.id,
            title=problem.title,
            title_slug=problem.title_slug,
            difficulty=problem.difficulty,
            url=problem.url,
            next_review_date=review.next_review_date,
            days_overdue=(today - review.next_review_date).days,
            last_confidence=review.last_confidence,
            approach=latest_approach(session, problem.id),
        )
        for review, problem in session.exec(query)
    ]


def count_due(session: Session, today: date) -> int:
    query = select(func.count()).where(
        Review.next_review_date.is_not(None), Review.next_review_date <= today
    )
    return session.exec(query).one()


def upcoming_counts(session: Session, today: date, days: int) -> list[ReviewDayCount]:
    """How many reviews fall on each of the next `days` days (tomorrow onwards).

    Today and anything overdue are in due_reviews() instead.
    """
    end = today + timedelta(days=days)
    dates = session.exec(
        select(Review.next_review_date).where(
            Review.next_review_date > today, Review.next_review_date <= end
        )
    )
    counts = Counter(dates)
    upcoming = []
    for offset in range(1, days + 1):
        day = today + timedelta(days=offset)
        upcoming.append(ReviewDayCount(date=day, count=counts[day]))
    return upcoming
