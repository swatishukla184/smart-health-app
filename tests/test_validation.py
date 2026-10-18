"""Input validation and boundary condition tests (Pydantic v2)."""
from fastapi.testclient import TestClient


def test_over_dispensation_rejected(client: TestClient):
    """Cannot dispense more than available stock."""
    med_id = "med-paracetamol-500"  # Current qty is 850
    resp = client.put(
        f"/api/medicines/{med_id}/stock",
        json={"action": "DEDUCT", "quantity": 900},
        headers={"X-User-Role": "pharmacist"}
    )
    assert resp.status_code == 400
    assert "Cannot dispense 900 strips; only 850 strips available in stock" in resp.json()["detail"]


def test_zero_or_negative_stock_quantity_rejected(client: TestClient):
    med_id = "med-paracetamol-500"
    resp = client.put(
        f"/api/medicines/{med_id}/stock",
        json={"action": "ADD", "quantity": 0},
        headers={"X-User-Role": "pharmacist"}
    )
    assert resp.status_code == 422

    resp_neg = client.put(
        f"/api/medicines/{med_id}/stock",
        json={"action": "ADD", "quantity": -10},
        headers={"X-User-Role": "pharmacist"}
    )
    assert resp_neg.status_code == 422


def test_bed_capacity_overflow_rejected(client: TestClient):
    """Occupied + Cleaning beds cannot exceed total ward capacity."""
    ward_id = "ward-emergency"  # Total beds: 6
    resp = client.put(
        f"/api/beds/{ward_id}",
        json={"occupied_beds": 5, "cleaning_beds": 2},  # 5 + 2 = 7 > 6
        headers={"X-User-Role": "doctor"}
    )
    assert resp.status_code == 422
    assert "exceeds total capacity" in resp.json()["detail"]


def test_negative_beds_rejected(client: TestClient):
    ward_id = "ward-emergency"
    resp = client.put(
        f"/api/beds/{ward_id}",
        json={"occupied_beds": -1, "cleaning_beds": 0},
        headers={"X-User-Role": "doctor"}
    )
    assert resp.status_code == 422


def test_medicine_creation_validation_rules(client: TestClient):
    # Missing required name
    resp1 = client.post(
        "/api/medicines",
        json={
            "name": "   ",  # Blank/whitespace
            "category": "Analgesic",
            "dosage_form": "Tablet",
            "current_quantity": 50,
            "unit": "strips",
            "reorder_level": 10,
            "expiry_date": "2027-01-01"
        },
        headers={"X-User-Role": "admin"}
    )
    assert resp1.status_code == 422

    # Negative stock
    resp2 = client.post(
        "/api/medicines",
        json={
            "name": "Ibuprofen 400mg",
            "category": "Analgesic",
            "dosage_form": "Tablet",
            "current_quantity": -5,
            "unit": "strips",
            "reorder_level": 10,
            "expiry_date": "2027-01-01"
        },
        headers={"X-User-Role": "admin"}
    )
    assert resp2.status_code == 422

    # Invalid expiry date format
    resp3 = client.post(
        "/api/medicines",
        json={
            "name": "Ibuprofen 400mg",
            "category": "Analgesic",
            "dosage_form": "Tablet",
            "current_quantity": 50,
            "unit": "strips",
            "reorder_level": 10,
            "expiry_date": "31-12-2027"  # Should be YYYY-MM-DD
        },
        headers={"X-User-Role": "admin"}
    )
    assert resp3.status_code == 422
