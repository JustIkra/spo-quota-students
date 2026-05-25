"""
Tests for operator API endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_list_specialties(client, operator_token, specialty):
    response = await client.get("/api/specialties", headers={
        "Authorization": f"Bearer {operator_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Информационные системы"
    assert data[0]["students_count"] == 0
    assert data[0]["available_slots"] == 25


@pytest.mark.asyncio
async def test_list_specialties_with_students(client, operator_token, specialty, student):
    response = await client.get("/api/specialties", headers={
        "Authorization": f"Bearer {operator_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data[0]["students_count"] == 1
    assert data[0]["available_slots"] == 24


@pytest.mark.asyncio
async def test_create_student(client, operator_token, specialty):
    response = await client.post("/api/students", json={
        "specialty_id": specialty.id,
        "first_name": "Анна",
        "last_name": "Иванова",
        "middle_name": "Петровна",
        "certificate_number": "9876543210"
    }, headers={"Authorization": f"Bearer {operator_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Анна"
    assert data["certificate_number"] == "9876543210"


@pytest.mark.asyncio
async def test_create_student_duplicate_attestat(client, operator_token, specialty, student):
    response = await client.post("/api/students", json={
        "specialty_id": specialty.id,
        "first_name": "Другой",
        "last_name": "Студент",
        "certificate_number": "1234567890"  # same as student fixture
    }, headers={"Authorization": f"Bearer {operator_token}"})
    assert response.status_code == 400
    assert "аттестата" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_student_invalid_attestat(client, operator_token, specialty):
    response = await client.post("/api/students", json={
        "specialty_id": specialty.id,
        "first_name": "Анна",
        "last_name": "Иванова",
        "certificate_number": "abc123"  # not digits only
    }, headers={"Authorization": f"Bearer {operator_token}"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_student_wrong_specialty(client, operator_token):
    response = await client.post("/api/students", json={
        "specialty_id": 99999,
        "first_name": "Анна",
        "last_name": "Иванова",
        "certificate_number": "1111111111"
    }, headers={"Authorization": f"Bearer {operator_token}"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_students(client, operator_token, student, specialty):
    response = await client.get("/api/students", headers={
        "Authorization": f"Bearer {operator_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["first_name"] == "Иван"
    assert data[0]["specialty_name"] == "Информационные системы"
    assert data[0]["spo_name"] == "Тестовое СПО"


@pytest.mark.asyncio
async def test_list_students_filter_by_specialty(client, operator_token, student, specialty):
    response = await client.get(f"/api/students?specialty_id={specialty.id}", headers={
        "Authorization": f"Bearer {operator_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_list_students_filter_wrong_specialty(client, operator_token, student):
    response = await client.get("/api/students?specialty_id=99999", headers={
        "Authorization": f"Bearer {operator_token}"
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_student(client, operator_token, student):
    response = await client.put(f"/api/students/{student.id}", json={
        "first_name": "Пётр"
    }, headers={"Authorization": f"Bearer {operator_token}"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Пётр"


@pytest.mark.asyncio
async def test_delete_student(client, operator_token, student):
    response = await client.delete(f"/api/students/{student.id}", headers={
        "Authorization": f"Bearer {operator_token}"
    })
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_cannot_access_operator_endpoints(client, admin_token, specialty):
    response = await client.get("/api/specialties", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_student_quota_exceeded(client, db_session, operator_token, specialty):
    """Fill quota then try to add one more student."""
    from app.models import Student as StudentModel
    # Set quota to 1
    specialty.quota = 1
    await db_session.commit()

    # Create first student (fills quota)
    response = await client.post("/api/students", json={
        "specialty_id": specialty.id,
        "first_name": "Первый",
        "last_name": "Студент",
        "certificate_number": "0000000001"
    }, headers={"Authorization": f"Bearer {operator_token}"})
    assert response.status_code == 201

    # Try to exceed quota
    response = await client.post("/api/students", json={
        "specialty_id": specialty.id,
        "first_name": "Второй",
        "last_name": "Студент",
        "certificate_number": "0000000002"
    }, headers={"Authorization": f"Bearer {operator_token}"})
    assert response.status_code == 400
    assert "Quota exceeded" in response.json()["detail"]
