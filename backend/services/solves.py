"""Business logic for listing, adding, editing, and deleting solves."""

import json
from datetime import UTC, date

from sqlmodel import Session, select

from models.schemas import SolveCreate, SolveOut, SolveUpdate
from models.tables import Problem, Solve
from services.clock import today_local, utc_now
from services.problems import create_problem, find_problem


class DuplicateSolveError(Exception):
    """This problem already has a solve on that day."""


class MissingProblemInfoError(Exception):
    """We don't know the problem and weren't given enough info to create it."""


def to_solve_out(solve: Solve, problem: Problem) -> SolveOut:
    """Combine a solve and its problem into the shape the API returns."""
    return SolveOut(
        id=solve.id,
        title=problem.title,
        title_slug=problem.title_slug,
        difficulty=problem.difficulty,
        topics=json.loads(problem.topics),
        url=problem.url,
        # SQLite drops timezone info; we always store UTC, so put it back.
        solved_at=solve.solved_at.replace(tzinfo=UTC),
        solved_date=solve.solved_date,
        source=solve.source,
        time_spent_min=solve.time_spent_min,
        confidence=solve.confidence,
        notes=solve.notes,
        needs_review=solve.needs_review,
    )


def list_solves(
    session: Session,
    difficulty: str | None = None,
    topic: str | None = None,
    needs_review: bool | None = None,
) -> list[SolveOut]:
    """Return solves newest first, optionally filtered."""
    query = select(Solve, Problem).join(Problem)
    if difficulty:
        query = query.where(Problem.difficulty == difficulty)
    if needs_review is not None:
        query = query.where(Solve.needs_review == needs_review)
    query = query.order_by(Solve.solved_date.desc(), Solve.solved_at.desc(), Solve.id.desc())

    results = [to_solve_out(solve, problem) for solve, problem in session.exec(query)]

    # Topics are a JSON list in one column, so filtering them in Python is the simplest option.
    if topic:
        results = [solve for solve in results if topic in solve.topics]
    return results


def solve_exists(session: Session, problem_id: int, solved_date: date) -> bool:
    query = select(Solve).where(Solve.problem_id == problem_id, Solve.solved_date == solved_date)
    return session.exec(query).first() is not None


def get_or_create_problem_for_manual_add(session: Session, data: SolveCreate) -> Problem:
    problem = find_problem(session, data.title_slug)
    if problem:
        return problem

    if not (data.title and data.difficulty):
        raise MissingProblemInfoError(
            f"Unknown problem '{data.title_slug}'. Provide title and difficulty."
        )
    return create_problem(
        session, data.title_slug, data.title, data.difficulty, data.topics or []
    )


def create_manual_solve(session: Session, data: SolveCreate) -> SolveOut:
    problem = get_or_create_problem_for_manual_add(session, data)
    solved_date = data.solved_date or today_local()

    if solve_exists(session, problem.id, solved_date):
        session.rollback()
        raise DuplicateSolveError(f"'{problem.title}' is already logged for {solved_date}")

    solve = Solve(
        problem_id=problem.id,
        solved_at=utc_now(),
        solved_date=solved_date,
        source="manual",
        time_spent_min=data.time_spent_min,
        confidence=data.confidence,
        notes=data.notes or "",
        needs_review=bool(data.needs_review),
    )
    session.add(solve)
    session.commit()
    session.refresh(solve)
    return to_solve_out(solve, problem)


def update_solve(session: Session, solve_id: int, data: SolveUpdate) -> SolveOut | None:
    """Change only the fields the client sent. Returns None if the solve doesn't exist."""
    solve = session.get(Solve, solve_id)
    if solve is None:
        return None

    changes = data.model_dump(exclude_unset=True)
    if changes.get("notes") is None:
        changes.pop("notes", None)  # notes can't be null in the DB
    if changes.get("needs_review") is None:
        changes.pop("needs_review", None)
    for field, value in changes.items():
        setattr(solve, field, value)

    session.add(solve)
    session.commit()
    session.refresh(solve)
    return to_solve_out(solve, session.get(Problem, solve.problem_id))


def delete_solve(session: Session, solve_id: int) -> bool:
    """Delete a solve. Returns False if it didn't exist."""
    solve = session.get(Solve, solve_id)
    if solve is None:
        return False
    session.delete(solve)
    session.commit()
    return True
