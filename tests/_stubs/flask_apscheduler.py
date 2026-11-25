"""Test-only stand-in for flask_apscheduler. spotisub/generator.py builds a
module-level APScheduler() and calls .add_job()/.start() unconditionally at
import time to wire up the periodic playlist-generation jobs, which is
unrelated to the logic under test. This no-op stand-in lets generator.py
(and therefore spotisub.database / spotisub.helpers.subsonic_helper, which
import through it) import cleanly without a real scheduler ticking away in
the test process."""


class APScheduler:
    """Minimal stand-in for flask_apscheduler.APScheduler (test stub)."""

    def __init__(self, scheduler=None):
        self.app = None
        self._jobs = {}

    def init_app(self, app):
        self.app = app

    def start(self, *args, **kwargs):
        pass

    def shutdown(self, *args, **kwargs):
        pass

    def add_job(self, *args, **kwargs):
        pass

    def remove_job(self, *args, **kwargs):
        pass

    def modify_job(self, *args, **kwargs):
        pass

    def get_job(self, *args, **kwargs):
        return None

    def get_jobs(self, *args, **kwargs):
        return []

    def run_job(self, *args, **kwargs):
        pass
