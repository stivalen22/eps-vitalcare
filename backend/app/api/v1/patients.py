from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.constants import ROL_ADMIN, ROL_MEDICO
from app.db.session import get_db
from app.dependencies import Pagination, get_current_user, require_roles
from app.models import Usuario
from app.schemas.common import Page, StatusUpdate
from app.schemas.persona import PacienteCreate, PacienteDetalle, PacienteMinOut, PacienteOut, PacienteUpdate
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["Pacientes"])
admin_only = require_roles(ROL_ADMIN)


@router.get("", response_model=Page[PacienteOut])
def list_patients(
    q: str | None = Query(None, description="Buscar por nombre, documento o correo"),
    activo: bool | None = None,
    pag: Pagination = Depends(),
    db: Session = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    return patient_service.list_patients(db, pag.page, pag.size, q, activo)


@router.get("/{paciente_id}", response_model=PacienteDetalle)
def get_patient(paciente_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    """Admin: detalle completo. Paciente: solo el propio. Médico: datos mínimos de pacientes asignados."""
    paciente = patient_service.get_patient_for(db, user, paciente_id)
    if user.rol == ROL_MEDICO:
        return PacienteMinOut.model_validate(paciente)
    return PacienteOut.model_validate(paciente)


@router.post("", response_model=PacienteOut, status_code=status.HTTP_201_CREATED)
def create_patient(data: PacienteCreate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)):
    return patient_service.create_patient(db, admin, data)


@router.put("/{paciente_id}", response_model=PacienteOut)
def update_patient(
    paciente_id: int, data: PacienteUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)
):
    return patient_service.update_patient(db, admin, paciente_id, data)


@router.patch("/{paciente_id}/status", response_model=PacienteOut)
def set_patient_status(
    paciente_id: int, data: StatusUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)
):
    return patient_service.set_status(db, admin, paciente_id, data.activo)
