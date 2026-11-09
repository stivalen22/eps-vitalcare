from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.constants import ROL_ADMIN
from app.db.session import get_db
from app.dependencies import Pagination, get_current_user, require_roles
from app.models import Medico, Usuario
from app.repositories.base import get_or_404
from app.schemas.common import Page, StatusUpdate
from app.schemas.persona import MedicoCreate, MedicoDetalle, MedicoOut, MedicoPublicOut, MedicoUpdate
from app.services import doctor_service

router = APIRouter(prefix="/doctors", tags=["Médicos"])
admin_only = require_roles(ROL_ADMIN)


@router.get("", response_model=Page[MedicoDetalle])
def list_doctors(
    q: str | None = Query(None, description="Buscar por nombre, correo o identificador"),
    activo: bool | None = None,
    especialidad_id: int | None = None,
    pag: Pagination = Depends(),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    """El administrador ve todos los datos; los demás roles ven solo médicos activos y sin datos de contacto."""
    if user.rol != ROL_ADMIN:
        activo = True
    result = doctor_service.list_doctors(db, pag.page, pag.size, q, activo, especialidad_id)
    schema = MedicoOut if user.rol == ROL_ADMIN else MedicoPublicOut
    result["items"] = [schema.model_validate(m) for m in result["items"]]
    return result


@router.get("/{medico_id}", response_model=MedicoDetalle)
def get_doctor(medico_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    medico = get_or_404(db, Medico, medico_id, "Médico no encontrado")
    if user.rol == ROL_ADMIN or (user.medico and user.medico.id == medico.id):
        return MedicoOut.model_validate(medico)
    return MedicoPublicOut.model_validate(medico)


@router.post("", response_model=MedicoOut, status_code=status.HTTP_201_CREATED)
def create_doctor(data: MedicoCreate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)):
    return doctor_service.create_doctor(db, admin, data)


@router.put("/{medico_id}", response_model=MedicoOut)
def update_doctor(
    medico_id: int, data: MedicoUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)
):
    return doctor_service.update_doctor(db, admin, medico_id, data)


@router.patch("/{medico_id}/status", response_model=MedicoOut)
def set_doctor_status(
    medico_id: int, data: StatusUpdate, db: Session = Depends(get_db), admin: Usuario = Depends(admin_only)
):
    return doctor_service.set_status(db, admin, medico_id, data.activo)
