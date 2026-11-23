"""
Errores de la API como claves de traducción (R-IDI-03, Docs/10-api.md §1).

Toda respuesta de error tiene la forma {"error": "<clave>", "detail": {...}}.
La clave la traduce la interfaz; el servidor nunca devuelve textos para el usuario.
"""
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class ApiError(exceptions.APIException):
    """Error de negocio con clave de traducción y, opcionalmente, datos para la interfaz."""

    def __init__(self, key: str, status_code: int = status.HTTP_400_BAD_REQUEST, **detail):
        self.key = key
        self.status_code = status_code
        self.extra = detail
        super().__init__(detail=key, code=key)


_KEYS = [
    (exceptions.NotAuthenticated, "not_authenticated"),
    (exceptions.AuthenticationFailed, "not_authenticated"),
    (exceptions.PermissionDenied, "forbidden"),
    (exceptions.NotFound, "not_found"),
    (exceptions.MethodNotAllowed, "method_not_allowed"),
    (exceptions.Throttled, "rate_limited"),
    (exceptions.ParseError, "invalid_input"),
    (exceptions.UnsupportedMediaType, "invalid_input"),
]


def custom_exception_handler(exc, context):
    if isinstance(exc, ApiError):
        return Response({"error": exc.key, "detail": exc.extra}, status=exc.status_code)

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)
    if response is not None:
        if isinstance(exc, exceptions.ValidationError):
            response.data = {"error": "invalid_input", "detail": exc.get_codes()}
        else:
            key = next((k for cls, k in _KEYS if isinstance(exc, cls)), "server_error")
            response.data = {"error": key, "detail": {}}
        return response

    # Un refresh válido puede apuntar a una cuenta que ya no existe (eliminada o
    # base de desarrollo reiniciada): es una credencial inválida, no un 500.
    if isinstance(exc, ObjectDoesNotExist):
        return Response({"error": "not_authenticated", "detail": {}}, status=status.HTTP_401_UNAUTHORIZED)

    return None
