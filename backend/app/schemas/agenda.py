"""Esquemas de horarios, citas y consultas."""
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.constants import ESTADOS_CITA
from app.schemas.common import ORMModel, clean_text


# ---------- Horarios ----------
class HorarioCreate(BaseModel):
    medico_id: int | None = Field(default=None, description="Obligatorio para el administrador")
    dia_semana: int = Field(ge=0, le=6, description="0=lunes ... 6=domingo")
    hora_inicio: time
    hora_fin: time
    duracion_cita_minutos: int = Field(default=30, ge=10, le=240)
    activo: bool = True

    @model_validator(mode="after")
    def _check_range(self):
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("La hora de finalización debe ser posterior a la hora de inicio")
        return self


class HorarioUpdate(HorarioCreate):
    pass


class HorarioOut(ORMModel):
    id: int
    medico_id: int
    medico_nombre: str
    dia_semana: int
    dia_nombre: str
    hora_inicio: time
    hora_fin: time
    duracion_cita_minutos: int
    activo: bool


class SlotOut(BaseModel):
    hora_inicio: time
    hora_fin: time


# ---------- Citas ----------
class CitaCreate(BaseModel):
    paciente_id: int | None = Field(default=None, description="Solo lo usa el administrador")
    medico_id: int = Field(gt=0)
    servicio_id: int = Field(gt=0)
    fecha: date
    hora_inicio: time
    motivo: str = Field(min_length=3, max_length=255)

    @field_validator("motivo")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("El motivo debe tener al menos 3 caracteres")
        return v


class CitaUpdate(BaseModel):
    """Reprogramación: cambia médico, fecha, hora o motivo."""

    medico_id: int = Field(gt=0)
    fecha: date
    hora_inicio: time
    motivo: str = Field(min_length=3, max_length=255)


class CitaStatusUpdate(BaseModel):
    estado: Literal[ESTADOS_CITA]  # type: ignore[valid-type]


class CitaCancel(BaseModel):
    motivo: str | None = Field(default=None, max_length=255)

    @field_validator("motivo")
    @classmethod
    def _clean(cls, v):
        return clean_text(v)


class CitaOut(ORMModel):
    id: int
    paciente_id: int
    paciente_nombre: str
    paciente_documento: str
    medico_id: int
    medico_nombre: str
    servicio_id: int
    servicio_nombre: str
    fecha: date
    hora_inicio: time
    hora_fin: time
    motivo: str
    estado: str
    motivo_cancelacion: str | None
    tiene_consulta: bool
    creado_en: datetime


# ---------- Consultas (simuladas) ----------
class ConsultaCreate(BaseModel):
    cita_id: int = Field(gt=0)
    resumen: str = Field(min_length=10, max_length=2000)
    observaciones: str | None = Field(default=None, max_length=2000)

    @field_validator("observaciones")
    @classmethod
    def _clean(cls, v):
        return clean_text(v)


class ConsultaOut(ORMModel):
    id: int
    cita_id: int
    fecha: date
    paciente_id: int
    paciente_nombre: str
    medico_id: int
    medico_nombre: str
    servicio_nombre: str
    resumen: str
    observaciones: str | None
    creado_en: datetime
