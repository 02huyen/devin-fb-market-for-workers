"""Magic-link email delivery.

Tries Resend first (RESEND_API_KEY), then SendGrid (SENDGRID_API_KEY). If
neither is configured, the caller falls back to dev-mode inline links.
EMAIL_FROM must be a verified sender for the chosen provider.
"""

import logging
import os
from email.utils import parseaddr

import httpx

logger = logging.getLogger(__name__)

EMAIL_FROM = os.environ.get("EMAIL_FROM", "Workplace Market <onboarding@resend.dev>")


HTML_TEMPLATE = (
    "<p>Click the link below to sign in to Workplace Market. "
    "It expires in 15 minutes.</p>"
    '<p><a href="{magic_link}">Sign in to Workplace Market</a></p>'
    "<p>If you did not request this, you can ignore this email.</p>"
)


def _from_name_and_email() -> tuple[str, str]:
    name, email = parseaddr(EMAIL_FROM)
    if not email:
        email = EMAIL_FROM
    return name, email


async def _send_via_resend(api_key: str, to_email: str, magic_link: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "from": EMAIL_FROM,
                    "to": [to_email],
                    "subject": "Your Workplace Market sign-in link",
                    "html": HTML_TEMPLATE.format(magic_link=magic_link),
                },
            )
        if resp.status_code in (200, 201):
            return True
        logger.warning("Resend send failed (%s): %s", resp.status_code, resp.text)
    except httpx.HTTPError as e:
        logger.warning("Resend send failed: %s", e)
    return False


async def _send_via_sendgrid(api_key: str, to_email: str, magic_link: str) -> bool:
    name, email = _from_name_and_email()
    payload: dict = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": email},
        "subject": "Your Workplace Market sign-in link",
        "content": [{"type": "text/html", "value": HTML_TEMPLATE.format(magic_link=magic_link)}],
    }
    if name:
        payload["from"]["name"] = name
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if resp.status_code in (200, 202):
            return True
        logger.warning("SendGrid send failed (%s): %s", resp.status_code, resp.text)
    except httpx.HTTPError as e:
        logger.warning("SendGrid send failed: %s", e)
    return False


async def send_magic_link_email(to_email: str, magic_link: str) -> bool:
    """Send the sign-in link. Returns True if the email was sent."""
    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key and await _send_via_resend(resend_key, to_email, magic_link):
        return True

    sendgrid_key = os.environ.get("SENDGRID_API_KEY")
    if sendgrid_key and await _send_via_sendgrid(sendgrid_key, to_email, magic_link):
        return True

    return False
