"""Regression tests for the REST endpoints in spotisub.routes.

The /api/v1/import/* and /api/v1/generate/* endpoints start a scheduler job in
a background thread. They used to reference `scheduler` without importing it,
so every call raised NameError inside the handler and returned the HTML error
page instead of a JSON response.
"""
from spotisub import generator, routes


def test_routes_imports_the_generator_scheduler():
    """The name the endpoints call must resolve to the running scheduler."""
    assert routes.scheduler is generator.scheduler


def test_scheduler_can_look_up_an_unregistered_job():
    """get_job() on an unknown id returns None, it must not raise.

    This is what the endpoints rely on to decide whether a job is already
    scheduled, so it also pins the APScheduler behaviour they assume.
    """
    assert routes.scheduler.get_job("no-such-job-id") is None
