"""Patient footfall logging and trend router."""
from typing import List
from fastapi import APIRouter, Depends, status
from app.models.schemas import FootfallRecord, FootfallCreate
from app.models.roles import Role, require_roles
from app.services.footfall_service import get_recent_footfall, record_patient_footfall

router = APIRouter(prefix="/api/footfall", tags=["Footfall"])


@router.get("", response_model=List[FootfallRecord])
def list_footfall(
    limit: int = 50,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR, Role.PHARMACIST])),
):
    """Retrieves recent footfall activity."""
    return get_recent_footfall(limit=limit)


@router.post("", response_model=FootfallRecord, status_code=status.HTTP_201_CREATED)
def log_footfall(
    payload: FootfallCreate,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR, Role.PHARMACIST])),
):
    """Registers new patient arrival count in a department."""
    return record_patient_footfall(payload)
