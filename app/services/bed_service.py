"""Bed occupancy and ward capacity management service."""
from datetime import datetime
from typing import List
from fastapi import HTTPException, status
from app.database.firestore_client import repo
from app.models.schemas import BedWard, BedUpdate, Alert


def get_all_wards() -> List[BedWard]:
    """Retrieves all wards with real-time occupancy calculations."""
    wards = repo.get_wards()
    return [BedWard(**w) for w in wards]


def get_ward_by_id(ward_id: str) -> BedWard:
    ward = repo.get_ward(ward_id)
    if not ward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ward with ID '{ward_id}' not found."
        )
    return BedWard(**ward)


def update_ward_beds(ward_id: str, payload: BedUpdate) -> BedWard:
    """Updates occupied and cleaning beds with strict capacity bounds checking."""
    ward = repo.get_ward(ward_id)
    if not ward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ward with ID '{ward_id}' not found."
        )

    total = ward["total_beds"]
    if payload.occupied_beds + payload.cleaning_beds > total:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid bed allocation for '{ward['ward_name']}': "
                f"Occupied ({payload.occupied_beds}) + Cleaning ({payload.cleaning_beds}) "
                f"exceeds total capacity ({total} beds)."
            )
        )

    updated = repo.update_ward(ward_id, payload.occupied_beds, payload.cleaning_beds)
    return BedWard(**updated)


def evaluate_bed_alerts() -> List[Alert]:
    """Generates alerts for wards approaching or reaching full capacity."""
    alerts = []
    wards = repo.get_wards()
    now_str = datetime.now().isoformat()

    total_facility_beds = sum(w["total_beds"] for w in wards)
    total_occupied = sum(w["occupied_beds"] for w in wards)

    if total_facility_beds > 0:
        overall_pct = (total_occupied / total_facility_beds) * 100
        if overall_pct >= 90:
            alerts.append(Alert(
                id="alert-facility-capacity-critical",
                severity="DANGER",
                category="BED",
                title="Critical Facility Bed Occupancy",
                message=f"Overall PHC/CHC bed occupancy has reached {overall_pct:.1f}% ({total_occupied}/{total_facility_beds} beds occupied). Activate surge contingency plan.",
                timestamp=now_str
            ))

    for w in wards:
        if w["occupancy_rate"] >= 90.0:
            alerts.append(Alert(
                id=f"alert-bed-{w['ward_id']}",
                severity="DANGER",
                category="BED",
                title=f"Critical Bed Shortage: {w['ward_name']}",
                message=f"{w['ward_name']} is at {w['occupancy_rate']}% capacity ({w['available_beds']} beds left out of {w['total_beds']}).",
                timestamp=now_str
            ))
        elif w["occupancy_rate"] >= 80.0:
            alerts.append(Alert(
                id=f"alert-bed-{w['ward_id']}",
                severity="WARNING",
                category="BED",
                title=f"High Occupancy: {w['ward_name']}",
                message=f"{w['ward_name']} is at {w['occupancy_rate']}% capacity.",
                timestamp=now_str
            ))

    return alerts
