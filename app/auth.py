import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.models import Session as UserSession, User

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, password)
    except Exception:
        return False


def _get_session_expiry() -> datetime:
    settings = get_settings()
    return datetime.utcnow() + timedelta(minutes=settings.session_timeout_minutes)


def create_user_session(db: Session, user: User) -> UserSession:
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    session = UserSession(
        user_id=user.id,
        token=token,
        csrf_token=csrf_token,
        expires_at=_get_session_expiry(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def clear_auth_cookies(response):
    settings = get_settings()
    response.delete_cookie("session_token", path="/")
    response.delete_cookie("csrf_token", path="/")


def set_auth_cookies(response, session_token: str, csrf_token: str):
    settings = get_settings()
    expiry_seconds = settings.session_timeout_minutes * 60
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        max_age=expiry_seconds,
        path="/",
    )
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="lax",
        secure=settings.session_cookie_secure,
        max_age=expiry_seconds,
        path="/",
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Authentication required.")

    session = db.query(UserSession).filter(UserSession.token == session_token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")

    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired.")

    return session.user


def require_csrf(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
        return

    expected_token = request.headers.get("X-CSRF-Token")
    if not expected_token:
        raise HTTPException(status_code=403, detail="CSRF token missing.")

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Authentication required.")

    session = db.query(UserSession).filter(UserSession.token == session_token).first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session.")

    if expected_token != session.csrf_token:
        raise HTTPException(status_code=403, detail="Invalid CSRF token.")

    return current_user
