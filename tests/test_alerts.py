"""Unit tests for low-stock, stock-out, bed capacity, and doctor coverage alerts."""
from fastapi.testclient import TestClient
from app.services.inventory_service import evaluate_stock_alerts
from app.services.bed_service import evaluate_bed_alerts, update_ward_beds
from app.services.attendance_service import evaluate_staff_alerts, toggle_doctor_attendance
from app.models.schemas import BedUpdate
from app.database.firestore_client import repo


def test_stockout_and_lowstock_alert_triggers():
    # Baseline seed data contains ORS with quantity 0 (out of stock)
    # and Amoxicillin with quantity 40 <= reorder 200 (low stock)
    alerts = evaluate_stock_alerts()
    alert_ids = [a.id for a in alerts]

    # ORS out of stock
    assert "alert-out-med-ors-sachets" in alert_ids
    ors_alert = next(a for a in alerts if a.id == "alert-out-med-ors-sachets")
    assert ors_alert.severity == "DANGER"
    assert "OUT OF STOCK" in ors_alert.message

    # Amoxicillin low stock
    assert "alert-low-med-amoxicillin-500" in alert_ids
    amx_alert = next(a for a in alerts if a.id == "alert-low-med-amoxicillin-500")
    assert "Low Stock Alert" in amx_alert.title


def test_critical_bed_capacity_alert():
    # Update Emergency ward (total 6 beds) to 6 occupied (100% capacity)
    update_ward_beds("ward-emergency", BedUpdate(occupied_beds=6, cleaning_beds=0))
    alerts = evaluate_bed_alerts()
    
    crit_alert = next((a for a in alerts if a.id == "alert-bed-ward-emergency"), None)
    assert crit_alert is not None
    assert crit_alert.severity == "DANGER"
    assert "100.0% capacity" in crit_alert.message


def test_zero_doctors_on_duty_alert():
    # Set all doctors to off duty
    docs = repo.get_doctors()
    for d in docs:
        toggle_doctor_attendance(d["doctor_id"], is_present=False)

    alerts = evaluate_staff_alerts()
    zero_doc_alert = next((a for a in alerts if a.id == "alert-no-doctors-on-duty"), None)
    assert zero_doc_alert is not None
    assert zero_doc_alert.severity == "DANGER"
    assert "No healthcare medical officers are currently marked ON DUTY" in zero_doc_alert.message
