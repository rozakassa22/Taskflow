"""Card endpoints: create, update, delete, and move (reorder/cross-column)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import BoardColumn, Card, User
from ..schemas import CardCreate, CardMove, CardOut, CardUpdate


router = APIRouter(prefix="/api", tags=["cards"])


def _owned_column(column_id: int, user: User, db: Session) -> BoardColumn:
    column = db.get(BoardColumn, column_id)
    if not column or column.board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="column not found")
    return column


def _owned_card(card_id: int, user: User, db: Session) -> Card:
    card = db.get(Card, card_id)
    if not card or card.column.board.owner_id != user.id:
        raise HTTPException(status_code=404, detail="card not found")
    return card


@router.post(
    "/columns/{column_id}/cards",
    response_model=CardOut,
    status_code=status.HTTP_201_CREATED,
)
def create_card(
    column_id: int,
    payload: CardCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CardOut:
    column = _owned_column(column_id, user, db)
    next_position = db.execute(
        select(func.coalesce(func.max(Card.position), -1) + 1).where(
            Card.column_id == column.id
        )
    ).scalar_one()
    card = Card(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        position=next_position,
        column_id=column.id,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return CardOut.model_validate(card)


@router.patch("/cards/{card_id}", response_model=CardOut)
def update_card(
    card_id: int,
    payload: CardUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CardOut:
    card = _owned_card(card_id, user, db)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(card, key, value)
    db.commit()
    db.refresh(card)
    return CardOut.model_validate(card)


@router.patch("/cards/{card_id}/move", response_model=CardOut)
def move_card(
    card_id: int,
    payload: CardMove,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CardOut:
    card = _owned_card(card_id, user, db)
    target = _owned_column(payload.column_id, user, db)

    old_column_id = card.column_id
    old_position = card.position
    new_column_id = target.id
    new_position = payload.position

    # Close the gap in the old column (only if moving across columns or up within the same).
    if old_column_id != new_column_id:
        db.execute(
            update(Card)
            .where(Card.column_id == old_column_id, Card.position > old_position)
            .values(position=Card.position - 1)
        )
        # Open a slot in the new column at the target position.
        db.execute(
            update(Card)
            .where(Card.column_id == new_column_id, Card.position >= new_position)
            .values(position=Card.position + 1)
        )
    else:
        if new_position < old_position:
            db.execute(
                update(Card)
                .where(
                    Card.column_id == old_column_id,
                    Card.position >= new_position,
                    Card.position < old_position,
                )
                .values(position=Card.position + 1)
            )
        elif new_position > old_position:
            db.execute(
                update(Card)
                .where(
                    Card.column_id == old_column_id,
                    Card.position > old_position,
                    Card.position <= new_position,
                )
                .values(position=Card.position - 1)
            )

    card.column_id = new_column_id
    card.position = new_position
    db.commit()
    db.refresh(card)
    return CardOut.model_validate(card)


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    card = _owned_card(card_id, user, db)
    column_id = card.column_id
    position = card.position
    db.delete(card)
    # Close the gap left by the removed card.
    db.execute(
        update(Card)
        .where(Card.column_id == column_id, Card.position > position)
        .values(position=Card.position - 1)
    )
    db.commit()
