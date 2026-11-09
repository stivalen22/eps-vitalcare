"""Configuración de pruebas.

Se usa una base de datos SQLite EN MEMORIA, independiente de la de desarrollo:
las pruebas nunca tocan vitalcare.db ni PostgreSQL. Cada prueba recibe un esquema limpio.
"""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas"
os.environ["ENVIRONMENT"] = "test"
os.environ["BCRYPT_ROUNDS"] = "4"

from datetime import date, time, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.constants import ROL_ADMIN, ROL_MEDICO, ROL_PACIENTE  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Especialidad, HorarioMedico, Medico, Paciente, ServicioMedico, Usuario  # noqa: E402

PASSWORD = "Prueba123*"

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db():
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db):
    def _override():
        s = TestingSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------- Fábricas de datos de prueba ----------
def make_user(db, email, rol):
    user = Usuario(email=email, password_hash=hash_password(PASSWORD), rol=rol, activo=True)
    db.add(user)
    db.flush()
    return user


def make_patient(db, email="paciente@test.demo", documento="80000001"):
    user = make_user(db, email, ROL_PACIENTE)
    p = Paciente(
        usuario_id=user.id, tipo_documento="CC", numero_documento=documento, nombres="Paciente",
        apellidos="De Prueba", fecha_nacimiento=date(1995, 5, 5), telefono="3000000000",
    )
    db.add(p)
    db.commit()
    return p


@pytest.fixture()
def seed_basic(db):
    """Admin, especialidad, servicio (30 min), médico con horario 08:00-12:00 todos los días y dos pacientes."""
    admin = make_user(db, "admin@test.demo", ROL_ADMIN)
    esp = Especialidad(nombre="Medicina General", activo=True)
    db.add(esp)
    db.flush()
    servicio = ServicioMedico(nombre="Consulta general", especialidad_id=esp.id, duracion_minutos=30, activo=True)
    db.add(servicio)
    med_user = make_user(db, "medico@test.demo", ROL_MEDICO)
    medico = Medico(
        usuario_id=med_user.id, nombres="Médico", apellidos="De Prueba", telefono="3000000001",
        registro_profesional="TEST-0001", especialidades=[esp],
    )
    db.add(medico)
    db.flush()
    for dia in range(7):
        db.add(HorarioMedico(medico_id=medico.id, dia_semana=dia, hora_inicio=time(8, 0), hora_fin=time(12, 0),
                             duracion_cita_minutos=30, activo=True))
    db.commit()
    p1 = make_patient(db, "paciente1@test.demo", "80000001")
    p2 = make_patient(db, "paciente2@test.demo", "80000002")
    return {"admin": admin, "especialidad": esp, "servicio": servicio, "medico": medico, "p1": p1, "p2": p2}


def login(client, email, password=PASSWORD) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def tokens(client, seed_basic):
    return {
        "admin": login(client, "admin@test.demo"),
        "medico": login(client, "medico@test.demo"),
        "p1": login(client, "paciente1@test.demo"),
        "p2": login(client, "paciente2@test.demo"),
    }


def future_date(days=7) -> str:
    return (date.today() + timedelta(days=days)).isoformat()
