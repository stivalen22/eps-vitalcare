from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    """Respuesta paginada estándar."""

    items: list[T]
    total: int
    page: int
    size: int


class Message(BaseModel):
    detail: str


class StatusUpdate(BaseModel):
    activo: bool


def clean_text(value: str | None) -> str | None:
    """Recorta espacios y convierte cadenas vacías en None."""
    if value is None:
        return None
    value = value.strip()
    return value or None
