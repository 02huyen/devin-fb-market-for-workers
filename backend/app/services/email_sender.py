"""Magic-link email delivery via Resend.

Sends only when RESEND_API_KEY is set; otherwise the caller falls back to
dev-mode inline links. EMAIL_FROM must be a verified Resend sender —
"onboarding@resend.dev" works for testing but only delivers to the Resend
account owner's email.
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

EMAIL_FROM = os.environ.get("EMAIL_FROM", "Workplace Market <onboarding@resend.dev>")


async def send_magic_link_email(to_email: str, magic_link: str) -> bool:
    """Send the sign-in link. Returns True if the email was sent."""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "from": EMAIL_FROM,
                    "to": [to_email],
                    "subject": "Your Workplace Market sign-in link",
                    "html": (
                        "<p>Click the link below to sign in to Workplace Market. "
                        "It expires in 15 minutes.</p>"
                        f'<p><a href="{magic_link}">Sign in to Workplace Market</a></p>'
                        "<p>If you did not request this, you can ignore this email.</p>"
                    ),
                },
            )
        if resp.status_code in (200, 201):
            return True
        logger.warning("Resend send failed (%s): %s", resp.status_code, resp.text)
    except httpx.HTTPError as e:
        logger.warning("Resend send failed: %s", e)
    return False
