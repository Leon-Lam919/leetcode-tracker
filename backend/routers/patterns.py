from fastapi import APIRouter, HTTPException, Query

from db import SessionDep
from models.schemas import PatternGroup
from services import patterns
from services.clock import today_local

router = APIRouter()


@router.get("/patterns", response_model=list[PatternGroup])
def pattern_progress(session: SessionDep, list_key: str = Query("neetcode150", alias="list")):
    """Progress through a pattern list, grouped by pattern in list order."""
    try:
        return patterns.get_progress(session, list_key, today_local())
    except patterns.UnknownListError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
