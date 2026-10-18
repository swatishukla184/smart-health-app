"""Doctor roster and real-time attendance router."""
from typing import List
from fastapi import APIRouter, Depends, status
from app.models.schemas import DoctorAttendance, DoctorCreate, DoctorToggleAttendance
from app.models.roles import Role, require_roles
from app.services.attendance_service import (
    get_all_doctors,
    get_doctor_by_id,
    toggle_doctor_attendance,
    add_doctor,
)

router = APIRouter(prefix="/api/doctors", tags=["Doctors & Attendance"])


@router.get("", response_model=List[DoctorAttendance])
def list_doctors(
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR, Role.PHARMACIST])),
):
    """View active doctor roster and duty status."""
    return get_all_doctors()


@router.get("/{doc_id}", response_model=DoctorAttendance)
def get_doctor(
    doc_id: str,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR, Role.PHARMACIST])),
):
    return get_doctor_by_id(doc_id)


@router.post("/{doc_id}/toggle-attendance", response_model=DoctorAttendance)
def toggle_attendance(
    doc_id: str,
    payload: DoctorToggleAttendance,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR])),
):
    """
    Check-in or check-out doctor attendance.
    Restricted to Doctor and Admin.
    """
    return toggle_doctor_attendance(doc_id, payload.is_present, payload.status)


@router.post("", response_model=DoctorAttendance, status_code=status.HTTP_201_CREATED)
def create_doctor(
    payload: DoctorCreate,
    current_role: Role = Depends(require_roles([Role.ADMIN])),
):
    """Adds a new doctor to the roster. Restricted to Admin only."""
    return add_doctor(payload)
