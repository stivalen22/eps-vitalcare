"""Citas médicas: reglas de negocio de agenda, estados y permisos.

Todas las reglas se validan en el backend antes de guardar, aunque el frontend
también las verifique para mejorar la experiencia de usuario.
"""
from datetime import date, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.constants import (
    CITA_ATENDIDA,
    CITA_CANCELADA,
    CITA_CONFIRMADA,
    CITA_EN_ATENCION,
    CITA_PENDIENTE,
    ROL_ADMIN,
    ROL_MEDICO,
    ROL_PACIENTE,
    TRANSICIONES_CITA,
)
from app.core.errors import conflict, forbidden, invalid, not_found
from app.core.timeutils import add_minutes, now_local
from app.models import Cita, Medico, Paciente, ServicioMedico, Usuario
from app.repositories.base import like, paginate
from app.schemas.agenda import CitaCreate, CitaUpdate
from app.services import audit_service, notification_service, schedule_service

ESTADO_LEGIBLE = {
    CITA_PENDIENTE: "pendiente",
    CITA_CONFIRMADA: "confirmada",
    CITA_EN_ATENCION: "en atención",
    CITA_ATENDIDA: "atendida",
    CITA_CANCELADA: "cancelada",
}


def _fmt(cita: Cita) -> str:
    return f"{cita.fecha.strftime('%d/%m/%Y')} a las {cita.hora_inicio.strftime('%H:%M')}"


# ---------- Acceso ----------
def _scope(stmt, user: Usuario):
    """Restringe una consulta de citas según el rol del usuario."""
    if user.rol == ROL_PACIENTE:
        return stmt.where(Cita.paciente_id == (user.paciente.id if user.paciente else -1))
    if user.rol == ROL_MEDICO:
        return stmt.where(Cita.medico_id == (user.medico.id if user.medico else -1))
    return stmt


def get_for_user(db: Session, user: Usuario, cita_id: int) -> Cita:
    cita = db.get(Cita, cita_id)
    if cita is None:
        raise not_found("Cita no encontrada")
    if user.rol == ROL_ADMIN:
        return cita
    if user.rol == ROL_PACIENTE and user.paciente and cita.paciente_id == user.paciente.id:
        return cita
    if user.rol == ROL_MEDICO and user.medico and cita.medico_id == user.medico.id:
        return cita
    raise forbidden("No tiene acceso a esta cita")


def list_appointments(
    db: Session,
    user: Usuario,
    page: int,
    size: int,
    estado: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    medico_id: int | None = None,
    paciente_id: int | None = None,
    servicio_id: int | None = None,
    q: str | None = None,
    orden: str = "desc",
) -> dict:
    stmt = select(Cita).join(Cita.paciente).join(Cita.medico).join(Cita.servicio)
    stmt = _scope(stmt, user)
    if estado:
        stmt = stmt.where(Cita.estado == estado)
    if fecha_desde:
        stmt = stmt.where(Cita.fecha >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(Cita.fecha <= fecha_hasta)
    if medico_id:
        stmt = stmt.where(Cita.medico_id == medico_id)
    if paciente_id:
        stmt = stmt.where(Cita.paciente_id == paciente_id)
    if servicio_id:
        stmt = stmt.where(Cita.servicio_id == servicio_id)
    if q:
        pattern = like(q)
        stmt = stmt.where(
            or_(
                Paciente.nombres.ilike(pattern),
                Paciente.apellidos.ilike(pattern),
                Paciente.numero_documento.ilike(pattern),
                Medico.nombres.ilike(pattern),
                Medico.apellidos.ilike(pattern),
                ServicioMedico.nombre.ilike(pattern),
            )
        )
    if orden == "asc":
        stmt = stmt.order_by(Cita.fecha.asc(), Cita.hora_inicio.asc())
    else:
        stmt = stmt.order_by(Cita.fecha.desc(), Cita.hora_inicio.desc())
    return paginate(db, stmt, page, size)


# ---------- Validación de agenda ----------
def _validate_slot(
    db: Session,
    *,
    medico: Medico,
    servicio: ServicioMedico,
    paciente: Paciente,
    fecha: date,
    hora_inicio,
    exclude_id: int | None = None,
):
    """Comprueba todas las reglas de disponibilidad. Devuelve la hora de finalización."""
    if not paciente.activo:
        raise conflict("La cuenta del paciente está desactivada")
    if not medico.activo:
        raise conflict("El médico seleccionado no está activo")
    if not servicio.activo:
        raise conflict("El servicio seleccionado no está activo")
    if servicio.especialidad_id not in {e.id for e in medico.especialidades}:
        raise conflict("El médico seleccionado no presta este servicio")

    if datetime.combine(fecha, hora_inicio) <= now_local():
        raise invalid("La cita debe programarse en una fecha y hora futuras")

    hora_fin = add_minutes(hora_inicio, servicio.duracion_minutos)
    if hora_fin is None:
        raise conflict("El horario solicitado está fuera de la disponibilidad del médico")

    if schedule_service.find_schedule_for(db, medico.id, fecha, hora_inicio, hora_fin) is None:
        raise conflict("El horario solicitado está fuera de la disponibilidad del médico")

    for ini, fin in schedule_service.busy_intervals(db, fecha, medico_id=medico.id, exclude_id=exclude_id):
        if hora_inicio < fin and hora_fin > ini:
            raise conflict("El médico ya tiene una cita en ese horario. Elija otro espacio disponible.")
    for ini, fin in schedule_service.busy_intervals(db, fecha, paciente_id=paciente.id, exclude_id=exclude_id):
        if hora_inicio < fin and hora_fin > ini:
            raise conflict("El paciente ya tiene otra cita que se cruza con ese horario")
    return hora_fin


def _lock_medico(db: Session, medico_id: int) -> Medico:
    """Bloquea la fila del médico (en PostgreSQL) para evitar reservas simultáneas del mismo espacio."""
    medico = db.scalar(select(Medico).where(Medico.id == medico_id).with_for_update(of=Medico))
    if medico is None:
        raise not_found("Médico no encontrado")
    return medico


# ---------- Operaciones ----------
def create_appointment(db: Session, user: Usuario, data: CitaCreate) -> Cita:
    if user.rol == ROL_PACIENTE:
        if user.paciente is None:
            raise forbidden()
        paciente = user.paciente
    elif user.rol == ROL_ADMIN:
        if data.paciente_id is None:
            raise invalid("Debe indicar el paciente (paciente_id)")
        paciente = db.get(Paciente, data.paciente_id)
        if paciente is None:
            raise not_found("Paciente no encontrado")
    else:
        raise forbidden("Los médicos no pueden solicitar citas")

    servicio = db.get(ServicioMedico, data.servicio_id)
    if servicio is None:
        raise not_found("Servicio no encontrado")
    medico = _lock_medico(db, data.medico_id)

    hora_fin = _validate_slot(
        db, medico=medico, servicio=servicio, paciente=paciente, fecha=data.fecha, hora_inicio=data.hora_inicio
    )
    cita = Cita(
        paciente_id=paciente.id,
        medico_id=medico.id,
        servicio_id=servicio.id,
        fecha=data.fecha,
        hora_inicio=data.hora_inicio,
        hora_fin=hora_fin,
        motivo=data.motivo,
        estado=CITA_PENDIENTE,
    )
    db.add(cita)
    db.flush()
    cuando = _fmt(cita)
    notification_service.notify(
        db, paciente.usuario_id, "Cita solicitada",
        f"Tu cita de {servicio.nombre} con {medico.nombre_completo} quedó registrada para el {cuando}.", "cita",
    )
    notification_service.notify(
        db, medico.usuario_id, "Nueva cita asignada",
        f"Se asignó una cita de {servicio.nombre} con {paciente.nombre_completo} el {cuando}.", "cita",
    )
    audit_service.log(db, user.id, "crear", "cita", cita.id)
    db.commit()
    db.refresh(cita)
    return cita


def update_appointment(db: Session, user: Usuario, cita_id: int, data: CitaUpdate) -> Cita:
    cita = get_for_user(db, user, cita_id)
    if user.rol == ROL_MEDICO:
        raise forbidden("El médico no puede reprogramar citas")
    if cita.estado not in (CITA_PENDIENTE, CITA_CONFIRMADA):
        raise conflict("Solo se pueden reprogramar citas pendientes o confirmadas")

    medico = _lock_medico(db, data.medico_id)
    hora_fin = _validate_slot(
        db,
        medico=medico,
        servicio=cita.servicio,
        paciente=cita.paciente,
        fecha=data.fecha,
        hora_inicio=data.hora_inicio,
        exclude_id=cita.id,
    )
    cambio_agenda = (medico.id, data.fecha, data.hora_inicio) != (cita.medico_id, cita.fecha, cita.hora_inicio)
    medico_anterior_usuario = cita.medico.usuario_id
    cita.medico_id = medico.id
    cita.fecha = data.fecha
    cita.hora_inicio = data.hora_inicio
    cita.hora_fin = hora_fin
    cita.motivo = data.motivo.strip()
    if cambio_agenda:
        cita.estado = CITA_PENDIENTE  # una cita reprogramada debe confirmarse de nuevo
        db.flush()
        db.refresh(cita)
        msg = f"La cita de {cita.servicio.nombre} fue reprogramada para el {_fmt(cita)}."
        notification_service.notify(db, cita.paciente.usuario_id, "Cita reprogramada", msg, "cita")
        notification_service.notify(db, medico.usuario_id, "Cita reprogramada", msg, "cita")
        if medico_anterior_usuario != medico.usuario_id:
            notification_service.notify(
                db, medico_anterior_usuario, "Cita reasignada", "Una de sus citas fue reasignada a otro médico.", "cita"
            )
    audit_service.log(db, user.id, "actualizar", "cita", cita.id)
    db.commit()
    db.refresh(cita)
    return cita


def change_status(db: Session, user: Usuario, cita_id: int, nuevo: str) -> Cita:
    cita = get_for_user(db, user, cita_id)
    if nuevo == CITA_CANCELADA:
        return cancel_appointment(db, user, cita_id, None)
    if user.rol == ROL_PACIENTE:
        raise forbidden("El paciente solo puede cancelar sus citas")
    if nuevo not in TRANSICIONES_CITA.get(cita.estado, set()):
        raise conflict(
            f"No se puede pasar una cita de '{ESTADO_LEGIBLE[cita.estado]}' a '{ESTADO_LEGIBLE.get(nuevo, nuevo)}'"
        )
    if nuevo in (CITA_EN_ATENCION, CITA_ATENDIDA) and cita.fecha > now_local().date():
        raise conflict("Una cita solo puede iniciarse o marcarse como atendida el día programado o después")

    anterior = cita.estado
    cita.estado = nuevo
    if nuevo == CITA_CONFIRMADA:
        notification_service.notify(
            db, cita.paciente.usuario_id, "Cita confirmada",
            f"Tu cita de {cita.servicio.nombre} del {_fmt(cita)} fue confirmada.", "cita",
        )
    elif nuevo == CITA_ATENDIDA:
        notification_service.notify(
            db, cita.paciente.usuario_id, "Cita atendida",
            f"Tu cita de {cita.servicio.nombre} del {_fmt(cita)} fue marcada como atendida.", "cita",
        )
    audit_service.log(db, user.id, "cambiar_estado", "cita", cita.id, detalle=f"{anterior} -> {nuevo}")
    db.commit()
    db.refresh(cita)
    return cita


def cancel_appointment(db: Session, user: Usuario, cita_id: int, motivo: str | None) -> Cita:
    """La cancelación conserva el registro como parte del historial (no se elimina)."""
    cita = get_for_user(db, user, cita_id)
    if cita.estado not in (CITA_PENDIENTE, CITA_CONFIRMADA):
        raise conflict("Solo se pueden cancelar citas pendientes o confirmadas")
    if user.rol == ROL_PACIENTE and datetime.combine(cita.fecha, cita.hora_inicio) <= now_local():
        raise conflict("No se puede cancelar una cita cuya hora ya pasó")

    cita.estado = CITA_CANCELADA
    cita.cancelado_por_id = user.id
    cita.motivo_cancelacion = motivo or f"Cancelada por {'el paciente' if user.rol == ROL_PACIENTE else user.rol}"
    texto = f"La cita de {cita.servicio.nombre} del {_fmt(cita)} fue cancelada."
    if user.rol != ROL_PACIENTE:
        notification_service.notify(db, cita.paciente.usuario_id, "Cita cancelada", texto, "cita")
    if user.rol != ROL_MEDICO:
        notification_service.notify(db, cita.medico.usuario_id, "Cita cancelada", texto, "cita")
    audit_service.log(db, user.id, "cancelar", "cita", cita.id)
    db.commit()
    db.refresh(cita)
    return cita
