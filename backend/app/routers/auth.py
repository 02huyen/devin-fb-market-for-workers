import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..auth_utils import SESSION_COOKIE, SESSION_MAX_AGE, create_session_token, get_current_user
from ..database import get_db
from ..models import MagicLinkToken, User
from ..schemas import RequestLinkIn, RequestLinkOut, UserOut
from ..services.email_validation import EmailValidationError, validate_work_email

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
DEV_MODE = os.environ.get("APP_ENV", "dev") == "dev"
TOKEN_TTL_MINUTES = 15


@router.post("/request-link", response_model=RequestLinkOut)
async def request_link(payload: RequestLinkIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    try:
        domain, company_name = await validate_work_email(email)
    except EmailValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            domain=domain,
            company_name=company_name,
            display_name=email.split("@")[0].replace(".", " ").title(),
        )
        db.add(user)

    token = secrets.token_urlsafe(32)
    db.add(
        MagicLinkToken(
            token=token,
            email=email,
            expires_at=datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MINUTES),
        )
    )
    db.commit()

    magic_link = f"{FRONTEND_URL}/verify?token={token}"
    # Production: send magic_link via an email provider (Resend/SendGrid/SES).
    return RequestLinkOut(
        message="Check your work email for a sign-in link.",
        dev_magic_link=magic_link if DEV_MODE else None,
    )


@router.post("/verify", response_model=UserOut)
def verify(token: str, response: Response, db: Session = Depends(get_db)):
    record = (
        db.query(MagicLinkToken)
        .filter(MagicLinkToken.token == token, MagicLinkToken.used.is_(False))
        .first()
    )
    if not record or record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired link")

    user = db.query(User).filter(User.email == record.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Unknown user")

    record.used = True
    user.is_verified = True
    db.commit()
    db.refresh(user)

    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(user.id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"message": "Logged out"}
