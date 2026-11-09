"""Esquemas de autorizaciones, notificaciones, usuarios y auditoría."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.constants import ESTADOS_AUTORIZACION, ROLES
from app.schemas.common import ORMModel, clean_text


# ---------- Autorizaciones ----------
class AutorizacionCreate(BaseModel):
    servicio_id: int = Field(gt=0)
    motivo: str = Field(min_length=5, max_length=255)

    @field_validator("motivo")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class AutorizacionStatusUpdate(BaseModel):
    estado: Literal[ESTADOS_AUTORIZACION]  # type: ignore[valid-type]
    observaciones: str | None = Field(default=None, max_length=500)

    @field_validator("observaciones")
    @classmethod
    def _clean(cls, v):
        return clean_text(v)


class AutorizacionOut(ORMModel):
    id: int
    paciente_id: int
    paciente_nombre: str
    servicio_id: int
    servicio_nombre: str
    motivo: str
    estado: str
    observaciones: str | None
    creado_en: datetime
    actualizado_en: datetime


class HistorialOut(ORMModel):
    id: int
    estado_anterior: str | None
    estado_nuevo: str
    observacion: str | None
    usuario_id: int
    usuario_nombre: str
    usuario_rol: str
    creado_en: datetime


# ---------- Notificaciones ----------
class NotificacionOut(ORMModel):
    id: int
    titulo: str
    mensaje: str
    tipo: str
    leida: bool
    creado_en: datetime


# ---------- Usuarios ----------
class UsuarioOut(ORMModel):
    id: int
    email: str
    rol: str
    activo: bool
    nombre_completo: str
    creado_en: datetime


class RoleUpdate(BaseModel):
    rol: Literal[ROLES]  # type: ignore[valid-type]


# ---------- Auditoría ----------
class AuditoriaOut(ORMModel):
    id: int
    usuario_id: int | None
    usuario_email: str | None
    accion: str
    recurso: str
    recurso_id: int | None
    resultado: str
    detalle: str | None
    creado_en: datetime
