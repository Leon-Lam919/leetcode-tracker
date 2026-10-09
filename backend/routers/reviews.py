from fastapi import APIRouter, HTTPException, Query

from db import SessionDep
from models.schemas import ReviewCreate, ReviewDayCount, ReviewDue, ReviewOut
from services import reviews
from services.clock import today_local

router = APIRouter()


@router.get("/reviews/due", response_model=list[ReviewDue])
def due(session: SessionDep):
    """Problems to review today (or overdue), most overdue first."""
    return reviews.due_reviews(session, today_local())


@router.get("/reviews/upcoming", response_model=list[ReviewDayCount])
def upcoming(session: SessionDep, days: int = Query(default=7, ge=1, le=60)):
    """How many reviews fall on each of the next `days` days."""
    return reviews.upcoming_counts(session, today_local(), days)


@router.post("/reviews/{problem_id}", response_model=ReviewOut)
def mark_reviewed(problem_id: int, data: ReviewCreate, session: SessionDep):
    """Mark a problem reviewed today (1 = again, 2 = good, 3 = easy), without a re-solve."""
    try:
        return reviews.record_review(session, problem_id, data.confidence, today_local())
    except reviews.NotInQueueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
