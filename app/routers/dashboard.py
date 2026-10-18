"""Dashboard metrics and live alerts router."""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from app.config import settings
from app.database.firestore_client import repo
from app.models.schemas import DashboardStats, Alert
from app.models.roles import Role, get_current_role, require_roles
from app.services.inventory_service import evaluate_stock_alerts, compute_stock_status
from app.services.bed_service import evaluate_bed_alerts
from app.services.attendance_service import evaluate_staff_alerts
from app.services.footfall_service import get_today_total_footfall

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(current_role: Role = Depends(get_current_role)):
    """Aggregates real-time operational status for PHC/CHC live dashboard."""
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Wards / Beds
    wards = repo.get_wards()
    total_beds = sum(w["total_beds"] for w in wards)
    occupied_beds = sum(w["occupied_beds"] for w in wards)
    available_beds = sum(w["available_beds"] for w in wards)
    overall_bed_occupancy = round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0.0

    # Medicines
    meds = repo.get_medicines()
    total_medicines = len(meds)
    low_stock_count = 0
    out_of_stock_count = 0
    for m in meds:
        st = compute_stock_status(m["current_quantity"], m["reorder_level"], m["expiry_date"])
        if st.value == "OUT_OF_STOCK":
            out_of_stock_count += 1
        elif st.value == "LOW_STOCK":
            low_stock_count += 1

    # Doctors
    docs = repo.get_doctors()
    total_doctors = len(docs)
    doctors_on_duty = sum(1 for d in docs if d.get("is_present") and d.get("status") == "ON_DUTY")

    # Footfall
    today_footfall = get_today_total_footfall()

    # Active Alerts
    active_alerts: List[Alert] = []
    active_alerts.extend(evaluate_stock_alerts())
    active_alerts.extend(evaluate_bed_alerts())
    active_alerts.extend(evaluate_staff_alerts())

    # Sort alerts by severity (DANGER first, then WARNING, then INFO)
    severity_order = {"DANGER": 0, "WARNING": 1, "INFO": 2}
    active_alerts.sort(key=lambda a: severity_order.get(a.severity, 99))

    return DashboardStats(
        facility_name="Smart Health PHC/CHC Facility",
        current_time=now_str,
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        available_beds=available_beds,
        bed_occupancy_percent=overall_bed_occupancy,
        total_medicines=total_medicines,
        low_stock_medicines=low_stock_count,
        out_of_stock_medicines=out_of_stock_count,
        doctors_on_duty=doctors_on_duty,
        total_doctors=total_doctors,
        today_footfall=today_footfall,
        alerts_count=len(active_alerts),
        active_alerts=active_alerts,
    )


@router.get("/alerts", response_model=List[Alert])
def get_live_alerts():
    """Returns only active alerts for live ticker/announcer."""
    alerts = []
    alerts.extend(evaluate_stock_alerts())
    alerts.extend(evaluate_bed_alerts())
    alerts.extend(evaluate_staff_alerts())
    severity_order = {"DANGER": 0, "WARNING": 1, "INFO": 2}
    alerts.sort(key=lambda a: severity_order.get(a.severity, 99))
    return alerts


@router.post("/simulate-surge")
def simulate_epidemic_surge(
    current_role: Role = Depends(require_roles([Role.ADMIN])),
):
    """
    Demo Evaluator Feature: Injects a realistic seasonal viral / monsoon epidemic surge.
    Increases patient footfall by 75, consumes buffer medicine stock, and occupies emergency beds.
    """
    from datetime import date
    today_str = date.today().isoformat()
    now_str = datetime.now().isoformat()

    # 1. Consume Critical Medicines
    consumed_summary = []
    med_updates = [
        ("med-paracetamol-500", 250), # High fever demand
        ("med-amoxicillin-500", 35),  # Drops Amoxicillin from 40 down to 5 (Critical Low)
        ("med-iv-normal-saline", 70), # Dehydration infusion
        ("med-rabies-vaccine", 3),    # Drops to 2 vials
    ]
    for med_id, deduct_qty in med_updates:
        med = repo.get_medicine(med_id)
        if med:
            new_qty = max(0, med["current_quantity"] - deduct_qty)
            med["current_quantity"] = new_qty
            med["last_updated_at"] = now_str
            repo.save_medicine(med)
            consumed_summary.append(f"{med['name']} (-{deduct_qty})")

    # 2. Fill Emergency & General Wards
    emergency_ward = repo.get_ward("ward-emergency")
    if emergency_ward:
        # Emergency ward total is 6; set to 6 (100% capacity)
        repo.update_ward("ward-emergency", occupied=6, cleaning=0)

    gen_ward = repo.get_ward("ward-gen-male")
    if gen_ward:
        # Increase male general ward to 14 occupied out of 15
        repo.update_ward("ward-gen-male", occupied=14, cleaning=1)

    # 3. Inject Surge Footfall
    surge_entry_opd = {
        "id": f"ff-surge-{datetime.now().strftime('%H%M%S')}-opd",
        "department": "Emergency & Casualty",
        "patient_count": 55,
        "date": today_str,
        "hour": datetime.now().hour,
        "recorded_at": now_str,
    }
    surge_entry_mch = {
        "id": f"ff-surge-{datetime.now().strftime('%H%M%S')}-mch",
        "department": "General OPD",
        "patient_count": 25,
        "date": today_str,
        "hour": datetime.now().hour,
        "recorded_at": now_str,
    }
    repo.add_footfall(surge_entry_opd)
    repo.add_footfall(surge_entry_mch)

    return {
        "status": "surge_simulated",
        "title": "⚡ Monsoon Outbreak Surge Injected",
        "message": "Simulated arrival of 80 acute gastroenteritis & viral fever patients. Emergency beds filled to 100%, and antibiotics/IV fluids consumed.",
        "consumed_medicines": consumed_summary,
        "patient_surge_count": 80,
    }


@router.post("/reset-baseline")
def reset_to_baseline(
    current_role: Role = Depends(require_roles([Role.ADMIN])),
):
    """Resets all facility inventory, beds, attendance, and footfall back to clean baseline state."""
    repo.reset_for_tests()
    return {
        "status": "reset_complete",
        "message": "PHC/CHC facility data reset to initial authentic baseline."
    }

