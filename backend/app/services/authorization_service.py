"""Solicitudes de autorización (flujo académico ficticio)."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.constants import (
    AUT_APROBADA,
    AUT_EN_REVISION,
    AUT_PENDIENTE,
    AUT_RECHAZADA,
    ROL_ADMIN,
    ROL_PACIENTE,
    TRANSICIONES_AUTORIZACION,
)
from app.core.errors import conflict, forbidden, invalid, not_found
from app.models import HistorialAutorizacion, Paciente, ServicioMedico, SolicitudAutorizacion, Usuario
from app.repositories.base import like, paginate
from app.schemas.otros import AutorizacionCreate, AutorizacionStatusUpdate
from app.services import audit_service, notification_service

MENSAJES_ESTADO = {
    AUT_PENDIENTE: "está pendiente de revisión",
    AUT_EN_REVISION: "está siendo revisada por el área administrativa",
    AUT_APROBADA: "fue aprobada (simulación académica, sin validez real)",
    AUT_RECHAZADA: "fue rechazada. Revisa las observaciones",
}


def get_for_user(db: Session, user: Usuario, solicitud_id: int) -> SolicitudAutorizacion:
    solicitud = db.get(SolicitudAutorizacion, solicitud_id)
    if solicitud is None:
        raise not_found("Solicitud no encontrada")
    if user.rol == ROL_ADMIN:
        return solicitud
    if user.rol == ROL_PACIENTE and user.paciente and solicitud.paciente_id == user.paciente.id:
        return solicitud
    raise forbidden("No tiene acceso a esta solicitud")


def list_authorizations(
    db: Session, user: Usuario, page: int, size: int, estado: str | None = None, q: str | None = None
) -> dict:
    stmt = select(SolicitudAutorizacion).join(SolicitudAutorizacion.paciente).join(SolicitudAutorizacion.servicio)
    if user.rol == ROL_PACIENTE:
        stmt = stmt.where(SolicitudAutorizacion.paciente_id == (user.paciente.id if user.paciente else -1))
    elif user.rol != ROL_ADMIN:
        raise forbidden("No tiene permisos para consultar solicitudes de autorización")
    if estado:
        stmt = stmt.where(SolicitudAutorizacion.estado == estado)
    if q:
        pattern = like(q)
        stmt = stmt.where(
            or_(
                Paciente.nombres.ilike(pattern),
                Paciente.apellidos.ilike(pattern),
                Paciente.numero_documento.ilike(pattern),
                ServicioMedico.nombre.ilike(pattern),
            )
        )
    stmt = stmt.order_by(SolicitudAutorizacion.creado_en.desc(), SolicitudAutorizacion.id.desc())
    return paginate(db, stmt, page, size)


def create_authorization(db: Session, user: Usuario, data: AutorizacionCreate) -> SolicitudAutorizacion:
    if user.rol != ROL_PACIENTE or user.paciente is None:
        raise forbidden("Solo los pacientes pueden crear solicitudes de autorización")
    servicio = db.get(ServicioMedico, data.servicio_id)
    if servicio is None:
        raise not_found("Servicio no encontrado")
    if not servicio.activo:
        raise invalid("El servicio seleccionado no está activo")
    abierta = db.scalar(
        select(SolicitudAutorizacion.id).where(
            SolicitudAutorizacion.paciente_id == user.paciente.id,
            SolicitudAutorizacion.servicio_id == servicio.id,
            SolicitudAutorizacion.estado.in_((AUT_PENDIENTE, AUT_EN_REVISION)),
        ).limit(1)
    )
    if abierta:
        raise conflict("Ya tiene una solicitud en trámite para este servicio")

    solicitud = SolicitudAutorizacion(
        paciente_id=user.paciente.id, servicio_id=servicio.id, motivo=data.motivo, estado=AUT_PENDIENTE
    )
    db.add(solicitud)
    db.flush()
    db.add(
        HistorialAutorizacion(
            solicitud_id=solicitud.id, estado_anterior=None, estado_nuevo=AUT_PENDIENTE,
            observacion="Solicitud creada por el paciente", usuario_id=user.id,
        )
    )
    notification_service.notify(
        db, user.id, "Solicitud de autorización creada",
        f"Tu solicitud para {servicio.nombre} {MENSAJES_ESTADO[AUT_PENDIENTE]}.", "autorizacion",
    )
    audit_service.log(db, user.id, "crear", "autorizacion", solicitud.id)
    db.commit()
    db.refresh(solicitud)
    return solicitud


def change_status(
    db: Session, admin: Usuario, solicitud_id: int, data: AutorizacionStatusUpdate
) -> SolicitudAutorizacion:
    solicitud = db.get(SolicitudAutorizacion, solicitud_id)
    if solicitud is None:
        raise not_found("Solicitud no encontrada")
    anterior = solicitud.estado
    if data.estado not in TRANSICIONES_AUTORIZACION.get(anterior, set()):
        raise conflict(f"No se puede cambiar una solicitud de '{anterior}' a '{data.estado}'")
    if data.estado == AUT_RECHAZADA and not data.observaciones:
        raise invalid("Debe indicar una observación al rechazar la solicitud")

    solicitud.estado = data.estado
    if data.observaciones:
        solicitud.observaciones = data.observaciones
    db.add(
        HistorialAutorizacion(
            solicitud_id=solicitud.id, estado_anterior=anterior, estado_nuevo=data.estado,
            observacion=data.observaciones, usuario_id=admin.id,
        )
    )
    notification_service.notify(
        db, solicitud.paciente.usuario_id, "Actualización de autorización",
        f"Tu solicitud para {solicitud.servicio.nombre} {MENSAJES_ESTADO[data.estado]}.", "autorizacion",
    )
    audit_service.log(
        db, admin.id, "cambiar_estado", "autorizacion", solicitud.id, detalle=f"{anterior} -> {data.estado}"
    )
    db.commit()
    db.refresh(solicitud)
    return solicitud
