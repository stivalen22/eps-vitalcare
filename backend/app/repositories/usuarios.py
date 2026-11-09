from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import ROL_ADMIN
from app.models import Medico, Paciente, Usuario


def get_by_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))


def email_exists(db: Session, email: str, exclude_user_id: int | None = None) -> bool:
    stmt = select(Usuario.id).where(func.lower(Usuario.email) == email.lower())
    if exclude_user_id is not None:
        stmt = stmt.where(Usuario.id != exclude_user_id)
    return db.scalar(stmt) is not None


def documento_exists(db: Session, numero: str, exclude_paciente_id: int | None = None) -> bool:
    stmt = select(Paciente.id).where(Paciente.numero_documento == numero)
    if exclude_paciente_id is not None:
        stmt = stmt.where(Paciente.id != exclude_paciente_id)
    return db.scalar(stmt) is not None


def registro_exists(db: Session, registro: str, exclude_medico_id: int | None = None) -> bool:
    stmt = select(Medico.id).where(Medico.registro_profesional == registro)
    if exclude_medico_id is not None:
        stmt = stmt.where(Medico.id != exclude_medico_id)
    return db.scalar(stmt) is not None


def count_active_admins(db: Session) -> int:
    return db.scalar(select(func.count(Usuario.id)).where(Usuario.rol == ROL_ADMIN, Usuario.activo.is_(True))) or 0
