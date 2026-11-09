"""Especialidades y servicios médicos."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.constants import ROL_ADMIN
from app.db.session import get_db
from app.dependencies import Pagination, get_current_user, require_roles
from app.models import ServicioMedico, Usuario
from app.repositories.base import get_or_404
from app.schemas.catalogo import (
    EspecialidadCreate,
    EspecialidadOut,
    EspecialidadUpdate,
    ServicioCreate,
    ServicioOut,
    ServicioUpdate,
)
from app.schemas.common import Page, StatusUpdate
from app.schemas.persona import MedicoPublicOut
from app.services import catalog_service

specialties_router = APIRouter(prefix="/specialties", tags=["Especialidades"])
services_router = APIRouter(prefix="/services", tags=["Servicios médicos"])
admin_only = require_roles(ROL_ADMIN)


# ---------- Especialidades ----------
@specialties_router.get("", response_model=list[EspecialidadOut])
def list_specialties(
    q: str | None = None,
    activo: bool | None = None,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if user.rol != ROL_ADMIN:
        activo = True
    return catalog_service.list_specialties(db, q, activo)


@specialties_router.post("", response_model=EspecialidadOut, status_code=status.HTTP_201_CREATED)
def create_specialty(data: EspecialidadCreate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)):
    return catalog_service.create_specialty(db, admin, data)


@specialties_router.put("/{esp_id}", response_model=EspecialidadOut)
def update_specialty(
    esp_id: int, data: EspecialidadUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)
):
    return catalog_service.update_specialty(db, admin, esp_id, data)


@specialties_router.patch("/{esp_id}/status", response_model=EspecialidadOut)
def set_specialty_status(
    esp_id: int, data: StatusUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)
):
    return catalog_service.set_specialty_status(db, admin, esp_id, data.activo)


# ---------- Servicios ----------
@services_router.get("", response_model=Page[ServicioOut])
def list_services(
    q: str | None = Query(None, description="Buscar por nombre o descripción"),
    activo: bool | None = None,
    especialidad_id: int | None = None,
    pag: Pagination = Depends(),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    if user.rol != ROL_ADMIN:
        activo = True
    return catalog_service.list_services(db, pag.page, pag.size, q, activo, especialidad_id)


@services_router.get("/{servicio_id}", response_model=ServicioOut)
def get_service(servicio_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    return get_or_404(db, ServicioMedico, servicio_id, "Servicio no encontrado")


@services_router.get("/{servicio_id}/doctors", response_model=list[MedicoPublicOut])
def doctors_for_service(servicio_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)):
    """Médicos activos que pueden prestar el servicio (según su especialidad)."""
    return catalog_service.doctors_for_service(db, servicio_id)


@services_router.post("", response_model=ServicioOut, status_code=status.HTTP_201_CREATED)
def create_service(data: ServicioCreate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)):
    return catalog_service.create_service(db, admin, data)


@services_router.put("/{servicio_id}", response_model=ServicioOut)
def update_service(
    servicio_id: int, data: ServicioUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)
):
    return catalog_service.update_service(db, admin, servicio_id, data)


@services_router.patch("/{servicio_id}/status", response_model=ServicioOut)
def set_service_status(
    servicio_id: int, data: StatusUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)
):
    return catalog_service.set_service_status(db, admin, servicio_id, data.activo)
