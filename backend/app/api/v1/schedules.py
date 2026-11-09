from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.constants import ROL_ADMIN, ROL_MEDICO
from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.models import Usuario
from app.schemas.agenda import HorarioCreate, HorarioOut, HorarioUpdate, SlotOut
from app.services import schedule_service

router = APIRouter(prefix="/schedules", tags=["Horarios"])
staff = require_roles(ROL_ADMIN, ROL_MEDICO)


# Debe declararse antes de /{horario_id}
@router.get("/available-slots", response_model=list[SlotOut])
def available_slots(
    medico_id: int = Query(..., gt=0),
    servicio_id: int = Query(..., gt=0),
    fecha: date = Query(..., description="Fecha en formato AAAA-MM-DD"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """Espacios libres de un médico para un servicio en una fecha (ya excluye horarios ocupados y pasados)."""
    return schedule_service.available_slots(db, medico_id, servicio_id, fecha)


@router.get("", response_model=list[HorarioOut])
def list_schedules(
    medico_id: int | None = None, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
):
    return schedule_service.list_schedules(db, user, medico_id)


@router.post("", response_model=HorarioOut, status_code=status.HTTP_201_CREATED)
def create_schedule(data: HorarioCreate, db: Session = Depends(get_db), user: Usuario = Depends(staff)):
    return schedule_service.create_schedule(db, user, data)


@router.put("/{horario_id}", response_model=HorarioOut)
def update_schedule(
    horario_id: int, data: HorarioUpdate, db: Session = Depends(get_db), user: Usuario = Depends(staff)
):
    return schedule_service.update_schedule(db, user, horario_id, data)


@router.delete("/{horario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(horario_id: int, db: Session = Depends(get_db), user: Usuario = Depends(staff)):
    schedule_service.delete_schedule(db, user, horario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
