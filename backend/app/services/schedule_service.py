"""Horarios de disponibilidad y cálculo de espacios libres."""
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import ESTADOS_CITA_OCUPAN, ESTADOS_CITA_PROGRAMADAS, ROL_ADMIN, ROL_MEDICO
from app.core.errors import conflict, forbidden, invalid, not_found
from app.core.timeutils import add_minutes, now_local
from app.models import Cita, HorarioMedico, Medico, ServicioMedico, Usuario
from app.repositories.base import get_or_404
from app.schemas.agenda import HorarioCreate, HorarioUpdate
from app.services import audit_service


def _resolve_medico_id(user: Usuario, requested: int | None) -> int:
    """El médico solo gestiona su propio horario; el administrador debe indicar el médico."""
    if user.rol == ROL_MEDICO:
        if user.medico is None:
            raise forbidden()
        if requested is not None and requested != user.medico.id:
            raise forbidden("Solo puede gestionar su propia disponibilidad")
        return user.medico.id
    if requested is None:
        raise invalid("Debe indicar el médico (medico_id)")
    return requested


def _check_owner(user: Usuario, horario: HorarioMedico) -> None:
    if user.rol == ROL_ADMIN:
        return
    if user.rol == ROL_MEDICO and user.medico and horario.medico_id == user.medico.id:
        return
    raise forbidden("Solo puede gestionar su propia disponibilidad")


def _check_overlap(
    db: Session, medico_id: int, dia: int, inicio: time, fin: time, exclude_id: int | None = None
) -> None:
    stmt = select(HorarioMedico.id).where(
        HorarioMedico.medico_id == medico_id,
        HorarioMedico.dia_semana == dia,
        HorarioMedico.activo.is_(True),
        HorarioMedico.hora_inicio < fin,
        HorarioMedico.hora_fin > inicio,
    )
    if exclude_id:
        stmt = stmt.where(HorarioMedico.id != exclude_id)
    if db.scalar(stmt.limit(1)):
        raise conflict("El horario se superpone con otra franja activa del mismo médico ese día")


def _future_citas_in(db: Session, horario: HorarioMedico) -> list[Cita]:
    """Citas futuras programadas que dependen de esta franja."""
    hoy = now_local().date()
    citas = db.scalars(
        select(Cita).where(
            Cita.medico_id == horario.medico_id,
            Cita.fecha >= hoy,
            Cita.estado.in_(ESTADOS_CITA_PROGRAMADAS),
        )
    ).all()
    return [
        c
        for c in citas
        if c.fecha.weekday() == horario.dia_semana
        and horario.hora_inicio <= c.hora_inicio
        and c.hora_fin <= horario.hora_fin
    ]


def list_schedules(db: Session, user: Usuario, medico_id: int | None = None) -> list[HorarioMedico]:
    stmt = select(HorarioMedico)
    if user.rol == ROL_MEDICO:
        stmt = stmt.where(HorarioMedico.medico_id == (user.medico.id if user.medico else -1))
    elif medico_id:
        stmt = stmt.where(HorarioMedico.medico_id == medico_id)
    stmt = stmt.order_by(HorarioMedico.medico_id, HorarioMedico.dia_semana, HorarioMedico.hora_inicio)
    return list(db.scalars(stmt).unique().all())


def create_schedule(db: Session, user: Usuario, data: HorarioCreate) -> HorarioMedico:
    medico_id = _resolve_medico_id(user, data.medico_id)
    if db.get(Medico, medico_id) is None:
        raise not_found("Médico no encontrado")
    if data.activo:
        _check_overlap(db, medico_id, data.dia_semana, data.hora_inicio, data.hora_fin)
    horario = HorarioMedico(
        medico_id=medico_id,
        dia_semana=data.dia_semana,
        hora_inicio=data.hora_inicio,
        hora_fin=data.hora_fin,
        duracion_cita_minutos=data.duracion_cita_minutos,
        activo=data.activo,
    )
    db.add(horario)
    db.flush()
    audit_service.log(db, user.id, "crear", "horario", horario.id)
    db.commit()
    db.refresh(horario)
    return horario


def update_schedule(db: Session, user: Usuario, horario_id: int, data: HorarioUpdate) -> HorarioMedico:
    horario = get_or_404(db, HorarioMedico, horario_id, "Horario no encontrado")
    _check_owner(user, horario)
    if data.activo:
        _check_overlap(db, horario.medico_id, data.dia_semana, data.hora_inicio, data.hora_fin, exclude_id=horario.id)

    # Las citas futuras de la franja anterior deben seguir cubiertas por la nueva franja
    nuevo = HorarioMedico(
        medico_id=horario.medico_id,
        dia_semana=data.dia_semana,
        hora_inicio=data.hora_inicio,
        hora_fin=data.hora_fin,
    )
    afectadas = [
        c
        for c in _future_citas_in(db, horario)
        if not data.activo
        or not (
            c.fecha.weekday() == nuevo.dia_semana
            and nuevo.hora_inicio <= c.hora_inicio
            and c.hora_fin <= nuevo.hora_fin
        )
    ]
    if afectadas:
        raise conflict(
            f"El cambio dejaría {len(afectadas)} cita(s) programada(s) fuera de horario. Reprográmelas primero."
        )
    horario.dia_semana = data.dia_semana
    horario.hora_inicio = data.hora_inicio
    horario.hora_fin = data.hora_fin
    horario.duracion_cita_minutos = data.duracion_cita_minutos
    horario.activo = data.activo
    audit_service.log(db, user.id, "actualizar", "horario", horario.id)
    db.commit()
    db.refresh(horario)
    return horario


def delete_schedule(db: Session, user: Usuario, horario_id: int) -> None:
    horario = get_or_404(db, HorarioMedico, horario_id, "Horario no encontrado")
    _check_owner(user, horario)
    if _future_citas_in(db, horario):
        raise conflict("No se puede eliminar: existen citas programadas en esta franja")
    audit_service.log(db, user.id, "eliminar", "horario", horario.id)
    db.delete(horario)
    db.commit()


def find_schedule_for(db: Session, medico_id: int, fecha: date, inicio: time, fin: time) -> HorarioMedico | None:
    """Devuelve la franja activa que contiene completamente el intervalo, si existe."""
    return db.scalar(
        select(HorarioMedico).where(
            HorarioMedico.medico_id == medico_id,
            HorarioMedico.dia_semana == fecha.weekday(),
            HorarioMedico.activo.is_(True),
            HorarioMedico.hora_inicio <= inicio,
            HorarioMedico.hora_fin >= fin,
        ).limit(1)
    )


def busy_intervals(
    db: Session, fecha: date, medico_id: int | None = None, paciente_id: int | None = None, exclude_id: int | None = None
) -> list[tuple[time, time]]:
    stmt = select(Cita.hora_inicio, Cita.hora_fin).where(Cita.fecha == fecha, Cita.estado.in_(ESTADOS_CITA_OCUPAN))
    if medico_id is not None:
        stmt = stmt.where(Cita.medico_id == medico_id)
    if paciente_id is not None:
        stmt = stmt.where(Cita.paciente_id == paciente_id)
    if exclude_id is not None:
        stmt = stmt.where(Cita.id != exclude_id)
    return [(r[0], r[1]) for r in db.execute(stmt).all()]


def available_slots(db: Session, medico_id: int, servicio_id: int, fecha: date) -> list[dict]:
    medico = db.get(Medico, medico_id)
    if medico is None:
        raise not_found("Médico no encontrado")
    servicio = db.get(ServicioMedico, servicio_id)
    if servicio is None:
        raise not_found("Servicio no encontrado")
    if not medico.activo or not servicio.activo:
        return []
    if servicio.especialidad_id not in {e.id for e in medico.especialidades}:
        return []

    ahora = now_local()
    ocupados = busy_intervals(db, fecha, medico_id=medico_id)
    horarios = db.scalars(
        select(HorarioMedico).where(
            HorarioMedico.medico_id == medico_id,
            HorarioMedico.dia_semana == fecha.weekday(),
            HorarioMedico.activo.is_(True),
        )
    ).all()

    slots: dict[time, time] = {}
    for h in horarios:
        inicio = h.hora_inicio
        while True:
            fin = add_minutes(inicio, servicio.duracion_minutos)
            if fin is None or fin > h.hora_fin:
                break
            en_futuro = datetime.combine(fecha, inicio) > ahora
            libre = all(not (inicio < o_fin and fin > o_ini) for o_ini, o_fin in ocupados)
            if en_futuro and libre:
                slots[inicio] = fin
            siguiente = add_minutes(inicio, h.duracion_cita_minutos)
            if siguiente is None:
                break
            inicio = siguiente
    return [{"hora_inicio": k, "hora_fin": slots[k]} for k in sorted(slots)]


def week_range(fecha: date) -> tuple[date, date]:
    lunes = fecha - timedelta(days=fecha.weekday())
    return lunes, lunes + timedelta(days=6)
