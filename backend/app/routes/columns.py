"""Column endpoints — nested under a board."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Board, BoardColumn, User
from ..schemas import ColumnCreate, ColumnOut


router = APIRouter(prefix="/api", tags=["columns"])


def _owned_board(board_id: int, user: User, db: Session) -> Board:
    board = db.get(Board, board_id)
    if not board or board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="board not found")
    return board


def _owned_column(column_id: int, user: User, db: Session) -> BoardColumn:
    column = db.get(BoardColumn, column_id)
    if not column or column.board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="column not found")
    return column


@router.post(
    "/boards/{board_id}/columns",
    response_model=ColumnOut,
    status_code=status.HTTP_201_CREATED,
)
def create_column(
    board_id: int,
    payload: ColumnCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ColumnOut:
    board = _owned_board(board_id, user, db)
    next_position = db.execute(
        select(func.coalesce(func.max(BoardColumn.position), -1) + 1).where(
            BoardColumn.board_id == board.id
        )
    ).scalar_one()
    column = BoardColumn(name=payload.name, position=next_position, board_id=board.id)
    db.add(column)
    db.commit()
    db.refresh(column)
    return ColumnOut.model_validate(column)


@router.delete("/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column(
    column_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    column = _owned_column(column_id, user, db)
    db.delete(column)
    db.commit()
