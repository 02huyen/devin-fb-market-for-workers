import dns.resolver
import pytest

from app.services.email_validation import (
    EmailValidationError,
    _is_disposable_domain,
    validate_work_email,
)


class FakeResponse:
    def __init__(self, status_code, json_data, text=""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def json(self):
        return self._json


@pytest.fixture
def fake_abstract_get(monkeypatch):
    async def _get(self, *args, **kwargs):
        return FakeResponse(200, {"name": "Example Inc"})

    monkeypatch.setattr("httpx.AsyncClient.get", _get)


async def test_extract_domain_and_validate_work_email():
    domain, company = await validate_work_email("user@example.com")
    assert domain == "example.com"
    assert company == "Example"


async def test_validate_work_email_rejects_free_email():
    with pytest.raises(EmailValidationError) as exc:
        await validate_work_email("user@gmail.com")
    assert "work email" in exc.value.message


async def test_validate_work_email_rejects_disposable_email():
    with pytest.raises(EmailValidationError) as exc:
        await validate_work_email("user@mailinator.com")
    assert "Disposable" in exc.value.message


async def test_validate_work_email_rejects_package_blocklist():
    with pytest.raises(EmailValidationError) as exc:
        await validate_work_email("user@laptoplonghai.com")
    assert "Disposable" in exc.value.message


async def test_is_disposable_domain_checks_parent_domains():
    assert _is_disposable_domain("sub.yopmail.com") is True
    assert _is_disposable_domain("yopmail.com") is True
    assert _is_disposable_domain("example.com") is False


async def test_lookup_company_name_abstract_api(fake_abstract_get, monkeypatch):
    monkeypatch.setenv("EMAIL_VERIFY_API_KEY", "test-abstract-key")
    domain, company = await validate_work_email("user@example.com")
    assert domain == "example.com"
    assert company == "Example Inc"


async def test_rejects_no_mx_records(monkeypatch):
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: [],
    )
    with pytest.raises(EmailValidationError) as exc:
        await validate_work_email("test@example.com")
    assert "cannot receive email" in exc.value.message


async def test_rejects_nxdomain(monkeypatch):
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: (_ for _ in ()).throw(dns.resolver.NXDOMAIN()),
    )
    with pytest.raises(EmailValidationError) as exc:
        await validate_work_email("test@example.com")
    assert "does not appear" in exc.value.message
