"""AI Forecasting router utilizing Google Gemini API with heuristic fallback."""
from fastapi import APIRouter, Depends
from app.config import settings
from app.models.schemas import AIPredictionResponse
from app.models.roles import Role, require_roles
from app.services.ai_forecasting import forecast_medicine_demand, forecast_patient_footfall

router = APIRouter(prefix="/api/ai", tags=["AI Forecasting"])


@router.get("/status")
def get_ai_status():
    """Returns AI service capabilities and active configuration."""
    has_gemini = bool(settings.gemini_api_key)
    return {
        "gemini_api_configured": has_gemini,
        "model_name": settings.gemini_model_name,
        "active_mode": "Live Google Gemini AI" if has_gemini else "Built-in Statistical Heuristic Engine",
        "description": "Ready to generate 7-day medicine demand and 72-hour patient footfall surge projections."
    }


@router.post("/forecast/medicines", response_model=AIPredictionResponse)
async def get_medicine_demand_forecast(
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.PHARMACIST])),
):
    """Generates 7-day medicine demand predictions and stockout risk horizon."""
    return await forecast_medicine_demand()


@router.post("/forecast/footfall", response_model=AIPredictionResponse)
async def get_footfall_surge_forecast(
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR])),
):
    """Generates 72-hour patient surge projections and staffing recommendations."""
    return await forecast_patient_footfall()
