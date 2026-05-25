"""
Tests for authentication endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    response = await client.post("/api/auth/login", json={
        "login": "admin_test",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    response = await client.post("/api/auth/login", json={
        "login": "admin_test",
        "password": "wrong"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post("/api/auth/login", json={
        "login": "nonexistent",
        "password": "test"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_as_admin(client, admin_user, admin_token):
    response = await client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["login"] == "admin_test"
    assert data["role"] == "admin"
    assert data["spo_id"] is None


@pytest.mark.asyncio
async def test_me_as_operator(client, operator_user, operator_token, spo):
    response = await client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {operator_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["login"] == "operator_test"
    assert data["role"] == "operator"
    assert data["spo_id"] == spo.id
    assert data["spo_name"] == "Тестовое СПО"


@pytest.mark.asyncio
async def test_me_invalid_token(client):
    response = await client.get("/api/auth/me", headers={
        "Authorization": "Bearer invalid_token"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_no_token(client):
    response = await client.get("/api/auth/me")
    assert response.status_code in (401, 403)
