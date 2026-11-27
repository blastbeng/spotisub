"""Regression tests for the global error handlers.

Every unhandled exception used to be rendered with the 404 template and an
HTTP 200 status, including `repr(error)` in the page for logged-in users, so
internal paths and database URIs leaked and browsers, proxies and the REST
clients all believed the request succeeded. HTTP errors (405, 404, ...) were
swallowed the same way.
"""
import json

import pytest

from spotisub import spotisub, routes

MARKER = 'INTERNAL-MARKER-/srv/spotisub.db'


def _raise_and_handle(path):
    """Run the app error handler as Flask would, for an exception raised on `path`."""
    with spotisub.test_request_context(path):
        try:
            raise RuntimeError(MARKER)
        except RuntimeError as error:  # pylint: disable=broad-except
            return routes.all_exception_handler(error)


def test_unhandled_exception_returns_500_without_leaking_details():
    """A bug is a 500, and the exception text never reaches the page."""
    body, status = _raise_and_handle('/overview/')
    assert status == 500
    assert MARKER not in body
    assert 'Traceback' not in body


def test_unhandled_exception_on_api_path_returns_json_500():
    """REST clients get the usual status/message payload, not an HTML page."""
    response = _raise_and_handle('/api/v1/utils/healthcheck')
    assert response.status_code == 500
    assert response.mimetype == 'application/json'
    payload = json.loads(response.get_data(as_text=True))
    assert payload == {'status': 'ko', 'message': 'Internal server error'}
    assert MARKER not in response.get_data(as_text=True)


def test_wrong_method_keeps_its_own_status():
    """405 must not become a 200 or a 500: it is not an application bug."""
    response = spotisub.test_client().post('/overview/')
    assert response.status_code == 405


def test_unknown_page_is_a_404_page():
    """An unknown URL still renders the HTML 404 page."""
    response = spotisub.test_client().get('/no-such-page/')
    assert response.status_code == 404
    assert response.mimetype == 'text/html'


@pytest.mark.parametrize('path', ['/api/v1/no-such-endpoint/', '/api/v1/generate/nope/'])
def test_unknown_api_path_is_a_json_404(path):
    """An unknown REST path answers in JSON, like every other API response."""
    response = spotisub.test_client().get(path)
    assert response.status_code == 404
    assert response.mimetype == 'application/json'
    assert json.loads(response.get_data(as_text=True)) == {
        'status': 'ko', 'message': 'Resource not found'}
