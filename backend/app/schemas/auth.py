from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel, clean_text
from app.schemas.persona import MedicoOut, PacienteBase, PacienteOut
from app.schemas.validators import Direccion, Email, Password, Telefono


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=64)


class RegisterRequest(PacienteBase):
    """Registro público: siempre crea una cuenta con rol paciente."""

    email: Email
    password: Password


class UserMe(ORMModel):
    id: int
    email: str
    rol: str
    activo: bool
    nombre_completo: str
    creado_en: datetime
    paciente: PacienteOut | None = None
    medico: MedicoOut | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserMe


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=64)
    new_password: Password


class ProfileUpdate(BaseModel):
    """Campos que el propio usuario puede editar de su perfil."""

    telefono: Telefono | None = None
    direccion: Direccion | None = None

    @field_validator("direccion")
    @classmethod
    def _clean(cls, v):
        return clean_text(v)
