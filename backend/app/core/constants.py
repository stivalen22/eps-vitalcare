"""Constantes de dominio: roles, estados y transiciones permitidas."""

# Roles
ROL_PACIENTE = "paciente"
ROL_MEDICO = "medico"
ROL_ADMIN = "admin"
ROLES = (ROL_PACIENTE, ROL_MEDICO, ROL_ADMIN)

# Tipos de documento de demostración
TIPOS_DOCUMENTO = ("CC", "TI", "CE", "PA", "RC")

# Estados de citas
CITA_PENDIENTE = "pendiente"
CITA_CONFIRMADA = "confirmada"
CITA_EN_ATENCION = "en_atencion"
CITA_ATENDIDA = "atendida"
CITA_CANCELADA = "cancelada"
ESTADOS_CITA = (CITA_PENDIENTE, CITA_CONFIRMADA, CITA_EN_ATENCION, CITA_ATENDIDA, CITA_CANCELADA)
# Estados que ocupan un espacio de agenda (la cancelación libera el horario)
ESTADOS_CITA_OCUPAN = (CITA_PENDIENTE, CITA_CONFIRMADA, CITA_EN_ATENCION, CITA_ATENDIDA)
# Estados de citas que aún no se han atendido ni cancelado
ESTADOS_CITA_PROGRAMADAS = (CITA_PENDIENTE, CITA_CONFIRMADA, CITA_EN_ATENCION)
TRANSICIONES_CITA = {
    CITA_PENDIENTE: {CITA_CONFIRMADA, CITA_CANCELADA},
    CITA_CONFIRMADA: {CITA_EN_ATENCION, CITA_ATENDIDA, CITA_CANCELADA},
    CITA_EN_ATENCION: {CITA_ATENDIDA},
    CITA_ATENDIDA: set(),
    CITA_CANCELADA: set(),
}

# Estados de solicitudes de autorización
AUT_PENDIENTE = "pendiente"
AUT_EN_REVISION = "en_revision"
AUT_APROBADA = "aprobada"
AUT_RECHAZADA = "rechazada"
ESTADOS_AUTORIZACION = (AUT_PENDIENTE, AUT_EN_REVISION, AUT_APROBADA, AUT_RECHAZADA)
TRANSICIONES_AUTORIZACION = {
    AUT_PENDIENTE: {AUT_EN_REVISION, AUT_APROBADA, AUT_RECHAZADA},
    AUT_EN_REVISION: {AUT_APROBADA, AUT_RECHAZADA},
    AUT_APROBADA: set(),
    AUT_RECHAZADA: set(),
}

DIAS_SEMANA = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


def sql_in(values) -> str:
    """Genera la lista para un CHECK ... IN (...)."""
    return ", ".join(f"'{v}'" for v in values)
