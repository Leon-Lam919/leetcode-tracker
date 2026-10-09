from fastapi import APIRouter, Query

from db import SessionDep
from models.schemas import HeatmapDay, Stats
from services.clock import today_local
from services.stats import get_heatmap, get_stats

router = APIRouter()


@router.get("/stats", response_model=Stats)
def stats(session: SessionDep):
    return get_stats(session, today_local())


@router.get("/heatmap", response_model=list[HeatmapDay])
def heatmap(session: SessionDep, days: int = Query(default=90, ge=1, le=366)):
    return get_heatmap(session, today_local(), days)
