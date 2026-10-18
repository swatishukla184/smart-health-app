"""Doctor attendance and shift roster tracking service."""
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from app.database.firestore_client import repo
from app.models.schemas import DoctorAttendance, DoctorCreate, DoctorStatus, Alert


def get_all_doctors() -> List[DoctorAttendance]:
    docs = repo.get_doctors()
    return [DoctorAttendance(**d) for d in docs]


def get_doctor_by_id(doc_id: str) -> DoctorAttendance:
    doc = repo.get_doctor(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{doc_id}' not found."
        )
    return DoctorAttendance(**doc)


def toggle_doctor_attendance(
    doc_id: str, is_present: bool, new_status: Optional[DoctorStatus] = None
) -> DoctorAttendance:
    """Toggles or sets attendance and duty status for a doctor."""
    status_str = new_status.value if new_status else ("ON_DUTY" if is_present else "OFF_DUTY")
    updated = repo.update_doctor_attendance(doc_id, is_present, status_str)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{doc_id}' not found."
        )
    return DoctorAttendance(**updated)


def add_doctor(payload: DoctorCreate) -> DoctorAttendance:
    """Adds a new doctor to the roster."""
    now_str = datetime.now().isoformat()
    doc_id = f"doc-{uuid.uuid4().hex[:6]}"
    doc_data = payload.model_dump()
    doc_data.update({
        "doctor_id": doc_id,
        "last_updated_at": now_str,
    })
    saved = repo.save_doctor(doc_data)
    return DoctorAttendance(**saved)


def evaluate_staff_alerts() -> List[Alert]:
    """Generates alerts if doctor duty roster coverage is critically low."""
    alerts = []
    docs = repo.get_doctors()
    now_str = datetime.now().isoformat()

    on_duty_count = sum(1 for d in docs if d.get("is_present") and d.get("status") == "ON_DUTY")

    if on_duty_count == 0:
        alerts.append(Alert(
            id="alert-no-doctors-on-duty",
            severity="DANGER",
            category="STAFF",
            title="Zero Doctors On Duty",
            message="No healthcare medical officers are currently marked ON DUTY! Casualty and OPD are unattended.",
            timestamp=now_str
        ))
    elif on_duty_count == 1:
        alerts.append(Alert(
            id="alert-low-doctor-coverage",
            severity="WARNING",
            category="STAFF",
            title="Minimal Doctor Coverage",
            message="Only 1 medical officer is on duty for the entire facility. High patient wait times expected.",
            timestamp=now_str
        ))

    return alerts
