"""Request and response shapes for the API (not database tables)."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class SolveOut(BaseModel):
    id: int
    title: str
    title_slug: str
    difficulty: str
    topics: list[str]
    url: str
    solved_at: datetime
    solved_date: date
    source: str
    time_spent_min: int | None
    confidence: int | None
    notes: str
    needs_review: bool


class NoteFields(BaseModel):
    """The fields a person writes about a solve. Shared by create and update."""

    time_spent_min: int | None = Field(default=None, ge=0)
    confidence: int | None = Field(default=None, ge=1, le=3)
    notes: str | None = None
    needs_review: bool | None = None


class SolveCreate(NoteFields):
    title_slug: str = Field(min_length=1)
    solved_date: date | None = None  # defaults to today (local)
    # Used only if the problem isn't in the DB and the LeetCode lookup fails.
    title: str | None = None
    difficulty: str | None = None
    topics: list[str] | None = None


class SolveUpdate(NoteFields):
    pass


class HeatmapDay(BaseModel):
    date: date
    count: int


class Stats(BaseModel):
    today_done: bool
    today_count: int
    daily_goal: int
    current_streak: int
    longest_streak: int
    total_solved: int
    by_difficulty: dict[str, int]
    by_topic: dict[str, int]
