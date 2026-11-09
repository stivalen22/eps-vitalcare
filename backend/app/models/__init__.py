"""Importa todos los modelos para que SQLAlchemy y Alembic los registren."""
from app.models.auditoria import Auditoria
from app.models.autorizacion import HistorialAutorizacion, SolicitudAutorizacion
from app.models.catalogo import Especialidad, ServicioMedico
from app.models.cita import Cita, Consulta
from app.models.horario import HorarioMedico
from app.models.medico import Medico, medico_especialidad
from app.models.notificacion import Notificacion
from app.models.paciente import Paciente
from app.models.usuario import Usuario

__all__ = [
    "Auditoria",
    "Cita",
    "Consulta",
    "Especialidad",
    "HistorialAutorizacion",
    "HorarioMedico",
    "Medico",
    "Notificacion",
    "Paciente",
    "ServicioMedico",
    "SolicitudAutorizacion",
    "Usuario",
    "medico_especialidad",
]
