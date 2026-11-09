"""Auditoría básica de acciones. Solo lectura desde la API."""
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Auditoria
from app.repositories.base import paginate


def log(
    db: Session,
    usuario_id: int | None,
    accion: str,
    recurso: str,
    recurso_id: int | None = None,
    resultado: str = "exito",
    detalle: str | None = None,
) -> None:
    """Agrega un registro de auditoría a la transacción actual.

    Nunca se deben pasar contraseñas, tokens ni datos clínicos en 'detalle'.
    """
    db.add(
        Auditoria(
            usuario_id=usuario_id,
            accion=accion,
            recurso=recurso,
            recurso_id=recurso_id,
            resultado=resultado,
            detalle=(detalle or None) and detalle[:255],
        )
    )


def list_logs(
    db: Session,
    page: int,
    size: int,
    accion: str | None = None,
    recurso: str | None = None,
    usuario_id: int | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> dict:
    stmt = select(Auditoria)
    if accion:
        stmt = stmt.where(Auditoria.accion == accion)
    if recurso:
        stmt = stmt.where(Auditoria.recurso == recurso)
    if usuario_id:
        stmt = stmt.where(Auditoria.usuario_id == usuario_id)
    if fecha_desde:
        stmt = stmt.where(Auditoria.creado_en >= datetime.combine(fecha_desde, time.min))
    if fecha_hasta:
        stmt = stmt.where(Auditoria.creado_en <= datetime.combine(fecha_hasta, time.max))
    stmt = stmt.order_by(Auditoria.creado_en.desc(), Auditoria.id.desc())
    return paginate(db, stmt, page, size)
