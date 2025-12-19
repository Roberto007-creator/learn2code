from fastapi import APIRouter, Depends, HTTPException, Response, Form
from sqlalchemy.orm import Session
from sqlalchemy import select
from api.deps import get_db
from app.schemas.auth import RegisterIn, TokenOut
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=400, detail="Email already used")
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=400, detail="Username already used")

    user = User(email=payload.email, username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(sub=str(user.id))
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut)
def login(response: Response, db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    user = db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(sub=str(user.id))
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return TokenOut(access_token=token)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}
