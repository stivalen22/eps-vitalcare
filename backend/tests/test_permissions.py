"""Restricciones de acceso entre roles y entre pacientes."""
from tests.conftest import future_date


def test_paciente_ve_su_propio_registro(client, tokens, seed_basic):
    r = client.get(f"/api/v1/patients/{seed_basic['p1'].id}", headers=tokens["p1"])
    assert r.status_code == 200
    assert r.json()["email"] == "paciente1@test.demo"


def test_paciente_no_ve_datos_de_otro(client, tokens, seed_basic):
    r = client.get(f"/api/v1/patients/{seed_basic['p2'].id}", headers=tokens["p1"])
    assert r.status_code == 403


def test_paciente_no_lista_pacientes(client, tokens):
    assert client.get("/api/v1/patients", headers=tokens["p1"]).status_code == 403


def test_medico_no_administra(client, tokens):
    assert client.get("/api/v1/patients", headers=tokens["medico"]).status_code == 403
    assert client.get("/api/v1/users", headers=tokens["medico"]).status_code == 403
    assert client.get("/api/v1/audit", headers=tokens["medico"]).status_code == 403
    r = client.post("/api/v1/specialties", headers=tokens["medico"], json={"nombre": "Cardiología"})
    assert r.status_code == 403


def test_paciente_no_crea_servicios_ni_cambia_roles(client, tokens, seed_basic):
    r = client.post(
        "/api/v1/services", headers=tokens["p1"],
        json={"nombre": "X", "especialidad_id": seed_basic["especialidad"].id, "duracion_minutos": 30},
    )
    assert r.status_code == 403
    r = client.patch(f"/api/v1/users/{seed_basic['p1'].usuario_id}/role", headers=tokens["p1"], json={"rol": "admin"})
    assert r.status_code == 403


def test_paciente_no_ve_cita_de_otro(client, tokens, seed_basic):
    s = seed_basic
    r = client.post(
        "/api/v1/appointments", headers=tokens["p1"],
        json={"medico_id": s["medico"].id, "servicio_id": s["servicio"].id, "fecha": future_date(),
              "hora_inicio": "09:00", "motivo": "Control"},
    )
    assert r.status_code == 201
    cita_id = r.json()["id"]
    assert client.get(f"/api/v1/appointments/{cita_id}", headers=tokens["p2"]).status_code == 403
    assert client.post(f"/api/v1/appointments/{cita_id}/cancel", headers=tokens["p2"]).status_code == 403
    # El listado del paciente 2 no incluye la cita del paciente 1
    assert client.get("/api/v1/appointments", headers=tokens["p2"]).json()["total"] == 0


def test_medico_ve_solo_datos_minimos_de_paciente_asignado(client, tokens, seed_basic):
    s = seed_basic
    # Sin cita asignada: prohibido
    assert client.get(f"/api/v1/patients/{s['p1'].id}", headers=tokens["medico"]).status_code == 403
    client.post(
        "/api/v1/appointments", headers=tokens["p1"],
        json={"medico_id": s["medico"].id, "servicio_id": s["servicio"].id, "fecha": future_date(),
              "hora_inicio": "09:00", "motivo": "Control"},
    )
    r = client.get(f"/api/v1/patients/{s['p1'].id}", headers=tokens["medico"])
    assert r.status_code == 200
    assert "email" not in r.json() and "direccion" not in r.json()


def test_admin_no_accede_a_consultas_clinicas(client, tokens):
    r = client.get("/api/v1/consultations", headers=tokens["admin"])
    assert r.status_code == 403


def test_admin_no_puede_quitarse_su_rol(client, tokens, seed_basic):
    r = client.patch(f"/api/v1/users/{seed_basic['admin'].id}/role", headers=tokens["admin"], json={"rol": "paciente"})
    assert r.status_code == 409


def test_vista_publica_de_medicos_sin_contacto(client, tokens):
    r = client.get("/api/v1/doctors", headers=tokens["p1"])
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert "email" not in item and "telefono" not in item
    r_admin = client.get("/api/v1/doctors", headers=tokens["admin"])
    assert "email" in r_admin.json()["items"][0]
