"""Work-email validation.

Strategy (layered):
1. Syntax check (pydantic EmailStr upstream).
2. Reject known free/disposable email providers via a domain blocklist.
3. Verify the domain has MX records (i.e. it can actually receive mail).
4. (Optional, production) Call a third-party enrichment/verification API
   to confirm the domain belongs to a real company and fetch its name.
   Hunter.io (HUNTER_API_KEY) is preferred; Abstract API
   (EMAIL_VERIFY_API_KEY) is supported as an alternative.
"""

import os

import dns.resolver
import httpx

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.co.uk", "hotmail.com", "outlook.com",
    "live.com", "msn.com", "aol.com", "icloud.com", "me.com", "mac.com",
    "protonmail.com", "proton.me", "zoho.com", "gmx.com", "gmx.net",
    "mail.com", "yandex.com", "yandex.ru", "qq.com", "163.com", "126.com",
    "naver.com", "daum.net", "web.de", "comcast.net", "verizon.net",
    "att.net", "sbcglobal.net", "cox.net", "rediffmail.com", "fastmail.com",
    "hey.com", "tutanota.com", "pm.me",
}

DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com",
    "tempmail.com", "temp-mail.org", "throwawaymail.com", "yopmail.com",
    "getnada.com", "trashmail.com", "sharklasers.com", "dispostable.com",
    "maildrop.cc", "mintemail.com", "mytemp.email",
}


class EmailValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def extract_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower().strip()


def check_work_domain(domain: str) -> None:
    if domain in FREE_EMAIL_DOMAINS:
        raise EmailValidationError(
            "Personal email providers are not allowed. Please use your work email."
        )
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        raise EmailValidationError(
            "Disposable email addresses are not allowed. Please use your work email."
        )


def check_mx_records(domain: str) -> None:
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=5.0)
        if not list(answers):
            raise EmailValidationError("This domain cannot receive email.")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        raise EmailValidationError(
            "This email domain does not appear to be a valid company domain."
        )
    except dns.exception.Timeout:
        # Fail open on DNS timeouts so a flaky resolver doesn't block signups.
        pass


async def lookup_company_name(domain: str) -> str:
    """Best-effort company name lookup for the domain.

    Uses Hunter.io if HUNTER_API_KEY is set, else Abstract API if
    EMAIL_VERIFY_API_KEY is set, else falls back to a prettified domain name.
    """
    hunter_key = os.environ.get("HUNTER_API_KEY")
    if hunter_key:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={"domain": domain, "api_key": hunter_key},
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    name = data.get("organization")
                    if name:
                        return name
        except httpx.HTTPError:
            pass

    api_key = os.environ.get("EMAIL_VERIFY_API_KEY")
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://companyenrichment.abstractapi.com/v2/",
                    params={"api_key": api_key, "domain": domain},
                )
                if resp.status_code == 200:
                    name = resp.json().get("name")
                    if name:
                        return name
        except httpx.HTTPError:
            pass
    return domain.rsplit(".", 1)[0].replace("-", " ").title()


async def validate_work_email(email: str) -> tuple[str, str]:
    """Validate a work email. Returns (domain, company_name) or raises."""
    domain = extract_domain(email)
    check_work_domain(domain)
    check_mx_records(domain)
    company_name = await lookup_company_name(domain)
    return domain, company_name
