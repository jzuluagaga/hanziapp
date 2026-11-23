"""Datos del cliente de la petición en curso, para los campos comunes de los eventos."""
from contextvars import ContextVar

_client: ContextVar[str] = ContextVar("analytics_client", default="")
_app_version: ContextVar[str] = ContextVar("analytics_app_version", default="")

VALID_CLIENTS = {"mobile_web", "desktop_web"}


def current_client() -> str:
    return _client.get()


def current_app_version() -> str:
    return _app_version.get()


class ClientContextMiddleware:
    """Lee `X-Client` y `X-App-Version` (Docs/10-api.md §1)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client = request.headers.get("X-Client", "")
        t1 = _client.set(client if client in VALID_CLIENTS else "")
        t2 = _app_version.set(request.headers.get("X-App-Version", "")[:20])
        try:
            return self.get_response(request)
        finally:
            _client.reset(t1)
            _app_version.reset(t2)
