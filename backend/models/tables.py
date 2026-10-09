"""Database tables.

A problem can be solved more than once (re-solving is good practice),
so problems and solves are separate tables.
"""

from datetime import date, datetime

from sqlmodel import Field, SQLModel, Text, UniqueConstraint


class Problem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title_slug: str = Field(unique=True, index=True)  # e.g. "two-sum"
    title: str
    difficulty: str  # "Easy" / "Medium" / "Hard"
    topics: str = "[]"  # JSON list, e.g. '["Array", "Hash Table"]'
    url: str


class Solve(SQLModel, table=True):
    # Solving the same problem twice on the same day counts as one solve.
    __table_args__ = (UniqueConstraint("problem_id", "solved_date"),)

    id: int | None = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.id", index=True)
    solved_at: datetime  # stored in UTC (SQLite drops the timezone, so it is naive UTC)
    solved_date: date = Field(index=True)  # local date in settings.tz, computed once at insert
    source: str  # "sync" or "manual"
    time_spent_min: int | None = None
    confidence: int | None = None  # 1 = needed help, 3 = solved cleanly
    notes: str = ""
    needs_review: bool = False
    # Solution fields (v2). Added to older databases by migrations.py.
    approach: str | None = Field(default=None, sa_type=Text)  # e.g. "hash map, one pass"
    code: str | None = Field(default=None, sa_type=Text)
    language: str | None = Field(default="python3", sa_column_kwargs={"server_default": "python3"})
    time_complexity: str | None = None  # e.g. "O(n)"
    space_complexity: str | None = None


class Review(SQLModel, table=True):
    """When to look at a problem again (spaced repetition). One row per problem, not per solve."""

    id: int | None = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.id", unique=True)
    interval_index: int = 0  # index into review_schedule.INTERVALS
    next_review_date: date | None = Field(default=None, index=True)  # local date; None = mastered
    last_reviewed_date: date
    last_confidence: int | None = None  # from the latest review or re-solve


class PatternList(SQLModel, table=True):
    """A named list of problems grouped by pattern, e.g. "NeetCode 150"."""

    __tablename__ = "pattern_list"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class PatternProblem(SQLModel, table=True):
    """One problem in a pattern list. Matched to solves by slug, not by a foreign key,
    because most listed problems haven't been solved (so aren't in `problem`) yet."""

    __tablename__ = "pattern_problem"
    __table_args__ = (UniqueConstraint("list_id", "slug"),)

    id: int | None = Field(default=None, primary_key=True)
    list_id: int = Field(foreign_key="pattern_list.id", index=True)
    slug: str
    title: str
    difficulty: str
    pattern: str  # e.g. "Two Pointers"
    position: int  # order within the whole list (NeetCode order)


class Meta(SQLModel, table=True):
    """Small key-value store for app state, e.g. when the last sync ran."""

    key: str = Field(primary_key=True)
    value: str
