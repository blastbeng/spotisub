"""Test-only stand-in for pygtail, used by spotisub/routes.py to tail the
application log file for the UI (unrelated to the logic this suite
exercises)."""


class Pygtail:
    """Minimal stand-in for pygtail.Pygtail (test stub)."""

    def __init__(self, *args, **kwargs):
        pass

    def __iter__(self):
        return iter([])
