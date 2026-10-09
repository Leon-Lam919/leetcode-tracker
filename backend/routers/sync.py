from fastapi import APIRouter, HTTPException

from config import settings
from db import SessionDep
from services.leetcode_client import LeetCodeError
from services.sync import sync_recent

router = APIRouter()


@router.post("/sync")
def sync(session: SessionDep):
    """Fetch the last 20 accepted submissions and add any new solves."""
    if not settings.leetcode_username:
        raise HTTPException(status_code=400, detail="LEETCODE_USERNAME is not set in .env")
    try:
        result = sync_recent(session, settings.leetcode_username)
    except LeetCodeError as error:
        session.rollback()
        raise HTTPException(status_code=502, detail=f"LeetCode sync failed: {error}") from error
    return {"added": result.added, "skipped": result.skipped}
