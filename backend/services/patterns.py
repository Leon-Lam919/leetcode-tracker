"""Pattern checklists (e.g. NeetCode 150): seeding and progress."""

import json
from datetime import date
from pathlib import Path

from loguru import logger
from sqlalchemy import Engine
from sqlmodel import Session, select

from models.schemas import PatternGroup, PatternProblemOut
from models.tables import PatternList, PatternProblem, Problem, Review, Solve
from services.problems import problem_url

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"

# URL key -> (list name in the DB, seed file). Add a line here to add another list.
LISTS = {"neetcode150": ("NeetCode 150", "neetcode150.json")}


class UnknownListError(Exception):
    """The ?list= key isn't in LISTS."""


def seed_lists(engine: Engine) -> None:
    """Load each list from its JSON file, but only if that list has no rows yet.

    Safe to run on every startup: a second run finds the list and does nothing.
    """
    with Session(engine) as session:
        for name, filename in LISTS.values():
            if session.exec(select(PatternList).where(PatternList.name == name)).first():
                continue
            entries = json.loads((SEED_DIR / filename).read_text())
            pattern_list = PatternList(name=name)
            session.add(pattern_list)
            session.flush()  # assigns pattern_list.id
            for position, entry in enumerate(entries):
                session.add(PatternProblem(list_id=pattern_list.id, position=position, **entry))
            session.commit()
            logger.info("Seeded pattern list {!r} with {} problems", name, len(entries))


def solved_slugs(session: Session) -> set[str]:
    query = select(Problem.title_slug).where(Problem.id.in_(select(Solve.problem_id)))
    return set(session.exec(query))


def review_slugs(session: Session, today: date) -> set[str]:
    """Slugs flagged "needs review" on any solve, or due in the review queue."""
    flagged = select(Problem.title_slug).join(Solve).where(Solve.needs_review)
    due = (
        select(Problem.title_slug)
        .join(Review)
        .where(Review.next_review_date.is_not(None), Review.next_review_date <= today)
    )
    return set(session.exec(flagged)) | set(session.exec(due))


def get_progress(session: Session, list_key: str, today: date) -> list[PatternGroup]:
    """The list grouped by pattern, in list order, with what's solved."""
    if list_key not in LISTS:
        raise UnknownListError(f"Unknown list {list_key!r}. Try: {', '.join(LISTS)}")
    name = LISTS[list_key][0]

    rows = session.exec(
        select(PatternProblem)
        .join(PatternList)
        .where(PatternList.name == name)
        .order_by(PatternProblem.position)
    )
    solved = solved_slugs(session)
    to_review = review_slugs(session, today)

    groups: dict[str, PatternGroup] = {}  # dicts keep insertion order, so list order is kept
    for row in rows:
        group = groups.setdefault(
            row.pattern, PatternGroup(pattern=row.pattern, total=0, solved=0, problems=[])
        )
        is_solved = row.slug in solved
        group.total += 1
        group.solved += is_solved
        group.problems.append(
            PatternProblemOut(
                slug=row.slug,
                title=row.title,
                difficulty=row.difficulty,
                url=problem_url(row.slug),
                solved=is_solved,
                needs_review=row.slug in to_review,
            )
        )
    return list(groups.values())
