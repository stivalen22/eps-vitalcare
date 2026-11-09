"""Esquemas de pacientes y médicos."""
from datetime import date, datetime
from typing import Annotated, Union

from pydantic import BaseModel, Field, field_validator

from app.schemas.catalogo import EspecialidadOut
from app.schemas.common import ORMModel, clean_text
from app.schemas.validators import (
    Direccion,
    Email,
    FechaNacimiento,
    Nombre,
    NumeroDocumento,
    Password,
    Telefono,
    TipoDocumento,
)


# ---------- Pacientes ----------
class PacienteBase(BaseModel):
    tipo_documento: TipoDocumento
    numero_documento: NumeroDocumento
    nombres: Nombre
    apellidos: Nombre
    fecha_nacimiento: FechaNacimiento
    telefono: Telefono
    direccion: Direccion | None = None

    @field_validator("direccion")
    @classmethod
    def _clean(cls, v):
        return clean_text(v)


class PacienteCreate(PacienteBase):
    """Creación por el administrador (incluye la cuenta de acceso)."""

    email: Email
    password: Password


class PacienteUpdate(PacienteBase):
    email: Email


class PacienteOut(ORMModel):
    id: int
    usuario_id: int
    email: str
    activo: bool
    tipo_documento: str
    numero_documento: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    telefono: str
    direccion: str | None
    creado_en: datetime


class PacienteMinOut(ORMModel):
    """Datos mínimos que puede ver un médico de un paciente asignado."""

    id: int
    tipo_documento: str
    numero_documento: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    telefono: str


# ---------- Médicos ----------
class MedicoBase(BaseModel):
    nombres: Nombre
    apellidos: Nombre
    telefono: Telefono
    registro_profesional: str = Field(min_length=4, max_length=30, description="Identificador académico ficticio")
    especialidad_ids: list[int] = Field(min_length=1, description="Al menos una especialidad")

    @field_validator("registro_profesional")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("especialidad_ids")
    @classmethod
    def _unique(cls, v: list[int]) -> list[int]:
        return sorted(set(v))


class MedicoCreate(MedicoBase):
    email: Email
    password: Password


class MedicoUpdate(MedicoBase):
    email: Email


class MedicoOut(ORMModel):
    id: int
    usuario_id: int
    email: str
    activo: bool
    nombres: str
    apellidos: str
    telefono: str
    registro_profesional: str
    especialidades: list[EspecialidadOut]
    creado_en: datetime


class MedicoPublicOut(ORMModel):
    """Vista pública del médico para pacientes (sin datos de contacto)."""

    id: int
    nombres: str
    apellidos: str
    activo: bool
    especialidades: list[EspecialidadOut]


# Respuestas que varían según el rol. 'left_to_right' prueba primero el esquema completo.
PacienteDetalle = Annotated[Union[PacienteOut, PacienteMinOut], Field(union_mode="left_to_right")]
MedicoDetalle = Annotated[Union[MedicoOut, MedicoPublicOut], Field(union_mode="left_to_right")]
