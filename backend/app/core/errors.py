"""Errores de negocio y manejadores de excepciones con respuestas JSON consistentes.

Formato de error: {"detail": "mensaje legible", "errors": [...] (solo en 422)}
"""
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("vitalcare")


def not_found(message: str = "Recurso no encontrado") -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, message)


def forbidden(message: str = "No tiene permisos para realizar esta operación") -> HTTPException:
    return HTTPException(status.HTTP_403_FORBIDDEN, message)


def conflict(message: str) -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, message)


def invalid(message: str) -> HTTPException:
    return HTTPException(422, message)


def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", []) if p not in ("body", "query", "path")]
        msg = str(err.get("msg", "Valor inválido")).replace("Value error, ", "")
        errors.append({"campo": ".".join(loc) or "general", "mensaje": msg})
    return JSONResponse(
        status_code=422,
        content={"detail": "Los datos enviados no son válidos", "errors": errors},
    )


def _integrity_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Error de integridad: %s", exc.orig)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "La operación viola una restricción de integridad de los datos"},
    )


def _unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(IntegrityError, _integrity_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
