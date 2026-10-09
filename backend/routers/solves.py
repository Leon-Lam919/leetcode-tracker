from fastapi import APIRouter, HTTPException, Response, status

from db import SessionDep
from models.schemas import SolveCreate, SolveOut, SolveUpdate
from services import solves

router = APIRouter()


@router.get("/solves", response_model=list[SolveOut])
def list_solves(
    session: SessionDep,
    difficulty: str | None = None,
    topic: str | None = None,
    needs_review: bool | None = None,
):
    return solves.list_solves(session, difficulty, topic, needs_review)


@router.post("/solves", response_model=SolveOut, status_code=status.HTTP_201_CREATED)
def add_solve(data: SolveCreate, session: SessionDep):
    """Manually log a solve (for example, one older than the last 20 synced)."""
    try:
        return solves.create_manual_solve(session, data)
    except solves.DuplicateSolveError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except solves.MissingProblemInfoError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.patch("/solves/{solve_id}", response_model=SolveOut)
def edit_solve(solve_id: int, data: SolveUpdate, session: SessionDep):
    updated = solves.update_solve(session, solve_id, data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Solve not found")
    return updated


@router.delete("/solves/{solve_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_solve(solve_id: int, session: SessionDep):
    if not solves.delete_solve(session, solve_id):
        raise HTTPException(status_code=404, detail="Solve not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
