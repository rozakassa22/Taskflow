"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


# ---------- Board / Column / Card ----------

class CardOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: str
    due_date: Optional[datetime]
    position: int
    column_id: int

    model_config = {"from_attributes": True}


class CardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    priority: str = "normal"
    due_date: Optional[datetime] = None


class CardUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


class CardMove(BaseModel):
    column_id: int
    position: int = Field(ge=0)


class ColumnOut(BaseModel):
    id: int
    name: str
    position: int
    board_id: int
    cards: List[CardOut] = []

    model_config = {"from_attributes": True}


class ColumnCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class BoardOut(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime
    columns: List[ColumnOut] = []

    model_config = {"from_attributes": True}


class BoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
