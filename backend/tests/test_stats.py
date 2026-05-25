"""
Tests for statistics endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_stats_as_admin(client, admin_token, spo, specialty, student):
    response = await client.get("/api/stats", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_spo"] >= 1
    assert data["total_students"] >= 1
    assert data["total_specialties"] >= 1
    assert len(data["spo_list"]) >= 1

    # Check nested structure
    spo_stat = next(s for s in data["spo_list"] if s["spo_id"] == spo.id)
    assert spo_stat["spo_name"] == "Тестовое СПО"
    assert spo_stat["total_students"] == 1
    assert len(spo_stat["specialties"]) == 1


@pytest.mark.asyncio
async def test_stats_as_operator(client, operator_token, spo, specialty, student):
    response = await client.get("/api/stats", headers={
        "Authorization": f"Bearer {operator_token}"
    })
    assert response.status_code == 200
    data = response.json()
    # Operator sees only their SPO
    assert data["total_spo"] == 1
    assert data["spo_list"][0]["spo_id"] == spo.id


@pytest.mark.asyncio
async def test_stats_empty(client, admin_token):
    """Admin with no data should still get valid stats."""
    response = await client.get("/api/stats", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == 0
