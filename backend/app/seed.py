"""Datos de DEMOSTRACIÓN (ficticios). Script idempotente.

Uso:  python -m app.seed

- No borra datos existentes.
- Si se ejecuta varias veces, no duplica registros (busca por correo o nombre).
- La contraseña de todas las cuentas demo se toma de SEED_DEMO_PASSWORD (.env).
Ningún nombre, documento ni teléfono corresponde a personas reales.
"""
from datetime import date, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import (
    AUT_APROBADA,
    AUT_EN_REVISION,
    AUT_PENDIENTE,
    AUT_RECHAZADA,
    CITA_ATENDIDA,
    CITA_CANCELADA,
    CITA_CONFIRMADA,
    CITA_PENDIENTE,
    ROL_ADMIN,
    ROL_MEDICO,
    ROL_PACIENTE,
)
from app.core.security import hash_password
from app.core.timeutils import add_minutes, today_local
from app.db.session import SessionLocal
from app.models import (
    Cita,
    Consulta,
    Especialidad,
    HistorialAutorizacion,
    HorarioMedico,
    Medico,
    Notificacion,
    Paciente,
    ServicioMedico,
    SolicitudAutorizacion,
    Usuario,
)

DOMINIO = "vitalcare.demo"

ESPECIALIDADES = [
    ("Medicina General", "Atención primaria y consulta general (ejemplo académico)."),
    ("Pediatría", "Atención de niños y adolescentes (ejemplo académico)."),
    ("Odontología", "Salud oral (ejemplo académico)."),
    ("Psicología", "Orientación y acompañamiento psicológico (ejemplo académico)."),
    ("Nutrición", "Orientación nutricional (ejemplo académico)."),
    ("Medicina Interna", "Atención de adultos (ejemplo académico)."),
]

SERVICIOS = [
    ("Consulta de medicina general", "Consulta general programada.", "Medicina General", 20),
    ("Control pediátrico", "Control de crecimiento y desarrollo.", "Pediatría", 30),
    ("Valoración odontológica", "Revisión y valoración oral.", "Odontología", 30),
    ("Consulta de psicología", "Sesión de orientación psicológica.", "Psicología", 45),
    ("Consulta de nutrición", "Valoración y plan nutricional.", "Nutrición", 30),
    ("Consulta de medicina interna", "Consulta especializada de adultos.", "Medicina Interna", 30),
]

MEDICOS = [
    # email, nombres, apellidos, teléfono, registro ficticio, especialidades
    ("laura.mendez", "Laura", "Méndez Ruiz", "3000000101", "DEMO-RP-0001", ["Medicina General", "Medicina Interna"]),
    ("andres.castillo", "Andrés", "Castillo Peña", "3000000102", "DEMO-RP-0002", ["Pediatría", "Medicina General"]),
    ("sofia.romero", "Sofía", "Romero Díaz", "3000000103", "DEMO-RP-0003", ["Odontología"]),
    ("julian.herrera", "Julián", "Herrera Vega", "3000000104", "DEMO-RP-0004", ["Psicología", "Nutrición"]),
]

PACIENTES = [
    ("paciente1", "CC", "90000001", "Carlos Andrés", "Gómez Ríos", date(1990, 4, 12), "3100000001", "Calle Ficticia 1 # 2-3"),
    ("paciente2", "CC", "90000002", "María Fernanda", "López Torres", date(1985, 9, 3), "3100000002", "Carrera Demo 45 # 10-20"),
    ("paciente3", "TI", "90000003", "Juan Pablo", "Martínez Salazar", date(2010, 1, 22), "3100000003", None),
    ("paciente4", "CC", "90000004", "Valentina", "Ruiz Cárdenas", date(1998, 12, 30), "3100000004", "Avenida Prueba 7 # 8-9"),
]


def _get_or_create_user(db: Session, local: str, rol: str, password_hash: str) -> tuple[Usuario, bool]:
    email = f"{local}@{DOMINIO}"
    user = db.scalar(select(Usuario).where(func.lower(Usuario.email) == email))
    if user:
        return user, False
    user = Usuario(email=email, password_hash=password_hash, rol=rol, activo=True)
    db.add(user)
    db.flush()
    return user, True


def _weekday_near(base: date, offset_days: int) -> date:
    """Fecha desplazada que cae de lunes a viernes (los médicos demo atienden en esos días)."""
    d = base + timedelta(days=offset_days)
    step = 1 if offset_days >= 0 else -1
    while d.weekday() > 4:
        d += timedelta(days=step)
    return d


def seed(db: Session) -> dict:
    pwd = hash_password(settings.SEED_DEMO_PASSWORD)
    resumen = {"creados": [], "existentes": []}

    # Administrador
    admin, nuevo = _get_or_create_user(db, "admin", ROL_ADMIN, pwd)
    (resumen["creados"] if nuevo else resumen["existentes"]).append(admin.email)

    # Especialidades
    esp = {}
    for nombre, desc in ESPECIALIDADES:
        e = db.scalar(select(Especialidad).where(Especialidad.nombre == nombre))
        if e is None:
            e = Especialidad(nombre=nombre, descripcion=desc, activo=True)
            db.add(e)
            db.flush()
        esp[nombre] = e

    # Servicios
    serv = {}
    for nombre, desc, esp_nombre, dur in SERVICIOS:
        s = db.scalar(select(ServicioMedico).where(ServicioMedico.nombre == nombre))
        if s is None:
            s = ServicioMedico(
                nombre=nombre, descripcion=desc, especialidad_id=esp[esp_nombre].id, duracion_minutos=dur, activo=True
            )
            db.add(s)
            db.flush()
        serv[esp_nombre] = s

    # Médicos y horarios (lunes a viernes, mañana y tarde)
    medicos = []
    for local, nombres, apellidos, tel, registro, esps in MEDICOS:
        user, nuevo = _get_or_create_user(db, local, ROL_MEDICO, pwd)
        (resumen["creados"] if nuevo else resumen["existentes"]).append(user.email)
        medico = db.scalar(select(Medico).where(Medico.usuario_id == user.id))
        if medico is None:
            medico = Medico(
                usuario_id=user.id, nombres=nombres, apellidos=apellidos, telefono=tel,
                registro_profesional=registro, especialidades=[esp[n] for n in esps],
            )
            db.add(medico)
            db.flush()
        if not db.scalar(select(HorarioMedico.id).where(HorarioMedico.medico_id == medico.id).limit(1)):
            for dia in range(5):
                db.add(HorarioMedico(medico_id=medico.id, dia_semana=dia, hora_inicio=time(8, 0),
                                     hora_fin=time(12, 0), duracion_cita_minutos=30, activo=True))
                db.add(HorarioMedico(medico_id=medico.id, dia_semana=dia, hora_inicio=time(14, 0),
                                     hora_fin=time(17, 0), duracion_cita_minutos=30, activo=True))
        medicos.append(medico)

    # Pacientes
    pacientes = []
    for local, tipo, doc, nombres, apellidos, nacimiento, tel, direccion in PACIENTES:
        user, nuevo = _get_or_create_user(db, local, ROL_PACIENTE, pwd)
        (resumen["creados"] if nuevo else resumen["existentes"]).append(user.email)
        paciente = db.scalar(select(Paciente).where(Paciente.usuario_id == user.id))
        if paciente is None:
            paciente = Paciente(
                usuario_id=user.id, tipo_documento=tipo, numero_documento=doc, nombres=nombres,
                apellidos=apellidos, fecha_nacimiento=nacimiento, telefono=tel, direccion=direccion,
            )
            db.add(paciente)
            db.flush()
        pacientes.append(paciente)
    db.flush()

    # Citas, consultas, autorizaciones y notificaciones: solo si aún no existen datos demo
    hay_citas = db.scalar(select(Cita.id).where(Cita.paciente_id.in_([p.id for p in pacientes])).limit(1))
    if not hay_citas:
        _seed_activity(db, admin, medicos, pacientes, serv)
        resumen["actividad"] = "creada"
    else:
        resumen["actividad"] = "ya existía (no se duplicó)"

    db.commit()
    return resumen


def _cita(db, paciente, medico, servicio, fecha, inicio, estado, motivo, **extra) -> Cita:
    cita = Cita(
        paciente_id=paciente.id, medico_id=medico.id, servicio_id=servicio.id, fecha=fecha,
        hora_inicio=inicio, hora_fin=add_minutes(inicio, servicio.duracion_minutos),
        motivo=motivo, estado=estado, **extra,
    )
    db.add(cita)
    db.flush()
    return cita


def _seed_activity(db: Session, admin, medicos, pacientes, serv) -> None:
    hoy = today_local()
    laura, andres, sofia, julian = medicos
    p1, p2, p3, p4 = pacientes
    mg, ped, odo, psi = serv["Medicina General"], serv["Pediatría"], serv["Odontología"], serv["Psicología"]

    # Historial pasado
    c1 = _cita(db, p1, laura, mg, _weekday_near(hoy, -21), time(8, 0), CITA_ATENDIDA, "Control general (demo)")
    db.add(Consulta(cita_id=c1.id, resumen="Consulta de control simulada. Paciente refiere sentirse bien. "
                                           "Registro ficticio con fines académicos.",
                    observaciones="Sin observaciones adicionales (dato de prueba)."))
    c2 = _cita(db, p2, sofia, odo, _weekday_near(hoy, -14), time(9, 0), CITA_ATENDIDA, "Revisión oral (demo)")
    db.add(Consulta(cita_id=c2.id, resumen="Valoración odontológica simulada para la demostración del sistema."))
    _cita(db, p1, julian, psi, _weekday_near(hoy, -7), time(10, 0), CITA_CANCELADA, "Orientación (demo)",
          motivo_cancelacion="Cancelada por el paciente (demo)", cancelado_por_id=p1.usuario_id)

    # Hoy (si es fin de semana, se usa el siguiente día hábil)
    dia_actual = _weekday_near(hoy, 0)
    _cita(db, p2, laura, mg, dia_actual, time(15, 0), CITA_CONFIRMADA, "Seguimiento (demo)")
    _cita(db, p4, laura, mg, dia_actual, time(16, 0), CITA_PENDIENTE, "Consulta general (demo)")

    # Próximas
    _cita(db, p1, laura, mg, _weekday_near(hoy, 3), time(9, 0), CITA_PENDIENTE, "Dolor de cabeza leve (demo)")
    _cita(db, p3, andres, ped, _weekday_near(hoy, 4), time(8, 30), CITA_CONFIRMADA, "Control de crecimiento (demo)")
    _cita(db, p4, sofia, odo, _weekday_near(hoy, 6), time(10, 0), CITA_PENDIENTE, "Limpieza (demo)")
    _cita(db, p2, julian, psi, _weekday_near(hoy, 8), time(14, 0), CITA_CONFIRMADA, "Orientación (demo)")

    # Autorizaciones con historial
    def solicitud(paciente, servicio, motivo, pasos):
        s = SolicitudAutorizacion(paciente_id=paciente.id, servicio_id=servicio.id, motivo=motivo, estado=AUT_PENDIENTE)
        db.add(s)
        db.flush()
        db.add(HistorialAutorizacion(solicitud_id=s.id, estado_anterior=None, estado_nuevo=AUT_PENDIENTE,
                                     observacion="Solicitud creada por el paciente", usuario_id=paciente.usuario_id))
        for estado, obs in pasos:
            db.add(HistorialAutorizacion(solicitud_id=s.id, estado_anterior=s.estado, estado_nuevo=estado,
                                         observacion=obs, usuario_id=admin.id))
            s.estado = estado
            if obs:
                s.observaciones = obs
        return s

    solicitud(p1, psi, "Solicitud de sesiones de orientación (demo)", [])
    solicitud(p2, serv["Medicina Interna"], "Remisión a medicina interna (demo)",
              [(AUT_EN_REVISION, "Documentación recibida (demo)")])
    solicitud(p3, odo, "Valoración odontológica infantil (demo)",
              [(AUT_EN_REVISION, None), (AUT_APROBADA, "Aprobada en simulación académica")])
    solicitud(p4, serv["Nutrición"], "Plan nutricional (demo)",
              [(AUT_RECHAZADA, "Falta soporte de la solicitud (dato de prueba)")])

    # Notificaciones de ejemplo
    for p in pacientes:
        db.add(Notificacion(usuario_id=p.usuario_id, titulo="Bienvenido a EPS VitalCare",
                            mensaje="Esta es una cuenta de demostración con datos ficticios.", tipo="cuenta"))
    db.add(Notificacion(usuario_id=p1.usuario_id, titulo="Cita solicitada",
                        mensaje="Tu cita de medicina general quedó registrada (demo).", tipo="cita"))
    db.add(Notificacion(usuario_id=laura.usuario_id, titulo="Agenda actualizada",
                        mensaje="Tienes nuevas citas asignadas para esta semana (demo).", tipo="cita"))


def main() -> None:
    with SessionLocal() as db:
        resultado = seed(db)
    print("Datos de demostración listos.")
    print(f"  Cuentas nuevas: {len(resultado['creados'])} | ya existentes: {len(resultado['existentes'])}")
    print(f"  Actividad demo: {resultado['actividad']}")
    print(f"  Contraseña demo (SEED_DEMO_PASSWORD): {'*' * len(settings.SEED_DEMO_PASSWORD)} (ver .env)")
    for email in resultado["creados"] + resultado["existentes"]:
        print(f"   - {email}")


if __name__ == "__main__":
    main()
