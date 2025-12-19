from fastapi import Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import SessionLocal
from app.core.security import decode_token
from app.db.models import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), access_token: str | None = Cookie(default=None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sub = decode_token(access_token)
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.scalar(select(User).where(User.id == int(sub)))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
