"""Consultas, autorizaciones, notificaciones, panel, usuarios y auditoría."""
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.constants import ROL_ADMIN
from app.db.session import get_db
from app.dependencies import Pagination, get_current_user, require_roles
from app.models import Usuario
from app.schemas.agenda import ConsultaCreate, ConsultaOut
from app.schemas.common import Message, Page, StatusUpdate
from app.schemas.otros import (
    AuditoriaOut,
    AutorizacionCreate,
    AutorizacionOut,
    AutorizacionStatusUpdate,
    HistorialOut,
    NotificacionOut,
    RoleUpdate,
    UsuarioOut,
)
from app.services import (
    audit_service,
    authorization_service,
    consultation_service,
    dashboard_service,
    notification_service,
    user_service,
)

admin_only = require_roles(ROL_ADMIN)

# ---------- Consultas ----------
consultations_router = APIRouter(prefix="/consultations", tags=["Consultas (simuladas)"])


@consultations_router.get("", response_model=Page[ConsultaOut])
def list_consultations(
    paciente_id: int | None = None,
    cita_id: int | None = None,
    pag: Pagination = Depends(),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return consultation_service.list_consultations(db, user, pag.page, pag.size, paciente_id, cita_id)


@consultations_router.get("/{consulta_id}", response_model=ConsultaOut)
def get_consultation(consulta_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return consultation_service.get_consultation(db, user, consulta_id)


@consultations_router.post("", response_model=ConsultaOut, status_code=status.HTTP_201_CREATED)
def create_consultation(data: ConsultaCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return consultation_service.create_consultation(db, user, data)


# ---------- Autorizaciones ----------
authorizations_router = APIRouter(prefix="/authorizations", tags=["Autorizaciones"])


@authorizations_router.get("", response_model=Page[AutorizacionOut])
def list_authorizations(
    estado: str | None = None,
    q: str | None = None,
    pag: Pagination = Depends(),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return authorization_service.list_authorizations(db, user, pag.page, pag.size, estado, q)


@authorizations_router.get("/{solicitud_id}", response_model=AutorizacionOut)
def get_authorization(solicitud_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return authorization_service.get_for_user(db, user, solicitud_id)


@authorizations_router.get("/{solicitud_id}/history", response_model=list[HistorialOut])
def authorization_history(
    solicitud_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
):
    return authorization_service.get_for_user(db, user, solicitud_id).historial


@authorizations_router.post("", response_model=AutorizacionOut, status_code=status.HTTP_201_CREATED)
def create_authorization(
    data: AutorizacionCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
):
    return authorization_service.create_authorization(db, user, data)


@authorizations_router.patch("/{solicitud_id}/status", response_model=AutorizacionOut)
def change_authorization_status(
    solicitud_id: int,
    data: AutorizacionStatusUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(admin_only),
):
    return authorization_service.change_status(db, admin, solicitud_id, data)


# ---------- Notificaciones ----------
notifications_router = APIRouter(prefix="/notifications", tags=["Notificaciones"])


@notifications_router.get("", response_model=Page[NotificacionOut])
def list_notifications(
    solo_no_leidas: bool = False,
    pag: Pagination = Depends(),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return notification_service.list_for_user(db, user, pag.page, pag.size, solo_no_leidas)


@notifications_router.patch("/read-all", response_model=Message)
def mark_all_read(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    total = notification_service.mark_all_read(db, user)
    return Message(detail=f"{total} notificación(es) marcadas como leídas")


@notifications_router.patch("/{notificacion_id}/read", response_model=NotificacionOut)
def mark_read(notificacion_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return notification_service.mark_read(db, user, notificacion_id)


# ---------- Panel ----------
dashboard_router = APIRouter(prefix="/dashboard", tags=["Panel"])


@dashboard_router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict:
    """Estadísticas según el rol del usuario autenticado: {rol, data}."""
    return dashboard_service.stats_for(db, user)


# ---------- Usuarios ----------
users_router = APIRouter(prefix="/users", tags=["Usuarios"])


@users_router.get("", response_model=Page[UsuarioOut])
def list_users(
    q: str | None = None,
    rol: str | None = None,
    activo: bool | None = None,
    pag: Pagination = Depends(),
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    return user_service.list_users(db, pag.page, pag.size, q, rol, activo)


@users_router.patch("/{user_id}/role", response_model=UsuarioOut)
def change_role(user_id: int, data: RoleUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)):
    return user_service.change_role(db, admin, user_id, data.rol)


@users_router.patch("/{user_id}/status", response_model=UsuarioOut)
def set_user_status(
    user_id: int, data: StatusUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)
):
    return user_service.set_status(db, admin, user_id, data.activo)


# ---------- Auditoría (solo lectura) ----------
audit_router = APIRouter(prefix="/audit", tags=["Auditoría"])


@audit_router.get("", response_model=Page[AuditoriaOut])
def list_audit(
    accion: str | None = None,
    recurso: str | None = None,
    usuario_id: int | None = None,
    fecha_desde: date | None = Query(None),
    fecha_hasta: date | None = Query(None),
    pag: Pagination = Depends(),
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    return audit_service.list_logs(db, pag.page, pag.size, accion, recurso, usuario_id, fecha_desde, fecha_hasta)
