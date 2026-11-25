"""Test-only stand-in for flask_socketio, used by spotisub/routes.py for the
live-progress websocket UI (unrelated to the logic this suite exercises).
Just enough surface for routes.py to import and decorate its handlers at
module load time."""


def emit(*args, **kwargs):
    pass


def join_room(*args, **kwargs):
    pass


def leave_room(*args, **kwargs):
    pass


def close_room(*args, **kwargs):
    pass


def rooms(*args, **kwargs):
    return []


def disconnect(*args, **kwargs):
    pass


class SocketIO:
    """Minimal stand-in for flask_socketio.SocketIO (test stub)."""

    def __init__(self, app=None, **kwargs):
        self.app = app

    def init_app(self, app, **kwargs):
        self.app = app

    def event(self, f):
        return f

    def on(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator

    def start_background_task(self, target, *args, **kwargs):
        return None

    def sleep(self, seconds):
        pass

    def run(self, *args, **kwargs):
        pass
