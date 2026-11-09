"""Gestión de pacientes (CRUD administrativo)."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.constants import ROL_ADMIN, ROL_MEDICO, ROL_PACIENTE
from app.core.errors import conflict, forbidden, not_found
from app.core.security import hash_password
from app.models import Cita, Paciente, Usuario
from app.repositories import usuarios as user_repo
from app.repositories.base import get_or_404, like, paginate
from app.schemas.persona import PacienteCreate, PacienteUpdate
from app.services import audit_service


def list_patients(db: Session, page: int, size: int, q: str | None = None, activo: bool | None = None) -> dict:
    stmt = select(Paciente).join(Paciente.usuario)
    if q:
        pattern = like(q)
        stmt = stmt.where(
            or_(
                Paciente.nombres.ilike(pattern),
                Paciente.apellidos.ilike(pattern),
                Paciente.numero_documento.ilike(pattern),
                Usuario.email.ilike(pattern),
            )
        )
    if activo is not None:
        stmt = stmt.where(Usuario.activo.is_(activo))
    stmt = stmt.order_by(Paciente.apellidos, Paciente.nombres)
    return paginate(db, stmt, page, size)


def get_patient_for(db: Session, user: Usuario, paciente_id: int) -> Paciente:
    """Aplica las reglas de acceso al detalle de un paciente."""
    paciente = db.get(Paciente, paciente_id)
    if paciente is None:
        raise not_found("Paciente no encontrado")
    if user.rol == ROL_ADMIN:
        return paciente
    if user.rol == ROL_PACIENTE:
        if user.paciente and user.paciente.id == paciente_id:
            return paciente
        raise forbidden("Solo puede consultar su propia información")
    if user.rol == ROL_MEDICO and user.medico:
        tiene_cita = db.scalar(
            select(Cita.id).where(Cita.paciente_id == paciente_id, Cita.medico_id == user.medico.id).limit(1)
        )
        if tiene_cita:
            return paciente
    raise forbidden("Solo puede consultar pacientes que tengan citas asignadas a usted")


def create_patient(db: Session, admin: Usuario, data: PacienteCreate) -> Paciente:
    if user_repo.email_exists(db, data.email):
        raise conflict("Ya existe una cuenta con ese correo electrónico")
    if user_repo.documento_exists(db, data.numero_documento):
        raise conflict("Ya existe un paciente con ese número de documento")
    user = Usuario(email=data.email, password_hash=hash_password(data.password), rol=ROL_PACIENTE, activo=True)
    db.add(user)
    db.flush()
    paciente = Paciente(
        usuario_id=user.id,
        **data.model_dump(exclude={"email", "password"}),
    )
    db.add(paciente)
    db.flush()
    audit_service.log(db, admin.id, "crear", "paciente", paciente.id)
    db.commit()
    db.refresh(paciente)
    return paciente


def update_patient(db: Session, admin: Usuario, paciente_id: int, data: PacienteUpdate) -> Paciente:
    paciente = get_or_404(db, Paciente, paciente_id, "Paciente no encontrado")
    if user_repo.email_exists(db, data.email, exclude_user_id=paciente.usuario_id):
        raise conflict("Ya existe una cuenta con ese correo electrónico")
    if user_repo.documento_exists(db, data.numero_documento, exclude_paciente_id=paciente.id):
        raise conflict("Ya existe un paciente con ese número de documento")
    for field, value in data.model_dump(exclude={"email"}).items():
        setattr(paciente, field, value)
    paciente.usuario.email = data.email
    audit_service.log(db, admin.id, "actualizar", "paciente", paciente.id)
    db.commit()
    db.refresh(paciente)
    return paciente


def set_status(db: Session, admin: Usuario, paciente_id: int, activo: bool) -> Paciente:
    paciente = get_or_404(db, Paciente, paciente_id, "Paciente no encontrado")
    if paciente.usuario_id == admin.id and not activo:
        raise conflict("No puede desactivar su propia cuenta")
    paciente.usuario.activo = activo
    audit_service.log(db, admin.id, "activar" if activo else "desactivar", "paciente", paciente.id)
    db.commit()
    db.refresh(paciente)
    return paciente
