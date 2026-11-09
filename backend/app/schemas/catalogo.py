from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel, clean_text


class EspecialidadCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=80)
    descripcion: str | None = Field(default=None, max_length=255)

    @field_validator("nombre")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("descripcion")
    @classmethod
    def _clean(cls, v):
        return clean_text(v)


class EspecialidadUpdate(EspecialidadCreate):
    pass


class EspecialidadOut(ORMModel):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool
    creado_en: datetime


class ServicioCreate(BaseModel):
    nombre: str = Field(min_length=3, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)
    especialidad_id: int = Field(gt=0)
    duracion_minutos: int = Field(ge=10, le=240, description="Duración estimada entre 10 y 240 minutos")

    @field_validator("nombre")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("descripcion")
    @classmethod
    def _clean(cls, v):
        return clean_text(v)


class ServicioUpdate(ServicioCreate):
    pass


class ServicioOut(ORMModel):
    id: int
    nombre: str
    descripcion: str | None
    especialidad_id: int
    especialidad_nombre: str
    duracion_minutos: int
    activo: bool
    creado_en: datetime
