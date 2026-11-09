from tests.conftest import PASSWORD, login

REGISTRO = {
    "email": "nuevo@test.demo",
    "password": "Clave1234",
    "tipo_documento": "CC",
    "numero_documento": "70000001",
    "nombres": "Nuevo",
    "apellidos": "Paciente",
    "fecha_nacimiento": "2000-01-01",
    "telefono": "3001112233",
}


def test_login_correcto(client, seed_basic):
    r = client.post("/api/v1/auth/login", json={"email": "admin@test.demo", "password": PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["user"]["rol"] == "admin"
    assert "password_hash" not in body["user"]


def test_login_incorrecto(client, seed_basic):
    r = client.post("/api/v1/auth/login", json={"email": "admin@test.demo", "password": "otra-clave"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Correo o contraseña incorrectos"
    # Correo inexistente: mismo mensaje (no revela si la cuenta existe)
    r2 = client.post("/api/v1/auth/login", json={"email": "noexiste@test.demo", "password": "x"})
    assert r2.status_code == 401
    assert r2.json()["detail"] == r.json()["detail"]


def test_endpoint_protegido_sin_token(client, seed_basic):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/appointments").status_code == 401
    assert client.get("/api/v1/patients").status_code == 401


def test_token_invalido(client, seed_basic):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token-falso"})
    assert r.status_code == 401


def test_registro_paciente_y_me(client, seed_basic):
    r = client.post("/api/v1/auth/register", json=REGISTRO)
    assert r.status_code == 201, r.text
    assert r.json()["user"]["rol"] == "paciente"
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers).json()
    assert me["paciente"]["numero_documento"] == "70000001"


def test_registro_correo_duplicado(client, seed_basic):
    data = {**REGISTRO, "email": "paciente1@test.demo", "numero_documento": "70000009"}
    r = client.post("/api/v1/auth/register", json=data)
    assert r.status_code == 409


def test_registro_datos_invalidos(client, seed_basic):
    data = {**REGISTRO, "email": "no-es-correo", "password": "corta", "fecha_nacimiento": "2999-01-01"}
    r = client.post("/api/v1/auth/register", json=data)
    assert r.status_code == 422
    campos = {e["campo"] for e in r.json()["errors"]}
    assert {"email", "password", "fecha_nacimiento"} <= campos


def test_cambio_contrasena(client, seed_basic):
    h = login(client, "paciente1@test.demo")
    r = client.post(
        "/api/v1/auth/change-password", headers=h,
        json={"current_password": PASSWORD, "new_password": "NuevaClave99"},
    )
    assert r.status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "paciente1@test.demo", "password": PASSWORD}).status_code == 401
    login(client, "paciente1@test.demo", "NuevaClave99")


def test_cuenta_desactivada_no_inicia_sesion(client, tokens, seed_basic):
    pid = seed_basic["p1"].id
    r = client.patch(f"/api/v1/patients/{pid}/status", headers=tokens["admin"], json={"activo": False})
    assert r.status_code == 200 and r.json()["activo"] is False
    r = client.post("/api/v1/auth/login", json={"email": "paciente1@test.demo", "password": PASSWORD})
    assert r.status_code == 403
    # El token emitido antes deja de servir
    assert client.get("/api/v1/auth/me", headers=tokens["p1"]).status_code == 401


def test_editar_perfil_propio(client, tokens):
    r = client.put("/api/v1/auth/me", headers=tokens["p1"], json={"telefono": "3209998877", "direccion": "Calle 1"})
    assert r.status_code == 200
    assert r.json()["paciente"]["telefono"] == "3209998877"
