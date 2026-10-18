"""Role-Based Access Control (RBAC) authorization tests."""
from fastapi.testclient import TestClient


def test_pharmacist_forbidden_from_bed_updates(client: TestClient):
    resp = client.put(
        "/api/beds/ward-emergency",
        json={"occupied_beds": 3, "cleaning_beds": 0},
        headers={"X-User-Role": "pharmacist"}
    )
    assert resp.status_code == 403
    assert "Access denied for role 'pharmacist'" in resp.json()["detail"]


def test_pharmacist_forbidden_from_doctor_attendance(client: TestClient):
    resp = client.post(
        "/api/doctors/doc-ramesh/toggle-attendance",
        json={"is_present": False},
        headers={"X-User-Role": "pharmacist"}
    )
    assert resp.status_code == 403
    assert "Access denied for role 'pharmacist'" in resp.json()["detail"]


def test_doctor_forbidden_from_medicine_creation(client: TestClient):
    resp = client.post(
        "/api/medicines",
        json={
            "name": "Ibuprofen 400mg",
            "category": "Analgesic",
            "dosage_form": "Tablet",
            "current_quantity": 50,
            "unit": "strips",
            "reorder_level": 10,
            "expiry_date": "2027-01-01"
        },
        headers={"X-User-Role": "doctor"}
    )
    assert resp.status_code == 403
    assert "Access denied for role 'doctor'" in resp.json()["detail"]


def test_doctor_forbidden_from_medicine_deletion(client: TestClient):
    resp = client.delete(
        "/api/medicines/med-paracetamol-500",
        headers={"X-User-Role": "doctor"}
    )
    assert resp.status_code == 403
    assert "Access denied for role 'doctor'" in resp.json()["detail"]


def test_doctor_forbidden_from_adding_doctor(client: TestClient):
    resp = client.post(
        "/api/doctors",
        json={
            "name": "Dr. Sunita Rao",
            "specialization": "Radiology",
            "shift": "Morning"
        },
        headers={"X-User-Role": "doctor"}
    )
    assert resp.status_code == 403


def test_invalid_role_header_rejected(client: TestClient):
    resp = client.get("/api/medicines", headers={"X-User-Role": "superhacker"})
    assert resp.status_code == 400
    assert "Invalid role" in resp.json()["detail"]
