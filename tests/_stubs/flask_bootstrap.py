"""Test-only stand-in for the (unmaintained, Flask-2.2-era) Flask-Bootstrap
package. spotisub/__init__.py imports and instantiates this unconditionally
at module import time purely to wire up template helpers this test suite
never renders. See tests/conftest.py for how this directory gets onto
sys.path.
"""


class Bootstrap:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
