"""Patient footfall recording and trend aggregation service."""
import uuid
from datetime import datetime, date
from typing import List
from app.database.firestore_client import repo
from app.models.schemas import FootfallRecord, FootfallCreate


def get_recent_footfall(limit: int = 50) -> List[FootfallRecord]:
    raw_list = repo.get_footfall(limit)
    return [FootfallRecord(**r) for r in raw_list]


def record_patient_footfall(payload: FootfallCreate) -> FootfallRecord:
    """Records real-time patient admissions / OPD registrations."""
    now = datetime.now()
    entry_date = payload.date if payload.date else date.today().isoformat()
    entry_hour = payload.hour if payload.hour is not None else now.hour

    entry_id = f"ff-{uuid.uuid4().hex[:8]}"
    entry = {
        "id": entry_id,
        "department": payload.department.strip(),
        "patient_count": payload.patient_count,
        "date": entry_date,
        "hour": entry_hour,
        "recorded_at": now.isoformat(),
    }
    saved = repo.add_footfall(entry)
    return FootfallRecord(**saved)


def get_today_total_footfall() -> int:
    """Calculates total patient visits registered today."""
    today_str = date.today().isoformat()
    records = repo.get_footfall(limit=100)
    return sum(r["patient_count"] for r in records if r.get("date") == today_str)
