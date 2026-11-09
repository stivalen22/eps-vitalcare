"""Validaciones reutilizables para los esquemas Pydantic."""
import re
from datetime import date
from typing import Annotated, Literal

from pydantic import AfterValidator, EmailStr, StringConstraints

from app.core.constants import TIPOS_DOCUMENTO

TipoDocumento = Literal[TIPOS_DOCUMENTO]  # type: ignore[valid-type]

Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
Telefono = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[0-9+\- ]{7,20}$")]
NumeroDocumento = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[0-9A-Za-z]{4,20}$")]
Direccion = Annotated[str, StringConstraints(strip_whitespace=True, max_length=150)]


def _lower(v: str) -> str:
    return v.strip().lower()


Email = Annotated[EmailStr, AfterValidator(_lower)]


def _password_strength(v: str) -> str:
    if len(v) < 8 or len(v) > 64:
        raise ValueError("La contraseña debe tener entre 8 y 64 caracteres")
    if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
        raise ValueError("La contraseña debe contener al menos una letra y un número")
    return v


Password = Annotated[str, AfterValidator(_password_strength)]


def _birth_date(v: date) -> date:
    today = date.today()
    if v > today:
        raise ValueError("La fecha de nacimiento no puede ser futura")
    if v.year < today.year - 120:
        raise ValueError("La fecha de nacimiento no es válida")
    return v


FechaNacimiento = Annotated[date, AfterValidator(_birth_date)]
