"""Ward bed capacity and occupancy management router."""
from typing import List
from fastapi import APIRouter, Depends
from app.models.schemas import BedWard, BedUpdate
from app.models.roles import Role, require_roles
from app.services.bed_service import get_all_wards, get_ward_by_id, update_ward_beds

router = APIRouter(prefix="/api/beds", tags=["Beds & Wards"])


@router.get("", response_model=List[BedWard])
def list_wards(
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR, Role.PHARMACIST])),
):
    """Returns ward-wise bed occupancy. Available to all healthcare roles."""
    return get_all_wards()


@router.get("/{ward_id}", response_model=BedWard)
def get_ward(
    ward_id: str,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR, Role.PHARMACIST])),
):
    return get_ward_by_id(ward_id)


@router.put("/{ward_id}", response_model=BedWard)
def update_beds(
    ward_id: str,
    payload: BedUpdate,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR])),
):
    """
    Updates occupied and cleaning beds for a ward.
    Restricted to Doctor and Admin.
    """
    return update_ward_beds(ward_id, payload)
