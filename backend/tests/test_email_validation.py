import pytest
from unittest.mock import Mock

import dns.resolver

from app.services.email_validation import EmailValidationError, validate_work_email


@pytest.mark.asyncio
async def test_accepts_work_email(monkeypatch):
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: [Mock()],
    )
    domain, company = await validate_work_email("dev@example.com")
    assert domain == "example.com"
    assert company == "Example"


@pytest.mark.asyncio
async def test_rejects_free_email():
    with pytest.raises(EmailValidationError) as exc:
        await validate_work_email("test@gmail.com")
    assert "Personal email" in exc.value.message


@pytest.mark.asyncio
async def test_rejects_disposable_email():
    with pytest.raises(EmailValidationError) as exc:
        await validate_work_email("test@mailinator.com")
    assert "Disposable" in exc.value.message


@pytest.mark.asyncio
async def test_rejects_no_mx_records(monkeypatch):
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: [],
    )
    with pytest.raises(EmailValidationError) as exc:
        await validate_work_email("test@example.com")
    assert "cannot receive email" in exc.value.message


@pytest.mark.asyncio
async def test_rejects_nxdomain(monkeypatch):
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: (_ for _ in ()).throw(dns.resolver.NXDOMAIN()),
    )
    with pytest.raises(EmailValidationError) as exc:
        await validate_work_email("test@example.com")
    assert "does not appear" in exc.value.message
