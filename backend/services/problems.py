"""Finding and creating rows in the problem table."""

import json

from sqlmodel import Session, select

from models.tables import Problem


def problem_url(slug: str) -> str:
    return f"https://leetcode.com/problems/{slug}/"


def find_problem(session: Session, slug: str) -> Problem | None:
    return session.exec(select(Problem).where(Problem.title_slug == slug)).first()


def create_problem(
    session: Session, slug: str, title: str, difficulty: str, topics: list[str]
) -> Problem:
    problem = Problem(
        title_slug=slug,
        title=title,
        difficulty=difficulty,
        topics=json.dumps(topics),
        url=problem_url(slug),
    )
    session.add(problem)
    session.flush()  # assigns problem.id without committing yet
    return problem
