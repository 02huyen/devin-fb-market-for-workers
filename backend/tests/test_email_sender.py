import pytest

from app.services.email_sender import send_magic_link_email


class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


@pytest.fixture
def fake_post_factory(monkeypatch):
    def _make(resend_status=200, sendgrid_status=202):
        async def _post(self, *args, **kwargs):
            url = args[0] if args else ""
            if "resend" in url:
                return FakeResponse(resend_status)
            if "sendgrid" in url:
                return FakeResponse(sendgrid_status)
            return FakeResponse(500)

        monkeypatch.setattr("httpx.AsyncClient.post", _post)

    return _make


async def test_send_no_provider_returns_false():
    sent = await send_magic_link_email("user@example.com", "http://test/verify?token=abc")
    assert sent is False


async def test_send_resend(fake_post_factory, monkeypatch):
    fake_post_factory(resend_status=201)
    monkeypatch.setenv("RESEND_API_KEY", "test-resend-key")
    sent = await send_magic_link_email("user@example.com", "http://test/verify?token=abc")
    assert sent is True


async def test_send_sendgrid(fake_post_factory, monkeypatch):
    fake_post_factory(sendgrid_status=202)
    monkeypatch.setenv("SENDGRID_API_KEY", "test-sendgrid-key")
    sent = await send_magic_link_email("user@example.com", "http://test/verify?token=abc")
    assert sent is True


async def test_send_resend_failure_falls_back_to_sendgrid(fake_post_factory, monkeypatch):
    fake_post_factory(resend_status=500, sendgrid_status=202)
    monkeypatch.setenv("RESEND_API_KEY", "test-resend-key")
    monkeypatch.setenv("SENDGRID_API_KEY", "test-sendgrid-key")
    sent = await send_magic_link_email("user@example.com", "http://test/verify?token=abc")
    assert sent is True


async def test_send_all_providers_fail(fake_post_factory, monkeypatch):
    fake_post_factory(resend_status=500, sendgrid_status=500)
    monkeypatch.setenv("RESEND_API_KEY", "test-resend-key")
    monkeypatch.setenv("SENDGRID_API_KEY", "test-sendgrid-key")
    sent = await send_magic_link_email("user@example.com", "http://test/verify?token=abc")
    assert sent is False
