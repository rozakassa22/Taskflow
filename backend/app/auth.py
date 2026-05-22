"""Authentication helpers: password hashing, JWT issuance and verification."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expires_minutes
    )
    payload = {"sub": subject, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="malformed token")
    return subject


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    subject = _decode_token(token)
    try:
        user_id = int(subject)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="malformed token subject") from exc
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="user not found")
    return user
