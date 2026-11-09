"""Gestión de médicos."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.constants import ESTADOS_CITA_PROGRAMADAS, ROL_MEDICO
from app.core.errors import conflict, invalid
from app.core.security import hash_password
from app.core.timeutils import now_local
from app.models import Cita, Especialidad, Medico, Usuario
from app.repositories import usuarios as user_repo
from app.repositories.base import get_or_404, like, paginate
from app.schemas.persona import MedicoCreate, MedicoUpdate
from app.services import audit_service


def _load_specialties(db: Session, ids: list[int]) -> list[Especialidad]:
    especialidades = db.scalars(select(Especialidad).where(Especialidad.id.in_(ids))).all()
    if len(especialidades) != len(ids):
        raise invalid("Una o más especialidades no existen")
    if any(not e.activo for e in especialidades):
        raise invalid("No se pueden asignar especialidades inactivas")
    return list(especialidades)


def list_doctors(
    db: Session,
    page: int,
    size: int,
    q: str | None = None,
    activo: bool | None = None,
    especialidad_id: int | None = None,
) -> dict:
    stmt = select(Medico).join(Medico.usuario)
    if q:
        pattern = like(q)
        stmt = stmt.where(
            or_(
                Medico.nombres.ilike(pattern),
                Medico.apellidos.ilike(pattern),
                Medico.registro_profesional.ilike(pattern),
                Usuario.email.ilike(pattern),
            )
        )
    if activo is not None:
        stmt = stmt.where(Usuario.activo.is_(activo))
    if especialidad_id:
        stmt = stmt.where(Medico.especialidades.any(Especialidad.id == especialidad_id))
    stmt = stmt.order_by(Medico.apellidos, Medico.nombres)
    return paginate(db, stmt, page, size)


def create_doctor(db: Session, admin: Usuario, data: MedicoCreate) -> Medico:
    if user_repo.email_exists(db, data.email):
        raise conflict("Ya existe una cuenta con ese correo electrónico")
    if user_repo.registro_exists(db, data.registro_profesional):
        raise conflict("Ya existe un médico con ese identificador profesional")
    especialidades = _load_specialties(db, data.especialidad_ids)
    user = Usuario(email=data.email, password_hash=hash_password(data.password), rol=ROL_MEDICO, activo=True)
    db.add(user)
    db.flush()
    medico = Medico(
        usuario_id=user.id,
        nombres=data.nombres,
        apellidos=data.apellidos,
        telefono=data.telefono,
        registro_profesional=data.registro_profesional,
        especialidades=especialidades,
    )
    db.add(medico)
    db.flush()
    audit_service.log(db, admin.id, "crear", "medico", medico.id)
    db.commit()
    db.refresh(medico)
    return medico


def update_doctor(db: Session, admin: Usuario, medico_id: int, data: MedicoUpdate) -> Medico:
    medico = get_or_404(db, Medico, medico_id, "Médico no encontrado")
    if user_repo.email_exists(db, data.email, exclude_user_id=medico.usuario_id):
        raise conflict("Ya existe una cuenta con ese correo electrónico")
    if user_repo.registro_exists(db, data.registro_profesional, exclude_medico_id=medico.id):
        raise conflict("Ya existe un médico con ese identificador profesional")
    medico.nombres = data.nombres
    medico.apellidos = data.apellidos
    medico.telefono = data.telefono
    medico.registro_profesional = data.registro_profesional
    medico.especialidades = _load_specialties(db, data.especialidad_ids)
    medico.usuario.email = data.email
    audit_service.log(db, admin.id, "actualizar", "medico", medico.id)
    db.commit()
    db.refresh(medico)
    return medico


def set_status(db: Session, admin: Usuario, medico_id: int, activo: bool) -> Medico:
    medico = get_or_404(db, Medico, medico_id, "Médico no encontrado")
    if not activo:
        ahora = now_local()
        futuras = db.scalar(
            select(Cita.id)
            .where(
                Cita.medico_id == medico.id,
                Cita.estado.in_(ESTADOS_CITA_PROGRAMADAS),
                Cita.fecha >= ahora.date(),
            )
            .limit(1)
        )
        if futuras:
            raise conflict(
                "El médico tiene citas activas programadas. Cancélelas o reprográmelas antes de desactivarlo."
            )
    medico.usuario.activo = activo
    audit_service.log(db, admin.id, "activar" if activo else "desactivar", "medico", medico.id)
    db.commit()
    db.refresh(medico)
    return medico
