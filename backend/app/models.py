"""SQLAlchemy ORM models: User, Board, Column, Card."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    boards: Mapped[List["Board"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="boards")
    columns: Mapped[List["BoardColumn"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="BoardColumn.position",
    )


class BoardColumn(Base):
    __tablename__ = "columns"
    __table_args__ = (UniqueConstraint("board_id", "position", name="uq_column_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))

    board: Mapped[Board] = relationship(back_populates="columns")
    cards: Mapped[List["Card"]] = relationship(
        back_populates="column",
        cascade="all, delete-orphan",
        order_by="Card.position",
    )


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(10), default="normal")  # low|normal|high
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    position: Mapped[int] = mapped_column(Integer)
    column_id: Mapped[int] = mapped_column(ForeignKey("columns.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    column: Mapped[BoardColumn] = relationship(back_populates="cards")
