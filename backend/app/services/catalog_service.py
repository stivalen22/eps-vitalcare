"""Especialidades y servicios médicos."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import conflict, invalid
from app.models import Especialidad, Medico, ServicioMedico, Usuario
from app.repositories.base import get_or_404, like, paginate
from app.schemas.catalogo import EspecialidadCreate, EspecialidadUpdate, ServicioCreate, ServicioUpdate
from app.services import audit_service


# ---------- Especialidades ----------
def _specialty_name_taken(db: Session, nombre: str, exclude_id: int | None = None) -> bool:
    stmt = select(Especialidad.id).where(func.lower(Especialidad.nombre) == nombre.lower())
    if exclude_id:
        stmt = stmt.where(Especialidad.id != exclude_id)
    return db.scalar(stmt) is not None


def list_specialties(db: Session, q: str | None = None, activo: bool | None = None) -> list[Especialidad]:
    stmt = select(Especialidad)
    if q:
        stmt = stmt.where(Especialidad.nombre.ilike(like(q)))
    if activo is not None:
        stmt = stmt.where(Especialidad.activo.is_(activo))
    return list(db.scalars(stmt.order_by(Especialidad.nombre)).all())


def create_specialty(db: Session, admin: Usuario, data: EspecialidadCreate) -> Especialidad:
    if _specialty_name_taken(db, data.nombre):
        raise conflict("Ya existe una especialidad con ese nombre")
    esp = Especialidad(nombre=data.nombre, descripcion=data.descripcion, activo=True)
    db.add(esp)
    db.flush()
    audit_service.log(db, admin.id, "crear", "especialidad", esp.id)
    db.commit()
    db.refresh(esp)
    return esp


def update_specialty(db: Session, admin: Usuario, esp_id: int, data: EspecialidadUpdate) -> Especialidad:
    esp = get_or_404(db, Especialidad, esp_id, "Especialidad no encontrada")
    if _specialty_name_taken(db, data.nombre, exclude_id=esp.id):
        raise conflict("Ya existe una especialidad con ese nombre")
    esp.nombre = data.nombre
    esp.descripcion = data.descripcion
    audit_service.log(db, admin.id, "actualizar", "especialidad", esp.id)
    db.commit()
    db.refresh(esp)
    return esp


def set_specialty_status(db: Session, admin: Usuario, esp_id: int, activo: bool) -> Especialidad:
    esp = get_or_404(db, Especialidad, esp_id, "Especialidad no encontrada")
    if not activo:
        servicios_activos = db.scalar(
            select(func.count(ServicioMedico.id)).where(
                ServicioMedico.especialidad_id == esp.id, ServicioMedico.activo.is_(True)
            )
        )
        if servicios_activos:
            raise conflict("La especialidad tiene servicios activos. Desactívelos primero.")
    esp.activo = activo
    audit_service.log(db, admin.id, "activar" if activo else "desactivar", "especialidad", esp.id)
    db.commit()
    db.refresh(esp)
    return esp


# ---------- Servicios ----------
def _service_name_taken(db: Session, nombre: str, exclude_id: int | None = None) -> bool:
    stmt = select(ServicioMedico.id).where(func.lower(ServicioMedico.nombre) == nombre.lower())
    if exclude_id:
        stmt = stmt.where(ServicioMedico.id != exclude_id)
    return db.scalar(stmt) is not None


def _check_specialty(db: Session, especialidad_id: int) -> None:
    esp = db.get(Especialidad, especialidad_id)
    if esp is None:
        raise invalid("La especialidad indicada no existe")
    if not esp.activo:
        raise invalid("La especialidad indicada está inactiva")


def list_services(
    db: Session,
    page: int,
    size: int,
    q: str | None = None,
    activo: bool | None = None,
    especialidad_id: int | None = None,
) -> dict:
    stmt = select(ServicioMedico)
    if q:
        pattern = like(q)
        stmt = stmt.where(or_(ServicioMedico.nombre.ilike(pattern), ServicioMedico.descripcion.ilike(pattern)))
    if activo is not None:
        stmt = stmt.where(ServicioMedico.activo.is_(activo))
    if especialidad_id:
        stmt = stmt.where(ServicioMedico.especialidad_id == especialidad_id)
    return paginate(db, stmt.order_by(ServicioMedico.nombre), page, size)


def create_service(db: Session, admin: Usuario, data: ServicioCreate) -> ServicioMedico:
    if _service_name_taken(db, data.nombre):
        raise conflict("Ya existe un servicio con ese nombre")
    _check_specialty(db, data.especialidad_id)
    servicio = ServicioMedico(**data.model_dump(), activo=True)
    db.add(servicio)
    db.flush()
    audit_service.log(db, admin.id, "crear", "servicio", servicio.id)
    db.commit()
    db.refresh(servicio)
    return servicio


def update_service(db: Session, admin: Usuario, servicio_id: int, data: ServicioUpdate) -> ServicioMedico:
    servicio = get_or_404(db, ServicioMedico, servicio_id, "Servicio no encontrado")
    if _service_name_taken(db, data.nombre, exclude_id=servicio.id):
        raise conflict("Ya existe un servicio con ese nombre")
    _check_specialty(db, data.especialidad_id)
    for field, value in data.model_dump().items():
        setattr(servicio, field, value)
    audit_service.log(db, admin.id, "actualizar", "servicio", servicio.id)
    db.commit()
    db.refresh(servicio)
    return servicio


def set_service_status(db: Session, admin: Usuario, servicio_id: int, activo: bool) -> ServicioMedico:
    """Desactivación lógica: los servicios con historial nunca se eliminan."""
    servicio = get_or_404(db, ServicioMedico, servicio_id, "Servicio no encontrado")
    if activo:
        _check_specialty(db, servicio.especialidad_id)
    servicio.activo = activo
    audit_service.log(db, admin.id, "activar" if activo else "desactivar", "servicio", servicio.id)
    db.commit()
    db.refresh(servicio)
    return servicio


def doctors_for_service(db: Session, servicio_id: int) -> list[Medico]:
    """Médicos activos que tienen la especialidad del servicio."""
    servicio = get_or_404(db, ServicioMedico, servicio_id, "Servicio no encontrado")
    stmt = (
        select(Medico)
        .join(Medico.usuario)
        .where(Usuario.activo.is_(True), Medico.especialidades.any(Especialidad.id == servicio.especialidad_id))
        .order_by(Medico.apellidos)
    )
    return list(db.scalars(stmt).unique().all())
