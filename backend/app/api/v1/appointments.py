from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import Pagination, get_current_user
from app.models import Usuario
from app.schemas.agenda import CitaCancel, CitaCreate, CitaOut, CitaStatusUpdate, CitaUpdate
from app.schemas.common import Page
from app.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["Citas"])


@router.get("", response_model=Page[CitaOut])
def list_appointments(
    estado: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    medico_id: int | None = None,
    paciente_id: int | None = None,
    servicio_id: int | None = None,
    q: str | None = Query(None, description="Buscar por paciente, médico o servicio"),
    orden: Literal["asc", "desc"] = "desc",
    pag: Pagination = Depends(),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """Paciente: sus citas. Médico: citas asignadas. Administrador: todas."""
    return appointment_service.list_appointments(
        db, user, pag.page, pag.size, estado, fecha_desde, fecha_hasta, medico_id, paciente_id, servicio_id, q, orden
    )


@router.get("/{cita_id}", response_model=CitaOut)
def get_appointment(cita_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return appointment_service.get_for_user(db, user, cita_id)


@router.post("", response_model=CitaOut, status_code=status.HTTP_201_CREATED)
def create_appointment(data: CitaCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return appointment_service.create_appointment(db, user, data)


@router.put("/{cita_id}", response_model=CitaOut)
def update_appointment(
    cita_id: int, data: CitaUpdate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
):
    """Reprogramar (paciente propietario o administrador)."""
    return appointment_service.update_appointment(db, user, cita_id, data)


@router.patch("/{cita_id}/status", response_model=CitaOut)
def change_status(
    cita_id: int, data: CitaStatusUpdate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
):
    return appointment_service.change_status(db, user, cita_id, data.estado)


@router.post("/{cita_id}/cancel", response_model=CitaOut)
def cancel_appointment(
    cita_id: int,
    data: CitaCancel | None = None,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return appointment_service.cancel_appointment(db, user, cita_id, data.motivo if data else None)
