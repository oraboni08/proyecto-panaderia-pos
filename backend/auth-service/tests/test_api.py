"""Pruebas del servicio completo: HTTP + DTOs + dominio + bcrypt + JWT + SQLite."""

import jwt

from tests.conftest import login

BASE = "/api/v1/auth"


def test_health(client):
    assert client.get(f"{BASE}/health").status_code == 200


def test_usuarios_iniciales_rn21(client, admin_headers):
    r = client.get(f"{BASE}/users", headers=admin_headers)
    assert r.status_code == 200
    usuarios = {u["usuario"]: u for u in r.json()}
    assert usuarios["admin"]["rol"] == "admin"
    assert usuarios["cajero"]["rol"] == "cajero"


def test_login_201_y_token_con_rol(client):
    r = client.post(f"{BASE}/tokens", json={"usuario": "cajero", "password": "cajero-pruebas-123"})
    assert r.status_code == 201
    body = r.json()
    assert body["rol"] == "cajero"
    assert body["token_type"] == "bearer"

    payload = jwt.decode(body["access_token"], "clave-de-pruebas-panaderia-pos-2026", algorithms=["HS256"])
    assert payload["sub"] == "cajero"
    assert payload["rol"] == "cajero"


def test_login_incorrecto_401(client):
    r = client.post(f"{BASE}/tokens", json={"usuario": "admin", "password": "equivocada"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Usuario o contraseña incorrectos"


def test_login_sin_campos_422(client):
    assert client.post(f"{BASE}/tokens", json={"usuario": "admin"}).status_code == 422


def test_me(client, cajero_headers):
    r = client.get(f"{BASE}/users/me", headers=cajero_headers)
    assert r.status_code == 200
    assert r.json()["usuario"] == "cajero"


def test_respuestas_no_incluyen_contrasena_rnf05(client, admin_headers):
    for u in client.get(f"{BASE}/users", headers=admin_headers).json():
        assert "password" not in u
        assert "password_hash" not in u


def test_cajero_no_gestiona_usuarios_rn13(client, cajero_headers):
    assert client.get(f"{BASE}/users", headers=cajero_headers).status_code == 403
    r = client.post(
        f"{BASE}/users",
        json={"nombre": "X", "usuario": "x", "password": "secreto123", "rol": "admin"},
        headers=cajero_headers,
    )
    assert r.status_code == 403


def test_sin_token_401(client):
    assert client.get(f"{BASE}/users").status_code == 401


def test_crear_usuario_y_entrar(client, admin_headers):
    r = client.post(
        f"{BASE}/users",
        json={"nombre": "Juan Pérez", "usuario": "juan", "password": "juan-12345", "rol": "cajero"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.json()["activo"] is True

    assert login(client, "juan", "juan-12345")


def test_crear_usuario_repetido_409(client, admin_headers):
    r = client.post(
        f"{BASE}/users",
        json={"nombre": "Otro", "usuario": "cajero", "password": "secreto123", "rol": "cajero"},
        headers=admin_headers,
    )
    assert r.status_code == 409


def test_crear_usuario_contrasena_corta_400(client, admin_headers):
    r = client.post(
        f"{BASE}/users",
        json={"nombre": "Ana", "usuario": "ana", "password": "123", "rol": "cajero"},
        headers=admin_headers,
    )
    assert r.status_code == 400


def test_crear_usuario_rol_invalido_422(client, admin_headers):
    r = client.post(
        f"{BASE}/users",
        json={"nombre": "Ana", "usuario": "ana", "password": "secreto123", "rol": "gerente"},
        headers=admin_headers,
    )
    assert r.status_code == 422


def test_desactivar_usuario_impide_login_rn19(client, admin_headers):
    r = client.post(
        f"{BASE}/users",
        json={"nombre": "Temporal", "usuario": "temporal", "password": "temporal123", "rol": "cajero"},
        headers=admin_headers,
    )
    uid = r.json()["id_usuario"]

    r = client.patch(f"{BASE}/users/{uid}", json={"activo": False}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["activo"] is False

    r = client.post(f"{BASE}/tokens", json={"usuario": "temporal", "password": "temporal123"})
    assert r.status_code == 401


def test_admin_no_se_desactiva_a_si_mismo_400_rn20(client, admin_headers):
    usuarios = client.get(f"{BASE}/users", headers=admin_headers).json()
    admin_id = next(u["id_usuario"] for u in usuarios if u["usuario"] == "admin")

    r = client.patch(f"{BASE}/users/{admin_id}", json={"activo": False}, headers=admin_headers)
    assert r.status_code == 400


def test_patch_usuario_inexistente_404(client, admin_headers):
    r = client.patch(f"{BASE}/users/9999", json={"activo": False}, headers=admin_headers)
    assert r.status_code == 404


def test_no_existe_delete_rn19(client, admin_headers):
    assert client.delete(f"{BASE}/users/1", headers=admin_headers).status_code == 405
