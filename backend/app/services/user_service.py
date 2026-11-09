"""Administración de cuentas de usuario y roles."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.constants import ROL_ADMIN, ROL_MEDICO, ROL_PACIENTE
from app.core.errors import conflict
from app.models import Medico, Paciente, Usuario
from app.repositories import usuarios as repo
from app.repositories.base import get_or_404, like, paginate
from app.services import audit_service


def list_users(
    db: Session, page: int, size: int, q: str | None = None, rol: str | None = None, activo: bool | None = None
) -> dict:
    stmt = select(Usuario).outerjoin(Paciente, Paciente.usuario_id == Usuario.id).outerjoin(
        Medico, Medico.usuario_id == Usuario.id
    )
    if q:
        pattern = like(q)
        stmt = stmt.where(
            or_(
                Usuario.email.ilike(pattern),
                Paciente.nombres.ilike(pattern),
                Paciente.apellidos.ilike(pattern),
                Medico.nombres.ilike(pattern),
                Medico.apellidos.ilike(pattern),
            )
        )
    if rol:
        stmt = stmt.where(Usuario.rol == rol)
    if activo is not None:
        stmt = stmt.where(Usuario.activo.is_(activo))
    return paginate(db, stmt.order_by(Usuario.id), page, size)


def _ensure_not_last_admin(db: Session, user: Usuario) -> None:
    if user.rol == ROL_ADMIN and user.activo and repo.count_active_admins(db) <= 1:
        raise conflict("Debe existir al menos un administrador activo")


def change_role(db: Session, admin: Usuario, user_id: int, rol: str) -> Usuario:
    user = get_or_404(db, Usuario, user_id, "Usuario no encontrado")
    if user.id == admin.id:
        raise conflict("No puede modificar el rol de su propia cuenta")
    if user.rol == rol:
        return user
    # El rol debe ser coherente con el perfil existente
    if rol == ROL_PACIENTE and user.paciente is None:
        raise conflict("La cuenta no tiene perfil de paciente; no puede asignarse ese rol")
    if rol == ROL_MEDICO and user.medico is None:
        raise conflict("La cuenta no tiene perfil de médico; regístrela desde el módulo de médicos")
    _ensure_not_last_admin(db, user)
    anterior = user.rol
    user.rol = rol
    audit_service.log(db, admin.id, "cambiar_rol", "usuario", user.id, detalle=f"{anterior} -> {rol}")
    db.commit()
    db.refresh(user)
    return user


def set_status(db: Session, admin: Usuario, user_id: int, activo: bool) -> Usuario:
    user = get_or_404(db, Usuario, user_id, "Usuario no encontrado")
    if user.id == admin.id and not activo:
        raise conflict("No puede desactivar su propia cuenta")
    if not activo:
        _ensure_not_last_admin(db, user)
    user.activo = activo
    audit_service.log(db, admin.id, "activar" if activo else "desactivar", "usuario", user.id)
    db.commit()
    db.refresh(user)
    return user
