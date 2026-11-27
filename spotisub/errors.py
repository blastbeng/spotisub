"""Spotisub error handlers"""

import json

from flask import Response
from flask import render_template
from flask import request
from spotisub import spotisub, configuration_db


def _api_error(message, status):
    """Return the REST endpoints' JSON error shape for a failed request."""
    r = Response(
        response=json.dumps({"status": "ko", "message": message}),
        status=status,
        mimetype="application/json")
    r.headers["Content-Type"] = "application/json; charset=utf-8"
    return r


@spotisub.errorhandler(404)
def not_found_error(error):
    """Not found handler"""
    if request.path.startswith('/api/'):
        return _api_error('Resource not found', 404)
    return render_template('errors/404.html', title='Page Not Found'), 404


@spotisub.errorhandler(500)
def internal_error(error):
    """Internal error handler"""
    configuration_db.session.rollback()
    if request.path.startswith('/api/'):
        return _api_error('Internal server error', 500)
    return render_template('errors/500.html', title='Unexpected Error'), 500
