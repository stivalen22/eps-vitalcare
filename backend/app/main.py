"""Punto de entrada de la API EPS VitalCare.

Ejecutar en desarrollo:  uvicorn app.main:app --reload
Documentación interactiva: http://localhost:8000/docs
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import DEFAULT_SECRET, settings
from app.core.errors import register_exception_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == DEFAULT_SECRET:
    raise RuntimeError("Configure una SECRET_KEY propia antes de ejecutar en producción")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "API REST del prototipo académico **EPS VitalCare**: gestión de pacientes, médicos, citas, "
        "servicios y autorizaciones. Datos ficticios; no representa una EPS real.\n\n"
        "Para probar endpoints protegidos: ejecute `POST /api/v1/auth/login`, copie el `access_token` "
        "y péguelo en el botón **Authorize**."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Estado"])
def root():
    return {"app": settings.APP_NAME, "docs": "/docs", "estado": "en ejecución"}


@app.get("/health", tags=["Estado"])
def health():
    return {"status": "ok"}
