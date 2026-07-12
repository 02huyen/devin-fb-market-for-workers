import os
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..auth_utils import (
    SESSION_COOKIE,
    SESSION_MAX_AGE,
    create_session_token,
    get_current_user,
    session_cookie_attributes,
)
from ..database import get_db
from ..models import MagicLinkToken, User
from ..schemas import RequestLinkIn, RequestLinkOut, UserOut, UserUpdate
from ..services.email_sender import send_magic_link_email
from ..services.email_validation import EmailValidationError, validate_work_email
from ..services.rate_limiter import rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
DEV_MODE = os.environ.get("APP_ENV", "dev") == "dev"
TOKEN_TTL_MINUTES = 15

# Rate limits for /auth/request-link.
RATE_LIMIT_EMAIL_LIMIT = 5
RATE_LIMIT_EMAIL_WINDOW = 15 * 60  # 15 minutes
RATE_LIMIT_IP_LIMIT = 20
RATE_LIMIT_IP_WINDOW = 15 * 60  # 15 minutes


def _get_client_ip(request: Request) -> str:
    """Best-effort client IP for rate limiting.

    Honors X-Forwarded-For and X-Real-IP headers (useful when behind a reverse
    proxy) and falls back to the transport-level client host. Spoofing is still
    possible if the app is not behind a proxy, so the IP limit is a best-effort
    throttle rather than a security guarantee.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # The first address in the chain is the original client when proxies
        # append addresses. The header may be client-provided if no proxy is
        # present, which is acceptable for basic rate limiting.
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/request-link", response_model=RequestLinkOut)
async def request_link(
    payload: RequestLinkIn,
    request: Request,
    db: Session = Depends(get_db),
):
    email = payload.email.lower()
    ip = _get_client_ip(request)

    if not await rate_limiter.is_allowed(
        f"request-link:ip:{ip}", RATE_LIMIT_IP_LIMIT, RATE_LIMIT_IP_WINDOW
    ):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    if not await rate_limiter.is_allowed(
        f"request-link:email:{email}", RATE_LIMIT_EMAIL_LIMIT, RATE_LIMIT_EMAIL_WINDOW
    ):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

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
    elif company_name and not user.company_name:
        # If the user record predates company enrichment, backfill the verified name.
        user.company_name = company_name

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
    sent = await send_magic_link_email(email, magic_link)
    if not sent and not DEV_MODE:
        raise HTTPException(status_code=502, detail="Could not send sign-in email. Please try again.")
    return RequestLinkOut(
        message="Check your work email for a sign-in link."
        if sent
        else "Dev mode: use the link below to sign in.",
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
        **session_cookie_attributes(),
    )
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.display_name = payload.display_name.strip()
    db.commit()
    db.refresh(user)
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, **session_cookie_attributes())
    return {"message": "Logged out"}
