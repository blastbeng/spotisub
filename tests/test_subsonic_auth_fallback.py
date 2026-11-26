"""Regression tests for Subsonic authentication handling (#98).

Spotisub used to send only the salted token authentication that libsonic
does by default. Servers older than Subsonic API 1.13 answer error 40 to
that scheme even with a correct password -- and with a password that *is*
wrong the old code called the server "offline" (an empty exception message)
and retried the same rejected credentials, feeding the server's failed-login
limiter.

The connection check now:
  * falls back once to the plain password scheme (hex encoded by libsonic),
  * reports a rejected login as SubsonicAuthException with the server's own
    reason instead of SubsonicOfflineException,
  * retries only transient connection errors.
"""
import pytest
from libsonic.errors import CredentialError

from spotisub.exceptions import SubsonicAuthException, SubsonicOfflineException
from spotisub.helpers import subsonic_helper


class _FakePysonic:
    """Stand-in for libsonic.Connection with scripted getMusicFolders()."""

    def __init__(self, errors=None):
        self.errors = list(errors or [])
        self.calls = 0
        self.legacy_auth = None

    def getMusicFolders(self):
        """Raise the next scripted error, then answer like libsonic."""
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return {"musicFolders": {"musicFolder": []}}


@pytest.fixture
def fake_connections(monkeypatch):
    """Install a fake token connection and record every fallback build."""
    built = []

    def _install(token_errors, legacy_errors=None):
        token = _FakePysonic(token_errors)
        monkeypatch.setattr(subsonic_helper, "pysonic", token)
        monkeypatch.setattr(subsonic_helper, "_auth_fallback_checked", False)

        def _build(legacy_auth=False):
            legacy = _FakePysonic(legacy_errors)
            legacy.legacy_auth = legacy_auth
            built.append(legacy)
            return legacy

        monkeypatch.setattr(subsonic_helper, "_build_pysonic", _build)
        return token

    return _install, built


def test_valid_credentials_use_token_auth_without_a_fallback(fake_connections):
    """The normal path must not build a second connection."""
    install, built = fake_connections
    token = install([])

    assert subsonic_helper.check_pysonic_connection() is token
    assert token.calls == 1
    assert built == []


def test_server_rejecting_token_auth_falls_back_to_password_auth(
        fake_connections, monkeypatch):
    """A pre-1.13 server gets one retry with the password scheme."""
    install, built = fake_connections
    token = install([CredentialError("Wrong username or password")])

    connection = subsonic_helper.check_pysonic_connection()

    assert token.calls == 1, "a credential error must not be retried as-is"
    assert len(built) == 1
    assert built[0].legacy_auth is True
    assert connection is built[0]
    # the working connection replaces the module-level one for the next call
    assert subsonic_helper.pysonic is built[0]


def test_rejected_password_is_an_auth_error_not_an_offline_server(
        fake_connections):
    """The operator must see the server's reason, not a bare 'offline'."""
    install, _ = fake_connections
    install([CredentialError("Wrong username or password")],
            [CredentialError("Wrong username or password")])

    with pytest.raises(SubsonicAuthException) as raised:
        subsonic_helper.check_pysonic_connection()

    message = str(raised.value)
    assert "Wrong username or password" in message
    assert "SUBSONIC_API_PASS" in message
    assert subsonic_helper.constants.get_subsonic_rest_url() in message
    assert "subsonic.invalid" in message
    # existing handlers catch SubsonicOfflineException; keep that contract
    assert isinstance(raised.value, SubsonicOfflineException)


def test_rejected_credentials_are_tried_once_not_twice(fake_connections):
    """No blind retry: it would hit the server's failed-login limiter."""
    install, _ = fake_connections
    token = install(
        [CredentialError("Wrong username or password")] * 2,
        [CredentialError("Wrong username or password")])

    with pytest.raises(SubsonicAuthException):
        subsonic_helper.check_pysonic_connection()

    assert token.calls == 1


def test_password_fallback_is_probed_once_per_process(fake_connections):
    """A later failure must not build and try another connection."""
    install, built = fake_connections
    token = install(
        [CredentialError("Wrong username or password")] * 2,
        [CredentialError("Wrong username or password")])

    with pytest.raises(SubsonicAuthException):
        subsonic_helper.check_pysonic_connection()
    with pytest.raises(SubsonicAuthException):
        subsonic_helper.check_pysonic_connection()

    assert len(built) == 1
    assert token.calls == 2  # one attempt per check, no doubling


def test_transient_connection_error_is_retried_once(fake_connections):
    """Network hiccups keep the old single retry."""
    install, built = fake_connections
    token = install([ConnectionRefusedError("connection refused")])

    assert subsonic_helper.check_pysonic_connection() is token
    assert token.calls == 2
    assert built == []


def test_unreachable_server_reports_the_target(fake_connections):
    """An offline server says where Spotisub tried to connect."""
    install, _ = fake_connections
    install([ConnectionRefusedError("connection refused")] * 2)

    with pytest.raises(SubsonicOfflineException) as raised:
        subsonic_helper.check_pysonic_connection()

    message = str(raised.value)
    assert "Cannot reach the Subsonic server" in message
    assert "subsonic.invalid" in message
    assert not isinstance(raised.value, SubsonicAuthException)


def test_status_endpoint_titles_an_auth_failure_distinctly(
        fake_connections, monkeypatch):
    """The check button must not call a rejected login 'Server Offline'."""
    from spotisub import spotisub as app

    install, _ = fake_connections
    install([CredentialError("Wrong username or password")],
            [CredentialError("Wrong username or password")])
    monkeypatch.setitem(app.config, "LOGIN_DISABLED", True)

    response = app.test_client().post("/check-subsonic-status")
    payload = response.get_json()

    assert payload["status"] == "error"
    assert payload["title"] == "Subsonic Authentication Failed"
    assert "Wrong username or password" in payload["message"]
