"""Integration tests for all REST API endpoints."""
from fastapi.testclient import TestClient


def test_healthz_endpoint(client: TestClient):
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data


def test_readyz_endpoint(client: TestClient):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_get_dashboard_stats(client: TestClient):
    response = client.get("/api/dashboard/stats", headers={"X-User-Role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert "facility_name" in data
    assert data["total_beds"] > 0
    assert data["total_medicines"] > 0
    assert len(data["active_alerts"]) > 0


def test_list_medicines(client: TestClient):
    response = client.get("/api/medicines", headers={"X-User-Role": "pharmacist"})
    assert response.status_code == 200
    meds = response.json()
    assert len(meds) >= 10
    assert any(m["name"] == "Paracetamol 500mg" for m in meds)


def test_create_and_delete_medicine(client: TestClient):
    new_med = {
        "name": "Azithromycin 500mg",
        "category": "Antibiotic",
        "dosage_form": "Tablet",
        "current_quantity": 100,
        "unit": "strips",
        "reorder_level": 30,
        "batch_number": "AZI-2026-T1",
        "expiry_date": "2027-12-31"
    }
    # Create as Pharmacist
    create_resp = client.post("/api/medicines", json=new_med, headers={"X-User-Role": "pharmacist"})
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == "Azithromycin 500mg"
    assert created["status"] == "IN_STOCK"
    med_id = created["id"]

    # Delete as Admin
    del_resp = client.delete(f"/api/medicines/{med_id}", headers={"X-User-Role": "admin"})
    assert del_resp.status_code == 200

    # Verify not found
    get_resp = client.get(f"/api/medicines/{med_id}", headers={"X-User-Role": "admin"})
    assert get_resp.status_code == 404


def test_update_stock_add_and_deduct(client: TestClient):
    med_id = "med-paracetamol-500"
    
    # 1. Deduct 50 strips (Dispense)
    deduct_resp = client.put(
        f"/api/medicines/{med_id}/stock",
        json={"action": "DEDUCT", "quantity": 50, "notes": "OPD Dispensing"},
        headers={"X-User-Role": "pharmacist"}
    )
    assert deduct_resp.status_code == 200
    data = deduct_resp.json()
    assert data["current_quantity"] == 800  # Baseline was 850

    # 2. Add 100 strips (Restock)
    add_resp = client.put(
        f"/api/medicines/{med_id}/stock",
        json={"action": "ADD", "quantity": 100, "notes": "Shipment receipt"},
        headers={"X-User-Role": "pharmacist"}
    )
    assert add_resp.status_code == 200
    assert add_resp.json()["current_quantity"] == 900


def test_list_and_update_beds(client: TestClient):
    # List beds
    list_resp = client.get("/api/beds", headers={"X-User-Role": "doctor"})
    assert list_resp.status_code == 200
    wards = list_resp.json()
    assert len(wards) >= 5

    # Update Emergency ward (total 6 beds)
    ward_id = "ward-emergency"
    update_resp = client.put(
        f"/api/beds/{ward_id}",
        json={"occupied_beds": 4, "cleaning_beds": 1},
        headers={"X-User-Role": "doctor"}
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["occupied_beds"] == 4
    assert data["cleaning_beds"] == 1
    assert data["available_beds"] == 1  # 6 - (4 + 1)
    assert data["occupancy_rate"] == 66.7


def test_doctor_attendance_toggle(client: TestClient):
    doc_id = "doc-ramesh"
    # Toggle attendance to false
    resp = client.post(
        f"/api/doctors/{doc_id}/toggle-attendance",
        json={"is_present": False},
        headers={"X-User-Role": "doctor"}
    )
    assert resp.status_code == 200
    assert resp.json()["is_present"] is False
    assert resp.json()["status"] == "OFF_DUTY"

    # Toggle back to true
    resp2 = client.post(
        f"/api/doctors/{doc_id}/toggle-attendance",
        json={"is_present": True},
        headers={"X-User-Role": "admin"}
    )
    assert resp2.status_code == 200
    assert resp2.json()["is_present"] is True
    assert resp2.json()["status"] == "ON_DUTY"


def test_record_footfall(client: TestClient):
    entry = {
        "department": "Emergency & Casualty",
        "patient_count": 5
    }
    resp = client.post("/api/footfall", json=entry, headers={"X-User-Role": "doctor"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["department"] == "Emergency & Casualty"
    assert data["patient_count"] == 5


def test_simulate_surge_and_reset(client: TestClient):
    # 1. Trigger Monsoon Surge Simulation as Admin
    surge_resp = client.post("/api/dashboard/simulate-surge", headers={"X-User-Role": "admin"})
    assert surge_resp.status_code == 200
    data = surge_resp.json()
    assert data["status"] == "surge_simulated"
    assert data["patient_surge_count"] == 80
    assert len(data["consumed_medicines"]) >= 4

    # Verify Emergency ward is now at 100% capacity
    bed_resp = client.get("/api/beds/ward-emergency", headers={"X-User-Role": "doctor"})
    assert bed_resp.status_code == 200
    assert bed_resp.json()["occupied_beds"] == 6
    assert bed_resp.json()["occupancy_rate"] == 100.0

    # 2. Reset back to baseline
    reset_resp = client.post("/api/dashboard/reset-baseline", headers={"X-User-Role": "admin"})
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "reset_complete"

    # Verify Emergency ward is back to baseline (5 occupied)
    bed_resp2 = client.get("/api/beds/ward-emergency", headers={"X-User-Role": "doctor"})
    assert bed_resp2.status_code == 200
    assert bed_resp2.json()["occupied_beds"] == 5


def test_export_drug_indent_csv(client: TestClient):
    # Test Pharmacist download
    resp = client.get("/api/medicines/export/indent", headers={"X-User-Role": "pharmacist"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=PHC_CHC_Drug_Warehouse_Indent.csv" in resp.headers["content-disposition"]
    
    csv_text = resp.text
    assert "Indent Item ID" in csv_text
    assert "Medicine Name & Strength" in csv_text
    assert "Paracetamol 500mg" in csv_text
    assert "Oral Rehydration Salts (ORS)" in csv_text
    assert "EMERGENCY - STOCK-OUT" in csv_text

