"""Role definitions and permission dependencies for RBAC."""
from enum import Enum
from typing import List, Optional
from fastapi import Header, HTTPException, status, Depends


class Role(str, Enum):
    """Supported facility user roles."""
    ADMIN = "admin"
    DOCTOR = "doctor"
    PHARMACIST = "pharmacist"


def get_current_role(
    x_user_role: Optional[str] = Header(default="admin", alias="X-User-Role")
) -> Role:
    """
    Extracts and validates the current role from request header.
    Defaults to 'admin' for kiosk / single-click evaluation.
    """
    if not x_user_role:
        return Role.ADMIN
    clean_role = x_user_role.strip().lower()
    try:
        return Role(clean_role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{x_user_role}'. Valid roles: {[r.value for r in Role]}"
        )


def require_roles(allowed_roles: List[Role]):
    """FastAPI dependency to enforce role-based access control."""
    def dependency(current_role: Role = Depends(get_current_role)) -> Role:
        if current_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role '{current_role.value}'. Permitted roles: {[r.value for r in allowed_roles]}"
            )
        return current_role
    return dependency

