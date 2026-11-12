from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.auth import clear_auth_cookies, create_user_session, get_current_user, hash_password, require_csrf, set_auth_cookies, verify_password
from app.database import get_db
from app.models.models import Session as UserSession, User
from app.schemas.schemas import LoginRequest, RegisterRequest, UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register_user(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing_email = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    existing_username = db.query(User).filter(User.username == payload.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="This username is already in use.")

    user = User(
        username=payload.username.strip(),
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    session = create_user_session(db, user)
    set_auth_cookies(response, session.token, session.csrf_token)
    return {"message": "Registration successful.", "user": UserRead.model_validate(user).model_dump(mode="json")}


@router.post("/login")
def login_user(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    session = db.query(UserSession).filter(UserSession.user_id == user.id).first()
    if session:
        db.delete(session)
        db.commit()

    active_session = create_user_session(db, user)
    set_auth_cookies(response, active_session.token, active_session.csrf_token)
    return {"message": "Login successful.", "user": UserRead.model_validate(user).model_dump(mode="json")}


@router.post("/logout")
def logout_user(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    _user: User = Depends(require_csrf),
):
    session_token = request.cookies.get("session_token")
    if session_token:
        row = db.query(UserSession).filter(UserSession.token == session_token).first()
        if row:
            db.delete(row)
            db.commit()
    clear_auth_cookies(response)
    return {"message": "Logged out successfully."}


@router.get("/me")
def get_current_account(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user).model_dump(mode="json")


@router.get("/csrf")
def get_csrf_token(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    token = request.cookies.get("session_token")
    session = db.query(UserSession).filter(UserSession.token == token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Session invalid.")
    return {"csrf_token": session.csrf_token}
