"""Estadísticas del panel principal. Todas se calculan desde la base de datos."""
from collections import Counter
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import (
    AUT_EN_REVISION,
    AUT_PENDIENTE,
    CITA_CONFIRMADA,
    CITA_EN_ATENCION,
    CITA_PENDIENTE,
    ESTADOS_CITA,
    ESTADOS_CITA_PROGRAMADAS,
    ROL_ADMIN,
    ROL_MEDICO,
    ROL_PACIENTE,
)
from app.core.timeutils import now_local
from app.models import Cita, Medico, Notificacion, Paciente, SolicitudAutorizacion, Usuario
from app.schemas.agenda import CitaOut

MESES = ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")


def _out(citas) -> list[dict]:
    return [CitaOut.model_validate(c).model_dump(mode="json") for c in citas]


def _count(db: Session, stmt) -> int:
    return db.scalar(stmt) or 0


def _unread(db: Session, user: Usuario) -> int:
    return _count(
        db,
        select(func.count(Notificacion.id)).where(Notificacion.usuario_id == user.id, Notificacion.leida.is_(False)),
    )


def _upcoming_stmt(where_clause, ahora):
    hoy = ahora.date()
    return (
        select(Cita)
        .where(where_clause, Cita.estado.in_(ESTADOS_CITA_PROGRAMADAS))
        .where((Cita.fecha > hoy) | ((Cita.fecha == hoy) & (Cita.hora_inicio >= ahora.time())))
        .order_by(Cita.fecha, Cita.hora_inicio)
    )


def _month_start(d: date, months_back: int) -> date:
    y, m = d.year, d.month - months_back
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


def admin_stats(db: Session) -> dict:
    hoy = now_local().date()
    pacientes = _count(
        db, select(func.count(Paciente.id)).join(Paciente.usuario).where(Usuario.activo.is_(True))
    )
    medicos = _count(db, select(func.count(Medico.id)).join(Medico.usuario).where(Usuario.activo.is_(True)))
    citas_hoy = _count(db, select(func.count(Cita.id)).where(Cita.fecha == hoy))
    pendientes = _count(db, select(func.count(Cita.id)).where(Cita.estado == CITA_PENDIENTE))
    aut_pend = _count(
        db,
        select(func.count(SolicitudAutorizacion.id)).where(
            SolicitudAutorizacion.estado.in_((AUT_PENDIENTE, AUT_EN_REVISION))
        ),
    )
    por_estado_rows = dict(db.execute(select(Cita.estado, func.count(Cita.id)).group_by(Cita.estado)).all())
    por_estado = [{"estado": e, "total": por_estado_rows.get(e, 0)} for e in ESTADOS_CITA]

    # Citas por mes (últimos 6 meses). Se agrupa en Python para ser compatible con SQLite y PostgreSQL.
    inicio = _month_start(hoy, 5)
    fechas = db.scalars(select(Cita.fecha).where(Cita.fecha >= inicio)).all()
    conteo = Counter((f.year, f.month) for f in fechas)
    por_mes = []
    for i in range(5, -1, -1):
        m = _month_start(hoy, i)
        por_mes.append({"periodo": f"{MESES[m.month - 1]} {m.year}", "total": conteo.get((m.year, m.month), 0)})

    recientes = db.scalars(select(Cita).order_by(Cita.creado_en.desc(), Cita.id.desc()).limit(6)).unique().all()
    return {
        "pacientes_activos": pacientes,
        "medicos_activos": medicos,
        "citas_hoy": citas_hoy,
        "citas_pendientes": pendientes,
        "autorizaciones_pendientes": aut_pend,
        "citas_por_estado": por_estado,
        "citas_por_mes": por_mes,
        "citas_recientes": _out(recientes),
    }


def patient_stats(db: Session, user: Usuario) -> dict:
    paciente_id = user.paciente.id if user.paciente else -1
    ahora = now_local()
    proxima = db.scalars(_upcoming_stmt(Cita.paciente_id == paciente_id, ahora).limit(1)).first()
    return {
        "proxima_cita": _out([proxima])[0] if proxima else None,
        "total_citas": _count(db, select(func.count(Cita.id)).where(Cita.paciente_id == paciente_id)),
        "citas_pendientes": _count(
            db,
            select(func.count(Cita.id)).where(
                Cita.paciente_id == paciente_id,
                Cita.estado.in_((CITA_PENDIENTE, CITA_CONFIRMADA)),
                Cita.fecha >= ahora.date(),
            ),
        ),
        "autorizaciones_en_tramite": _count(
            db,
            select(func.count(SolicitudAutorizacion.id)).where(
                SolicitudAutorizacion.paciente_id == paciente_id,
                SolicitudAutorizacion.estado.in_((AUT_PENDIENTE, AUT_EN_REVISION)),
            ),
        ),
        "notificaciones_no_leidas": _unread(db, user),
    }


def doctor_stats(db: Session, user: Usuario) -> dict:
    medico_id = user.medico.id if user.medico else -1
    ahora = now_local()
    hoy = ahora.date()
    citas_hoy = db.scalars(
        select(Cita).where(Cita.medico_id == medico_id, Cita.fecha == hoy).order_by(Cita.hora_inicio)
    ).unique().all()
    proximas = db.scalars(_upcoming_stmt(Cita.medico_id == medico_id, ahora).limit(5)).unique().all()
    pendientes_atencion = _count(
        db,
        select(func.count(Cita.id)).where(
            Cita.medico_id == medico_id,
            Cita.estado.in_((CITA_PENDIENTE, CITA_CONFIRMADA, CITA_EN_ATENCION)),
            Cita.fecha <= hoy,
        ),
    )
    return {
        "citas_hoy": len(citas_hoy),
        "agenda_hoy": _out(citas_hoy),
        "proximas_citas": _out(proximas),
        "pendientes_atencion": pendientes_atencion,
        "notificaciones_no_leidas": _unread(db, user),
    }


def stats_for(db: Session, user: Usuario) -> dict:
    if user.rol == ROL_ADMIN:
        data = admin_stats(db)
    elif user.rol == ROL_MEDICO:
        data = doctor_stats(db, user)
    elif user.rol == ROL_PACIENTE:
        data = patient_stats(db, user)
    else:
        data = {}
    return {"rol": user.rol, "data": data}
