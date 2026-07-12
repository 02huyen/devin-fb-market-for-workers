import os

from fastapi import Depends, HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

SECRET_KEY = os.environ.get("APP_SECRET_KEY", "dev-secret-change-in-production")
SESSION_COOKIE = "wm_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="wm-session")


def create_session_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def session_cookie_attributes() -> dict[str, bool | str]:
    """Return the cookie flags used for both set_cookie and delete_cookie.

    In production we set Secure=True and SameSite=None. SameSite=None requires
    Secure and lets a cross-origin SPA send credentials with fetch(). In dev
    we keep Secure=False and SameSite=Lax so http://localhost flows work.
    Operators can override with SESSION_COOKIE_SAMESITE.
    """
    secure = os.environ.get("APP_ENV") == "production"
    default_samesite = "none" if secure else "lax"
    samesite = os.environ.get("SESSION_COOKIE_SAMESITE", default_samesite)
    return {
        "httponly": True,
        "secure": secure,
        "samesite": samesite,
    }


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = db.get(User, data["user_id"])
    if not user or not user.is_verified:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
