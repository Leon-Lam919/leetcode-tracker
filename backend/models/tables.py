"""Database tables.

A problem can be solved more than once (re-solving is good practice),
so problems and solves are separate tables.
"""

from datetime import date, datetime

from sqlmodel import Field, SQLModel, UniqueConstraint


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
