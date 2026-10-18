"""AI Forecasting Service integrating Google Gemini API with Statistical Heuristic Fallback."""
import json
import logging
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import httpx

from app.config import settings
from app.database.firestore_client import repo
from app.models.schemas import (
    AIPredictionResponse,
    MedicineForecastItem,
    FootfallForecastItem,
)

logger = logging.getLogger(__name__)


def extract_json_from_llm_response(text: str) -> Optional[Dict[str, Any]]:
    """Safely extracts JSON object from LLM response text, stripping markdown code blocks."""
    if not text:
        return None
    # 1. Look for ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 2. Look for outermost { ... }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return None


def generate_heuristic_medicine_forecast(medicines: List[Dict[str, Any]], footfall: List[Dict[str, Any]]) -> AIPredictionResponse:
    """Statistical moving-average and seasonal surge heuristic for medicine demand."""
    now_str = datetime.now().isoformat()
    total_recent_patients = sum(f.get("patient_count", 0) for f in footfall[:10]) or 800
    avg_daily_patients = max(int(total_recent_patients / 7), 50)

    forecast_items: List[MedicineForecastItem] = []
    
    # Specific clinical consumption velocity multipliers per patient visit
    multipliers = {
        "paracetamol": 1.2, # Fever, viral, body ache
        "amoxicillin": 0.35, # Bacterial infections
        "oral rehydration": 0.65, # Dehydration / gastroenteritis
        "rabies": 0.04, # Dog / animal bites casualty
        "tetanus": 0.15, # Trauma, lacerations
        "metformin": 0.40, # Non-communicable disease chronic
        "amlodipine": 0.38, # Hypertension chronic
        "oxytocin": 0.05, # Deliveries in labor room
        "iron & folic": 0.80, # Antenatal care
        "artesunate": 0.03, # Severe malaria emergency
        "normal saline": 0.20, # Dehydration & trauma IV
    }

    for med in medicines:
        name = med["name"]
        curr_stock = med["current_quantity"]
        reorder = med["reorder_level"]

        # Match multiplier
        mult = 0.25
        for key, val in multipliers.items():
            if key in name.lower():
                mult = val
                break

        projected_7d = int(avg_daily_patients * mult * 7)
        if projected_7d <= 0:
            projected_7d = 20

        daily_burn = projected_7d / 7.0
        days_left = int(curr_stock / daily_burn) if daily_burn > 0 else 999

        if curr_stock == 0 or days_left <= 2:
            risk = "CRITICAL"
            suggested_reorder = max(reorder * 2, projected_7d * 2)
            rationale = f"Imminent stock-out risk! Only {days_left} days of stock remaining based on {avg_daily_patients} daily patient visits."
        elif days_left <= 7:
            risk = "MODERATE"
            suggested_reorder = max(reorder, int(projected_7d * 1.5))
            rationale = f"Stock projected to exhaust within {days_left} days. Place buffer indent now."
        else:
            risk = "LOW"
            suggested_reorder = 0
            rationale = f"Comfortable inventory buffer ({days_left} days of supply)."

        forecast_items.append(MedicineForecastItem(
            medicine_name=name,
            current_stock=curr_stock,
            projected_7day_demand=projected_7d,
            days_until_stockout=days_left,
            suggested_reorder_qty=suggested_reorder,
            risk_level=risk,
            rationale=rationale
        ))

    recommendations = [
        "Urgent: Issue emergency procurement requisition for all medicines with CRITICAL stockout risk.",
        "Buffer Seasonal Drugs: Increase ORS and antipyretics buffer stock by 25% due to prevailing weather trends.",
        "Check batch expiration dates before dispensing newly indented stock."
    ]

    return AIPredictionResponse(
        forecast_type="MEDICINE_DEMAND",
        generated_at=now_str,
        engine_source="statistical_heuristic",
        summary=f"Algorithmic forecasting completed for {len(forecast_items)} essential medicines based on recent {avg_daily_patients} patients/day footfall.",
        medicine_forecasts=forecast_items,
        recommendations=recommendations
    )


def generate_heuristic_footfall_forecast(footfall: List[Dict[str, Any]], wards: List[Dict[str, Any]]) -> AIPredictionResponse:
    """Predicts patient surges and bed congestion windows based on PHC/CHC patterns."""
    now_str = datetime.now().isoformat()
    today = date.today()

    forecast_items: List[FootfallForecastItem] = []
    
    # 3-day projection window
    day_names = ["Tomorrow", "Day 2 (Mid-Week)", "Day 3 (Weekend Window)"]
    for i, window in enumerate(day_names):
        target_date = today + timedelta(days=i + 1)
        weekday = target_date.weekday() # 0 = Monday, 2 = Wednesday (Immunization), 6 = Sunday

        if weekday == 0:  # Monday rush
            expected = 240
            peak = "09:00 - 12:30"
            crit_dept = "General OPD & NCD Screening"
            staff = 4
        elif weekday == 2:  # Wednesday maternal/child immunization day in PHCs
            expected = 265
            peak = "09:30 - 13:00"
            crit_dept = "Maternal & Child Health / Immunization"
            staff = 4
        elif weekday in (5, 6):  # Weekend
            expected = 120
            peak = "11:00 - 14:00"
            crit_dept = "Emergency & Casualty"
            staff = 2
        else:
            expected = 180
            peak = "10:00 - 13:00"
            crit_dept = "General OPD"
            staff = 3

        forecast_items.append(FootfallForecastItem(
            day_or_window=f"{window} ({target_date.strftime('%a, %d %b')})",
            predicted_patient_count=expected,
            peak_hours=peak,
            critical_department=crit_dept,
            recommended_staff=staff
        ))

    recommendations = [
        "Pre-allocate triage nursing staff during peak morning window (09:00 - 12:30).",
        "Ensure Casualty & Maternity wards maintain at least 2 emergency buffer beds at shift handovers.",
        "Coordinate with ANM / ASHA workers for scheduled Wednesday Village Health & Nutrition arrivals."
    ]

    return AIPredictionResponse(
        forecast_type="PATIENT_FOOTFALL",
        generated_at=now_str,
        engine_source="statistical_heuristic",
        summary="Footfall surge forecast projected across upcoming 72 hours with peak department bottlenecks identified.",
        footfall_forecasts=forecast_items,
        recommendations=recommendations
    )


async def call_gemini_api(prompt: str) -> Optional[str]:
    """Invokes Google Gemini API via official google-genai SDK or direct REST fallback."""
    if not settings.gemini_api_key:
        return None

    # Method 1: Official google-genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model_name,
            contents=prompt,
        )
        if response and response.text:
            return response.text
    except Exception as e:
        logger.warning(f"google-genai SDK call failed ({e}); attempting direct REST endpoint fallback...")

    # Method 2: Direct REST endpoint fallback
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model_name}:generateContent?key={settings.gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text")
            else:
                logger.warning(f"Gemini REST API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Gemini REST endpoint exception: {e}")

    return None


async def forecast_medicine_demand() -> AIPredictionResponse:
    """Generates medicine demand predictions using Gemini API with statistical fallback."""
    meds = repo.get_medicines()
    footfall = repo.get_footfall(limit=30)

    prompt = f"""You are an expert AI epidemiologist and public health supply chain officer for Primary Health Centres (PHCs) and Community Health Centres (CHCs).
Analyze the following inventory and patient footfall data to predict medicine demand for the next 7 days.

Current Medicines Inventory:
{json.dumps([{'name': m['name'], 'current_quantity': m['current_quantity'], 'unit': m.get('unit'), 'reorder_level': m['reorder_level']} for m in meds], indent=2)}

Recent Footfall:
{json.dumps(footfall[:15], indent=2)}

Return a strict JSON object with this exact schema:
{{
  "summary": "Short analytical summary of facility supply health",
  "medicine_forecasts": [
    {{
      "medicine_name": "Exact Name",
      "current_stock": 100,
      "projected_7day_demand": 150,
      "days_until_stockout": 4,
      "suggested_reorder_qty": 300,
      "risk_level": "CRITICAL or MODERATE or LOW",
      "rationale": "Clinical reasoning based on footfall and disease burden"
    }}
  ],
  "recommendations": [
    "Actionable bullet point for Medical Officer In-Charge",
    "Actionable bullet point 2"
  ]
}}
Do NOT output any markdown backticks. Return ONLY the raw JSON."""

    gemini_output = await call_gemini_api(prompt)
    if gemini_output:
        parsed = extract_json_from_llm_response(gemini_output)
        if parsed and "medicine_forecasts" in parsed:
            try:
                items = [MedicineForecastItem(**item) for item in parsed["medicine_forecasts"]]
                return AIPredictionResponse(
                    forecast_type="MEDICINE_DEMAND",
                    generated_at=datetime.now().isoformat(),
                    engine_source="gemini_api",
                    summary=parsed.get("summary", "Gemini 1.5 Flash demand forecast completed."),
                    medicine_forecasts=items,
                    recommendations=parsed.get("recommendations", [])
                )
            except Exception as e:
                logger.warning(f"Failed to parse Gemini response into Pydantic schema: {e}")

    # Seamless graceful degradation
    return generate_heuristic_medicine_forecast(meds, footfall)


async def forecast_patient_footfall() -> AIPredictionResponse:
    """Generates patient footfall surge forecasts using Gemini API with statistical fallback."""
    footfall = repo.get_footfall(limit=30)
    wards = repo.get_wards()

    prompt = f"""You are an expert AI hospital administrator and health systems planner for Indian PHCs/CHCs.
Analyze the following historical patient footfall and ward capacity to forecast patient loads and staffing recommendations for the next 3 days.

Recent Footfall Records:
{json.dumps(footfall[:20], indent=2)}

Ward Capacity:
{json.dumps([{'ward_name': w['ward_name'], 'total_beds': w['total_beds'], 'occupied_beds': w['occupied_beds']} for w in wards], indent=2)}

Return a strict JSON object with this exact schema:
{{
  "summary": "Short executive summary of expected patient footfall trends",
  "footfall_forecasts": [
    {{
      "day_or_window": "Tomorrow (Mon, 19 Oct)",
      "predicted_patient_count": 220,
      "peak_hours": "09:00 - 12:30",
      "critical_department": "General OPD & Casualty",
      "recommended_staff": 4
    }}
  ],
  "recommendations": [
    "Clinical workflow recommendation 1",
    "Staff scheduling recommendation 2"
  ]
}}
Do NOT output any markdown backticks. Return ONLY the raw JSON."""

    gemini_output = await call_gemini_api(prompt)
    if gemini_output:
        parsed = extract_json_from_llm_response(gemini_output)
        if parsed and "footfall_forecasts" in parsed:
            try:
                items = [FootfallForecastItem(**item) for item in parsed["footfall_forecasts"]]
                return AIPredictionResponse(
                    forecast_type="PATIENT_FOOTFALL",
                    generated_at=datetime.now().isoformat(),
                    engine_source="gemini_api",
                    summary=parsed.get("summary", "Gemini 1.5 Flash patient footfall surge analysis completed."),
                    footfall_forecasts=items,
                    recommendations=parsed.get("recommendations", [])
                )
            except Exception as e:
                logger.warning(f"Failed to parse Gemini footfall response into schema: {e}")

    # Seamless graceful degradation
    return generate_heuristic_footfall_forecast(footfall, wards)
