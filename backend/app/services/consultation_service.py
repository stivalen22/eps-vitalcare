"""Consultas simuladas asociadas a citas.

No se generan diagnósticos, recetas ni recomendaciones automáticas. El administrador
NO tiene acceso al contenido de las consultas por el solo hecho de su rol.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import CITA_ATENDIDA, CITA_CONFIRMADA, CITA_EN_ATENCION, ROL_MEDICO, ROL_PACIENTE
from app.core.errors import conflict, forbidden, not_found
from app.core.timeutils import now_local
from app.models import Cita, Consulta, Usuario
from app.repositories.base import paginate
from app.schemas.agenda import ConsultaCreate
from app.services import audit_service, notification_service

ADMIN_SIN_ACCESO = "Por privacidad, el administrador no tiene acceso al contenido de las consultas"


def _scoped_query(user: Usuario):
    stmt = select(Consulta).join(Consulta.cita)
    if user.rol == ROL_PACIENTE:
        return stmt.where(Cita.paciente_id == (user.paciente.id if user.paciente else -1))
    if user.rol == ROL_MEDICO:
        return stmt.where(Cita.medico_id == (user.medico.id if user.medico else -1))
    raise forbidden(ADMIN_SIN_ACCESO)


def list_consultations(
    db: Session, user: Usuario, page: int, size: int, paciente_id: int | None = None, cita_id: int | None = None
) -> dict:
    stmt = _scoped_query(user)
    if cita_id:
        stmt = stmt.where(Consulta.cita_id == cita_id)
    if paciente_id and user.rol == ROL_MEDICO:
        stmt = stmt.where(Cita.paciente_id == paciente_id)
    stmt = stmt.order_by(Cita.fecha.desc(), Consulta.id.desc())
    return paginate(db, stmt, page, size)


def get_consultation(db: Session, user: Usuario, consulta_id: int) -> Consulta:
    stmt = _scoped_query(user).where(Consulta.id == consulta_id)
    consulta = db.scalar(stmt)
    if consulta is None:
        # Si existe pero no le pertenece, se informa 403; si no existe, 404
        if db.get(Consulta, consulta_id) is None:
            raise not_found("Consulta no encontrada")
        raise forbidden("No tiene acceso a esta consulta")
    return consulta


def create_consultation(db: Session, user: Usuario, data: ConsultaCreate) -> Consulta:
    if user.rol != ROL_MEDICO or user.medico is None:
        raise forbidden("Solo el médico asignado puede registrar la consulta")
    cita = db.get(Cita, data.cita_id)
    if cita is None:
        raise not_found("Cita no encontrada")
    if cita.medico_id != user.medico.id:
        raise forbidden("Solo puede registrar consultas de sus propias citas")
    if cita.estado not in (CITA_CONFIRMADA, CITA_EN_ATENCION, CITA_ATENDIDA):
        raise conflict("La cita debe estar confirmada, en atención o atendida para registrar la consulta")
    if cita.fecha > now_local().date():
        raise conflict("No se puede registrar la consulta antes de la fecha de la cita")
    if cita.consulta is not None:
        raise conflict("Esta cita ya tiene una consulta registrada")

    consulta = Consulta(cita_id=cita.id, resumen=data.resumen.strip(), observaciones=data.observaciones)
    db.add(consulta)
    cita.estado = CITA_ATENDIDA
    db.flush()
    notification_service.notify(
        db, cita.paciente.usuario_id, "Consulta registrada",
        f"Se registró la consulta de tu cita de {cita.servicio.nombre} del {cita.fecha.strftime('%d/%m/%Y')}.",
        "consulta",
    )
    audit_service.log(db, user.id, "crear", "consulta", consulta.id)
    db.commit()
    db.refresh(consulta)
    return consulta
