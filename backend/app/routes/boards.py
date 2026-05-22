"""Board CRUD endpoints. New boards get three default columns."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Board, BoardColumn, User
from ..schemas import BoardCreate, BoardOut


router = APIRouter(prefix="/api/boards", tags=["boards"])

DEFAULT_COLUMNS = ["Todo", "Doing", "Done"]


def _get_owned_board(board_id: int, user: User, db: Session) -> Board:
    board = db.get(Board, board_id)
    if not board or board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="board not found")
    return board


@router.get("", response_model=List[BoardOut])
def list_boards(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> List[BoardOut]:
    rows = db.execute(
        select(Board).where(Board.owner_id == user.id).order_by(Board.created_at)
    ).scalars().all()
    return [BoardOut.model_validate(b) for b in rows]


@router.post("", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
def create_board(
    payload: BoardCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BoardOut:
    board = Board(name=payload.name, owner_id=user.id)
    db.add(board)
    db.flush()  # assigns board.id without committing
    for i, name in enumerate(DEFAULT_COLUMNS):
        db.add(BoardColumn(name=name, position=i, board_id=board.id))
    db.commit()
    db.refresh(board)
    return BoardOut.model_validate(board)


@router.get("/{board_id}", response_model=BoardOut)
def get_board(
    board_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BoardOut:
    return BoardOut.model_validate(_get_owned_board(board_id, user, db))


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    board = _get_owned_board(board_id, user, db)
    db.delete(board)
    db.commit()
