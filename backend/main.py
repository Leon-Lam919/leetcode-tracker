"""FastAPI entry point. Run with: uvicorn main:app --reload"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import settings
from db import create_db_and_tables
from routers.health import router as health_router
from routers.solves import router as solves_router
from routers.stats import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    if not settings.leetcode_username:
        logger.warning("LEETCODE_USERNAME is not set; /api/sync will fail until it is")
    logger.info("Using timezone {}, daily goal {}", settings.tz, settings.daily_goal)
    yield


app = FastAPI(title="LeetCode Tracker", lifespan=lifespan)

# In dev the Vite proxy makes this unnecessary; it is a fallback for calling the API directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(solves_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
