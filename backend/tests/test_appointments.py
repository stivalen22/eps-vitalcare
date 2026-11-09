"""Reglas de negocio de citas y consultas."""
from datetime import date, time, timedelta

from app.core.constants import CITA_CONFIRMADA
from app.models import Cita
from tests.conftest import future_date


def _payload(s, fecha=None, hora="09:00"):
    return {
        "medico_id": s["medico"].id,
        "servicio_id": s["servicio"].id,
        "fecha": fecha or future_date(),
        "hora_inicio": hora,
        "motivo": "Control general",
    }


def test_crear_cita_valida_y_persistida(client, tokens, seed_basic, db):
    r = client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["estado"] == "pendiente"
    assert body["hora_fin"] == "09:30:00"  
    # Persistencia real en la base de datos
    db.expire_all()
    assert db.get(Cita, body["id"]) is not None
    # Visible para el médico asignado
    lista = client.get("/api/v1/appointments", headers=tokens["medico"]).json()
    assert lista["total"] == 1


def test_rechazo_horario_ocupado(client, tokens, seed_basic):
    assert client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic)).status_code == 201
    r = client.post("/api/v1/appointments", headers=tokens["p2"], json=_payload(seed_basic, hora="09:15"))
    assert r.status_code == 409
    assert "ya tiene una cita" in r.json()["detail"]


def test_rechazo_fuera_de_horario(client, tokens, seed_basic):
    r = client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic, hora="18:00"))
    assert r.status_code == 409
    assert "fuera de la disponibilidad" in r.json()["detail"]
    # Termina después del cierre (11:45 + 30 min > 12:00)
    r = client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic, hora="11:45"))
    assert r.status_code == 409


def test_rechazo_fecha_pasada(client, tokens, seed_basic):
    ayer = (date.today() - timedelta(days=1)).isoformat()
    r = client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic, fecha=ayer))
    assert r.status_code == 422


def test_paciente_sin_citas_simultaneas(client, tokens, seed_basic, db):
    # Segundo médico con la misma especialidad
    from app.models import Medico, Usuario
    from app.core.security import hash_password
    from app.models import HorarioMedico

    u = Usuario(email="medico2@test.demo", password_hash=hash_password("x1234567"), rol="medico", activo=True)
    db.add(u)
    db.flush()
    m2 = Medico(usuario_id=u.id, nombres="Otro", apellidos="Médico", telefono="3000000009",
                registro_profesional="TEST-0002", especialidades=[db.merge(seed_basic["especialidad"])])
    db.add(m2)
    db.flush()
    db.add(HorarioMedico(medico_id=m2.id, dia_semana=(date.today() + timedelta(days=7)).weekday(),
                         hora_inicio=time(8, 0), hora_fin=time(12, 0), duracion_cita_minutos=30, activo=True))
    db.commit()

    assert client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic)).status_code == 201
    otra = {**_payload(seed_basic), "medico_id": m2.id}
    r = client.post("/api/v1/appointments", headers=tokens["p1"], json=otra)
    assert r.status_code == 409
    assert "paciente" in r.json()["detail"]


def test_slots_disponibles_excluyen_ocupados(client, tokens, seed_basic):
    s = seed_basic
    params = {"medico_id": s["medico"].id, "servicio_id": s["servicio"].id, "fecha": future_date()}
    antes = client.get("/api/v1/schedules/available-slots", headers=tokens["p1"], params=params).json()
    assert len(antes) == 8  # 08:00 a 12:00 cada 30 min
    client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(s))
    despues = client.get("/api/v1/schedules/available-slots", headers=tokens["p1"], params=params).json()
    assert len(despues) == 7
    assert "09:00:00" not in [x["hora_inicio"] for x in despues]


def test_cancelacion_valida_libera_horario(client, tokens, seed_basic):
    cita = client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic)).json()
    r = client.post(f"/api/v1/appointments/{cita['id']}/cancel", headers=tokens["p1"], json={"motivo": "Viaje"})
    assert r.status_code == 200
    assert r.json()["estado"] == "cancelada"
    assert r.json()["motivo_cancelacion"] == "Viaje"
    # La cita se conserva en el historial
    assert client.get(f"/api/v1/appointments/{cita['id']}", headers=tokens["p1"]).status_code == 200
    # Y el horario vuelve a estar disponible
    assert client.post("/api/v1/appointments", headers=tokens["p2"], json=_payload(seed_basic)).status_code == 201
    # No se puede cancelar dos veces
    r = client.post(f"/api/v1/appointments/{cita['id']}/cancel", headers=tokens["p1"])
    assert r.status_code == 409


def test_flujo_de_estados_y_permisos(client, tokens, seed_basic):
    cita = client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic)).json()
    url = f"/api/v1/appointments/{cita['id']}/status"
    # El paciente no confirma
    assert client.patch(url, headers=tokens["p1"], json={"estado": "confirmada"}).status_code == 403
    # Transición inválida
    assert client.patch(url, headers=tokens["medico"], json={"estado": "atendida"}).status_code == 409
    # El médico asignado confirma
    r = client.patch(url, headers=tokens["medico"], json={"estado": "confirmada"})
    assert r.status_code == 200 and r.json()["estado"] == "confirmada"
    # No se atiende una cita futura
    assert client.patch(url, headers=tokens["medico"], json={"estado": "atendida"}).status_code == 409
    # Estado inexistente -> 422
    assert client.patch(url, headers=tokens["medico"], json={"estado": "volando"}).status_code == 422


def test_reprogramar_cita(client, tokens, seed_basic):
    cita = client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic)).json()
    nuevo = {"medico_id": seed_basic["medico"].id, "fecha": future_date(8), "hora_inicio": "10:00", "motivo": "Cambio"}
    r = client.put(f"/api/v1/appointments/{cita['id']}", headers=tokens["p1"], json=nuevo)
    assert r.status_code == 200, r.text
    assert r.json()["hora_inicio"] == "10:00:00"


def test_consulta_simulada_por_medico(client, tokens, seed_basic, db):
    s = seed_basic
    # Cita de hoy creada directamente (la API no permite crear citas en el pasado)
    cita = Cita(paciente_id=s["p1"].id, medico_id=s["medico"].id, servicio_id=s["servicio"].id,
                fecha=date.today(), hora_inicio=time(8, 0), hora_fin=time(8, 30), motivo="Hoy",
                estado=CITA_CONFIRMADA)
    db.add(cita)
    db.commit()
    data = {"cita_id": cita.id, "resumen": "Resumen ficticio de la consulta de prueba."}
    # Otro rol no puede registrar
    assert client.post("/api/v1/consultations", headers=tokens["p1"], json=data).status_code == 403
    r = client.post("/api/v1/consultations", headers=tokens["medico"], json=data)
    assert r.status_code == 201, r.text
    assert client.get(f"/api/v1/appointments/{cita.id}", headers=tokens["p1"]).json()["estado"] == "atendida"
    # Duplicada
    assert client.post("/api/v1/consultations", headers=tokens["medico"], json=data).status_code == 409
    # El paciente ve su historial; otro paciente no
    assert client.get("/api/v1/consultations", headers=tokens["p1"]).json()["total"] == 1
    assert client.get("/api/v1/consultations", headers=tokens["p2"]).json()["total"] == 0
    cid = r.json()["id"]
    assert client.get(f"/api/v1/consultations/{cid}", headers=tokens["p2"]).status_code == 403


def test_notificaciones_por_cita(client, tokens, seed_basic):
    client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic))
    notifs = client.get("/api/v1/notifications", headers=tokens["medico"]).json()
    assert notifs["total"] == 1
    nid = notifs["items"][0]["id"]
    # Un usuario no puede marcar notificaciones ajenas
    assert client.patch(f"/api/v1/notifications/{nid}/read", headers=tokens["p2"]).status_code == 404
    r = client.patch(f"/api/v1/notifications/{nid}/read", headers=tokens["medico"])
    assert r.json()["leida"] is True


def test_dashboard_por_rol(client, tokens, seed_basic):
    client.post("/api/v1/appointments", headers=tokens["p1"], json=_payload(seed_basic))
    admin = client.get("/api/v1/dashboard/stats", headers=tokens["admin"]).json()
    assert admin["rol"] == "admin"
    assert admin["data"]["pacientes_activos"] == 2
    assert admin["data"]["citas_pendientes"] == 1
    pac = client.get("/api/v1/dashboard/stats", headers=tokens["p1"]).json()
    assert pac["data"]["proxima_cita"] is not None
    med = client.get("/api/v1/dashboard/stats", headers=tokens["medico"]).json()
    assert len(med["data"]["proximas_citas"]) == 1
