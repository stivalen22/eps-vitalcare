"""Solicitudes de autorización y su historial."""


def _crear(client, tokens, seed_basic):
    r = client.post("/api/v1/authorizations", headers=tokens["p1"],
                    json={"servicio_id": seed_basic["servicio"].id, "motivo": "Necesito autorización (prueba)"})
    assert r.status_code == 201, r.text
    return r.json()


def test_crear_solicitud(client, tokens, seed_basic):
    sol = _crear(client, tokens, seed_basic)
    assert sol["estado"] == "pendiente"
    # Duplicada mientras está en trámite
    r = client.post("/api/v1/authorizations", headers=tokens["p1"],
                    json={"servicio_id": seed_basic["servicio"].id, "motivo": "Otra vez la misma"})
    assert r.status_code == 409


def test_solo_pacientes_crean(client, tokens, seed_basic):
    r = client.post("/api/v1/authorizations", headers=tokens["admin"],
                    json={"servicio_id": seed_basic["servicio"].id, "motivo": "Intento admin"})
    assert r.status_code == 403


def test_cambio_estado_autorizado_e_historial(client, tokens, seed_basic):
    sol = _crear(client, tokens, seed_basic)
    url = f"/api/v1/authorizations/{sol['id']}/status"
    # El paciente no puede cambiar el estado
    assert client.patch(url, headers=tokens["p1"], json={"estado": "aprobada"}).status_code == 403
    r = client.patch(url, headers=tokens["admin"], json={"estado": "en_revision"})
    assert r.status_code == 200
    r = client.patch(url, headers=tokens["admin"], json={"estado": "aprobada", "observaciones": "OK"})
    assert r.json()["estado"] == "aprobada"
    # Estado final: no admite más cambios
    assert client.patch(url, headers=tokens["admin"], json={"estado": "rechazada", "observaciones": "x"}).status_code == 409

    # El paciente ve el nuevo estado y el historial completo
    assert client.get(f"/api/v1/authorizations/{sol['id']}", headers=tokens["p1"]).json()["estado"] == "aprobada"
    hist = client.get(f"/api/v1/authorizations/{sol['id']}/history", headers=tokens["p1"]).json()
    assert [h["estado_nuevo"] for h in hist] == ["pendiente", "en_revision", "aprobada"]
    assert hist[1]["usuario_rol"] == "admin"
    # Y recibió notificaciones
    titulos = [n["titulo"] for n in client.get("/api/v1/notifications", headers=tokens["p1"]).json()["items"]]
    assert "Actualización de autorización" in titulos


def test_rechazo_requiere_observacion(client, tokens, seed_basic):
    sol = _crear(client, tokens, seed_basic)
    r = client.patch(f"/api/v1/authorizations/{sol['id']}/status", headers=tokens["admin"], json={"estado": "rechazada"})
    assert r.status_code == 422


def test_otro_paciente_no_ve_solicitud(client, tokens, seed_basic):
    sol = _crear(client, tokens, seed_basic)
    assert client.get(f"/api/v1/authorizations/{sol['id']}", headers=tokens["p2"]).status_code == 403
    assert client.get("/api/v1/authorizations", headers=tokens["p2"]).json()["total"] == 0
    assert client.get("/api/v1/authorizations", headers=tokens["admin"]).json()["total"] == 1


def test_seed_idempotente(db):
    from sqlalchemy import func, select

    from app.models import Cita, Usuario
    from app.seed import seed

    seed(db)
    usuarios_1 = db.scalar(select(func.count(Usuario.id)))
    citas_1 = db.scalar(select(func.count(Cita.id)))
    seed(db)
    assert db.scalar(select(func.count(Usuario.id))) == usuarios_1
    assert db.scalar(select(func.count(Cita.id))) == citas_1
    assert usuarios_1 == 9  # 1 admin + 4 médicos + 4 pacientes
