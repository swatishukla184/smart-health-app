"""Unit tests for AI Forecasting (Gemini API integration & heuristic fallback)."""
import pytest
from fastapi.testclient import TestClient
from app.services.ai_forecasting import (
    extract_json_from_llm_response,
    generate_heuristic_medicine_forecast,
    generate_heuristic_footfall_forecast,
)
from app.database.firestore_client import repo


def test_json_extraction_from_markdown_fences():
    raw_markdown = """Here is the demand analysis requested:
```json
{
  "summary": "Facility demand is stable.",
  "medicine_forecasts": [
    {
      "medicine_name": "Paracetamol 500mg",
      "current_stock": 850,
      "projected_7day_demand": 400,
      "days_until_stockout": 14,
      "suggested_reorder_qty": 0,
      "risk_level": "LOW",
      "rationale": "Sufficient inventory buffer available."
    }
  ],
  "recommendations": ["Routine inventory audit."]
}
```
Hope this helps!"""
    parsed = extract_json_from_llm_response(raw_markdown)
    assert parsed is not None
    assert parsed["summary"] == "Facility demand is stable."
    assert len(parsed["medicine_forecasts"]) == 1
    assert parsed["medicine_forecasts"][0]["medicine_name"] == "Paracetamol 500mg"


def test_json_extraction_from_bare_json():
    bare_json = '{"key": "value", "count": 42}'
    parsed = extract_json_from_llm_response(bare_json)
    assert parsed == {"key": "value", "count": 42}


def test_heuristic_medicine_forecast():
    meds = repo.get_medicines()
    footfall = repo.get_footfall()
    forecast = generate_heuristic_medicine_forecast(meds, footfall)

    assert forecast.forecast_type == "MEDICINE_DEMAND"
    assert forecast.engine_source == "statistical_heuristic"
    assert len(forecast.medicine_forecasts) >= 10
    assert len(forecast.recommendations) > 0

    # ORS has 0 stock in seed data, so its risk level must be CRITICAL
    ors_forecast = next((m for m in forecast.medicine_forecasts if "Oral Rehydration" in m.medicine_name), None)
    assert ors_forecast is not None
    assert ors_forecast.risk_level == "CRITICAL"
    assert ors_forecast.days_until_stockout == 0
    assert ors_forecast.suggested_reorder_qty > 0


def test_heuristic_footfall_forecast():
    footfall = repo.get_footfall()
    wards = repo.get_wards()
    forecast = generate_heuristic_footfall_forecast(footfall, wards)

    assert forecast.forecast_type == "PATIENT_FOOTFALL"
    assert len(forecast.footfall_forecasts) == 3
    for f in forecast.footfall_forecasts:
        assert f.predicted_patient_count > 0
        assert f.recommended_staff >= 2
        assert len(f.peak_hours) > 0


def test_ai_status_endpoint(client: TestClient):
    resp = client.get("/api/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_mode" in data
    assert "model_name" in data


def test_api_forecast_endpoints(client: TestClient):
    # Test Medicine forecast endpoint (allowed for Pharmacist)
    med_resp = client.post("/api/ai/forecast/medicines", headers={"X-User-Role": "pharmacist"})
    assert med_resp.status_code == 200
    med_data = med_resp.json()
    assert med_data["forecast_type"] == "MEDICINE_DEMAND"
    assert len(med_data["medicine_forecasts"]) > 0

    # Test Footfall forecast endpoint (allowed for Doctor)
    ff_resp = client.post("/api/ai/forecast/footfall", headers={"X-User-Role": "doctor"})
    assert ff_resp.status_code == 200
    ff_data = ff_resp.json()
    assert ff_data["forecast_type"] == "PATIENT_FOOTFALL"
    assert len(ff_data["footfall_forecasts"]) == 3
