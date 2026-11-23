"""Test-only stand-in for flask_restx, used by spotisub/routes.py to define
the /api/v1 REST endpoints (unrelated to the logic this suite exercises).
Just enough surface for routes.py to import and define its
Api/Namespace/Resource classes at module load time without registering real
routes."""


class Resource:
    """Minimal stand-in for flask_restx.Resource (test stub)."""
    pass


class Namespace:
    def __init__(self, name, description=None):
        self.name = name
        self.description = description

    def route(self, path):
        def decorator(cls):
            return cls
        return decorator


class Api:
    def __init__(self, *args, **kwargs):
        pass

    def namespace(self, name, description=None):
        return Namespace(name, description)
