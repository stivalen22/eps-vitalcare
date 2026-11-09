"""Notificaciones internas (no se envían correos ni SMS)."""
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.models import Notificacion, Usuario
from app.repositories.base import paginate


def notify(db: Session, usuario_id: int, titulo: str, mensaje: str, tipo: str) -> None:
    """Agrega una notificación a la transacción actual (se confirma con el commit del servicio)."""
    db.add(Notificacion(usuario_id=usuario_id, titulo=titulo, mensaje=mensaje[:500], tipo=tipo))


def list_for_user(db: Session, user: Usuario, page: int, size: int, solo_no_leidas: bool = False) -> dict:
    stmt = select(Notificacion).where(Notificacion.usuario_id == user.id)
    if solo_no_leidas:
        stmt = stmt.where(Notificacion.leida.is_(False))
    stmt = stmt.order_by(Notificacion.creado_en.desc(), Notificacion.id.desc())
    return paginate(db, stmt, page, size)


def mark_read(db: Session, user: Usuario, notificacion_id: int) -> Notificacion:
    notif = db.get(Notificacion, notificacion_id)
    # Se responde 404 también si pertenece a otro usuario para no revelar su existencia
    if notif is None or notif.usuario_id != user.id:
        raise not_found("Notificación no encontrada")
    notif.leida = True
    db.commit()
    db.refresh(notif)
    return notif


def mark_all_read(db: Session, user: Usuario) -> int:
    result = db.execute(
        update(Notificacion)
        .where(Notificacion.usuario_id == user.id, Notificacion.leida.is_(False))
        .values(leida=True)
    )
    db.commit()
    return result.rowcount or 0
