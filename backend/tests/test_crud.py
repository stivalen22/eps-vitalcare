"""CRUD de pacientes, médicos, especialidades y servicios."""

NUEVO_PACIENTE = {
    "email": "creado@test.demo",
    "password": "Clave1234",
    "tipo_documento": "CC",
    "numero_documento": "60000001",
    "nombres": "Creado",
    "apellidos": "Por Admin",
    "fecha_nacimiento": "1999-03-03",
    "telefono": "3005556677",
    "direccion": "Calle Demo",
}


def test_crear_listar_editar_paciente(client, tokens):
    h = tokens["admin"]
    r = client.post("/api/v1/patients", headers=h, json=NUEVO_PACIENTE)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    r = client.get("/api/v1/patients", headers=h, params={"q": "60000001"})
    assert r.json()["total"] == 1

    editado = {**NUEVO_PACIENTE, "nombres": "Editado"}
    editado.pop("password")
    r = client.put(f"/api/v1/patients/{pid}", headers=h, json=editado)
    assert r.status_code == 200 and r.json()["nombres"] == "Editado"

    r = client.patch(f"/api/v1/patients/{pid}/status", headers=h, json={"activo": False})
    assert r.json()["activo"] is False
    r = client.get("/api/v1/patients", headers=h, params={"activo": False})
    assert r.json()["total"] == 1


def test_paciente_correo_duplicado(client, tokens):
    data = {**NUEVO_PACIENTE, "email": "paciente1@test.demo"}
    r = client.post("/api/v1/patients", headers=tokens["admin"], json=data)
    assert r.status_code == 409
    assert "correo" in r.json()["detail"]


def test_paciente_documento_duplicado(client, tokens):
    data = {**NUEVO_PACIENTE, "numero_documento": "80000001"}
    r = client.post("/api/v1/patients", headers=tokens["admin"], json=data)
    assert r.status_code == 409


def test_recurso_inexistente(client, tokens):
    assert client.get("/api/v1/patients/9999", headers=tokens["admin"]).status_code == 404
    assert client.get("/api/v1/appointments/9999", headers=tokens["admin"]).status_code == 404
    assert client.get("/api/v1/doctors/9999", headers=tokens["admin"]).status_code == 404
    r = client.put("/api/v1/services/9999", headers=tokens["admin"],
                   json={"nombre": "Nada", "especialidad_id": 1, "duracion_minutos": 30})
    assert r.status_code == 404


def test_crear_servicio_y_validar_duracion(client, tokens, seed_basic):
    h = tokens["admin"]
    esp_id = seed_basic["especialidad"].id
    r = client.post("/api/v1/services", headers=h,
                    json={"nombre": "Teleconsulta", "especialidad_id": esp_id, "duracion_minutos": 20})
    assert r.status_code == 201
    sid = r.json()["id"]
    assert r.json()["especialidad_nombre"] == "Medicina General"

    r = client.post("/api/v1/services", headers=h,
                    json={"nombre": "Muy larga", "especialidad_id": esp_id, "duracion_minutos": 500})
    assert r.status_code == 422

    r = client.post("/api/v1/services", headers=h,
                    json={"nombre": "teleconsulta", "especialidad_id": esp_id, "duracion_minutos": 20})
    assert r.status_code == 409  # nombre duplicado (sin distinguir mayúsculas)

    r = client.patch(f"/api/v1/services/{sid}/status", headers=h, json={"activo": False})
    assert r.json()["activo"] is False
    # Los pacientes solo ven servicios activos
    nombres = [s["nombre"] for s in client.get("/api/v1/services", headers=tokens["p1"]).json()["items"]]
    assert "Teleconsulta" not in nombres


def test_crear_medico(client, tokens, seed_basic):
    r = client.post("/api/v1/doctors", headers=tokens["admin"], json={
        "email": "nuevo.medico@test.demo", "password": "Clave1234", "nombres": "Nueva", "apellidos": "Médica",
        "telefono": "3001234567", "registro_profesional": "test-0099",
        "especialidad_ids": [seed_basic["especialidad"].id],
    })
    assert r.status_code == 201, r.text
    assert r.json()["registro_profesional"] == "TEST-0099"
    assert r.json()["especialidades"][0]["nombre"] == "Medicina General"


def test_crear_especialidad_duplicada(client, tokens):
    r = client.post("/api/v1/specialties", headers=tokens["admin"], json={"nombre": "medicina general"})
    assert r.status_code == 409


def test_horario_superpuesto_rechazado(client, tokens, seed_basic):
    r = client.post("/api/v1/schedules", headers=tokens["admin"], json={
        "medico_id": seed_basic["medico"].id, "dia_semana": 0, "hora_inicio": "11:00", "hora_fin": "13:00",
    })
    assert r.status_code == 409


def test_horario_rango_invalido(client, tokens):
    r = client.post("/api/v1/schedules", headers=tokens["medico"], json={
        "dia_semana": 0, "hora_inicio": "15:00", "hora_fin": "14:00",
    })
    assert r.status_code == 422


def test_medico_crea_su_horario(client, tokens):
    r = client.post("/api/v1/schedules", headers=tokens["medico"], json={
        "dia_semana": 2, "hora_inicio": "14:00", "hora_fin": "16:00", "duracion_cita_minutos": 30,
    })
    assert r.status_code == 201, r.text


def test_auditoria_registra_acciones(client, tokens):
    client.post("/api/v1/specialties", headers=tokens["admin"], json={"nombre": "Cardiología"})
    r = client.get("/api/v1/audit", headers=tokens["admin"], params={"recurso": "especialidad"})
    assert r.status_code == 200
    assert r.json()["items"][0]["accion"] == "crear"
