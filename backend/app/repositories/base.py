"""Operaciones de persistencia reutilizables."""
from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.errors import not_found

ModelT = TypeVar("ModelT")


def get_or_404(db: Session, model: type[ModelT], obj_id: int, message: str | None = None) -> ModelT:
    obj = db.get(model, obj_id)
    if obj is None:
        raise not_found(message or "Recurso no encontrado")
    return obj


def paginate(db: Session, stmt: Select, page: int, size: int) -> dict[str, Any]:
    """Ejecuta una consulta paginada y devuelve {items, total, page, size}."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    items = db.scalars(stmt.offset((page - 1) * size).limit(size)).unique().all()
    return {"items": list(items), "total": total, "page": page, "size": size}


def like(term: str) -> str:
    """Patrón para búsquedas parciales sin distinguir mayúsculas."""
    return f"%{term.strip()}%"
