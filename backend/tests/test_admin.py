"""
Tests for admin API endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_list_spo(client, admin_token, spo):
    response = await client.get("/api/admin/spo", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(s["name"] == "Тестовое СПО" for s in data)


@pytest.mark.asyncio
async def test_create_spo(client, admin_token):
    response = await client.post("/api/admin/spo", json={
        "name": "Новое СПО"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 201
    assert response.json()["name"] == "Новое СПО"


@pytest.mark.asyncio
async def test_get_spo(client, admin_token, spo):
    response = await client.get(f"/api/admin/spo/{spo.id}", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Тестовое СПО"
    assert "specialties_count" in data
    assert "students_count" in data


@pytest.mark.asyncio
async def test_update_spo(client, admin_token, spo):
    response = await client.put(f"/api/admin/spo/{spo.id}", json={
        "name": "Обновлённое СПО"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Обновлённое СПО"


@pytest.mark.asyncio
async def test_delete_spo(client, admin_token, spo):
    response = await client.delete(f"/api/admin/spo/{spo.id}", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_operator(client, admin_token, spo):
    response = await client.post("/api/admin/operators", json={
        "spo_id": spo.id
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 201
    data = response.json()
    assert "login" in data
    assert "generated_password" in data
    assert data["spo_id"] == spo.id


@pytest.mark.asyncio
async def test_create_operator_duplicate(client, admin_token, spo, operator_user):
    response = await client.post("/api/admin/operators", json={
        "spo_id": spo.id
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_operators(client, admin_token, operator_user):
    response = await client.get("/api/admin/operators", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_operator_cannot_access_admin(client, operator_token):
    response = await client.get("/api/admin/spo", headers={
        "Authorization": f"Bearer {operator_token}"
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_all_specialties(client, admin_token, specialty, spo):
    response = await client.get("/api/admin/specialties", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["spo_name"] == "Тестовое СПО"


@pytest.mark.asyncio
async def test_list_specialties_filter_by_spo(client, admin_token, specialty, spo):
    response = await client.get(f"/api/admin/specialties?spo_id={spo.id}", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert all(s["spo_id"] == spo.id for s in data)


@pytest.mark.asyncio
async def test_update_specialty_quota(client, admin_token, specialty):
    response = await client.put(f"/api/admin/specialties/{specialty.id}/quota", json={
        "quota": 50
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["quota"] == 50


@pytest.mark.asyncio
async def test_create_specialty_template(client, admin_token):
    response = await client.post("/api/admin/specialty-templates", json={
        "code": "38.02.01",
        "name": "Экономика"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 201
    assert response.json()["code"] == "38.02.01"


@pytest.mark.asyncio
async def test_assign_specialty_to_spo(client, admin_token, spo, template):
    """Assign via the specialty assignment endpoint (not already assigned in fixture)."""
    # First unassign if exists (from other tests), just create a new SPO
    create_resp = await client.post("/api/admin/spo", json={
        "name": "СПО для теста назначения"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    new_spo_id = create_resp.json()["id"]

    response = await client.post("/api/admin/specialties", json={
        "template_id": template.id,
        "spo_id": new_spo_id,
        "quota": 30
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["spo_id"] == new_spo_id
    assert data["quota"] == 30
