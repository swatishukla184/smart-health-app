"""Data Repository with Google Cloud Firestore and Zero-Config Local Fallback."""
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.config import settings
from app.database.seed_data import (
    get_initial_medicines,
    get_initial_wards,
    get_initial_doctors,
    get_initial_footfall,
)

logger = logging.getLogger(__name__)


class LocalMemoryStore:
    """Thread-safe in-memory store replicating Firestore collection behavior."""

    def __init__(self):
        self._lock = threading.RLock()
        self.reset()

    def reset(self):
        with self._lock:
            self.medicines: Dict[str, Dict[str, Any]] = {
                m["id"]: dict(m) for m in get_initial_medicines()
            }
            self.wards: Dict[str, Dict[str, Any]] = {
                w["ward_id"]: dict(w) for w in get_initial_wards()
            }
            self.doctors: Dict[str, Dict[str, Any]] = {
                d["doctor_id"]: dict(d) for d in get_initial_doctors()
            }
            self.footfall: List[Dict[str, Any]] = [
                dict(f) for f in get_initial_footfall()
            ]

    # Medicines
    def get_medicines(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.medicines.values())

    def get_medicine(self, med_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.medicines.get(med_id)

    def save_medicine(self, med: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self.medicines[med["id"]] = dict(med)
            return self.medicines[med["id"]]

    def delete_medicine(self, med_id: str) -> bool:
        with self._lock:
            if med_id in self.medicines:
                del self.medicines[med_id]
                return True
            return False

    # Wards
    def get_wards(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.wards.values())

    def get_ward(self, ward_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.wards.get(ward_id)

    def update_ward(self, ward_id: str, occupied: int, cleaning: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            ward = self.wards.get(ward_id)
            if not ward:
                return None
            total = ward["total_beds"]
            if occupied + cleaning > total:
                raise ValueError(f"Occupied ({occupied}) + Cleaning ({cleaning}) exceeds total beds ({total})")
            ward["occupied_beds"] = occupied
            ward["cleaning_beds"] = cleaning
            ward["available_beds"] = total - (occupied + cleaning)
            ward["occupancy_rate"] = round((occupied / total) * 100, 1)
            ward["last_updated_at"] = datetime.now().isoformat()
            return ward

    # Doctors
    def get_doctors(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.doctors.values())

    def get_doctor(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.doctors.get(doc_id)

    def save_doctor(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self.doctors[doc["doctor_id"]] = dict(doc)
            return self.doctors[doc["doctor_id"]]

    def update_doctor_attendance(self, doc_id: str, is_present: bool, status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock:
            doc = self.doctors.get(doc_id)
            if not doc:
                return None
            doc["is_present"] = is_present
            if status:
                doc["status"] = status
            else:
                doc["status"] = "ON_DUTY" if is_present else "OFF_DUTY"
            doc["last_updated_at"] = datetime.now().isoformat()
            return doc

    # Footfall
    def get_footfall(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            # Sort newest first
            sorted_ff = sorted(self.footfall, key=lambda x: x.get("recorded_at", ""), reverse=True)
            return sorted_ff[:limit]

    def add_footfall(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self.footfall.append(dict(entry))
            return entry


class DataRepository:
    """Unified repository routing between Cloud Firestore and Local Memory Store."""

    def __init__(self):
        self.firestore_db = None
        self.local_store = LocalMemoryStore()
        self.is_firestore_active = False
        self._initialize_backend()

    def _initialize_backend(self):
        """Attempts to initialize Firebase Admin / Firestore if configured."""
        if not settings.firebase_project_id:
            logger.info("FIREBASE_PROJECT_ID not set. Using high-performance Local Memory Data Store.")
            return

        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                if settings.firebase_credentials_path:
                    cred = credentials.Certificate(settings.firebase_credentials_path)
                    firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
                else:
                    # Cloud Run default ADC
                    firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})

            self.firestore_db = firestore.client()
            self.is_firestore_active = True
            logger.info("Connected successfully to Google Cloud Firestore.")
            self._ensure_firestore_seeded()
        except Exception as e:
            logger.warning(
                f"Failed to connect to Cloud Firestore ({e}). "
                "Engaging resilient Local Memory Data Store fallback."
            )
            self.is_firestore_active = False

    def _ensure_firestore_seeded(self):
        """Seeds initial data in Firestore if collections are empty."""
        try:
            meds_ref = self.firestore_db.collection("medicines")
            if len(list(meds_ref.limit(1).stream())) == 0:
                logger.info("Seeding initial medicines into Firestore...")
                for med in get_initial_medicines():
                    meds_ref.document(med["id"]).set(med)
            
            wards_ref = self.firestore_db.collection("wards")
            if len(list(wards_ref.limit(1).stream())) == 0:
                logger.info("Seeding initial wards into Firestore...")
                for ward in get_initial_wards():
                    wards_ref.document(ward["ward_id"]).set(ward)

            docs_ref = self.firestore_db.collection("doctors")
            if len(list(docs_ref.limit(1).stream())) == 0:
                logger.info("Seeding initial doctors into Firestore...")
                for doc in get_initial_doctors():
                    docs_ref.document(doc["doctor_id"]).set(doc)
        except Exception as e:
            logger.warning(f"Firestore auto-seed warning: {e}")

    # --- Repository Operations ---

    def get_medicines(self) -> List[Dict[str, Any]]:
        if self.is_firestore_active:
            try:
                docs = self.firestore_db.collection("medicines").stream()
                return [d.to_dict() for d in docs]
            except Exception as e:
                logger.error(f"Firestore get_medicines error: {e}. Falling back to local store.")
        return self.local_store.get_medicines()

    def get_medicine(self, med_id: str) -> Optional[Dict[str, Any]]:
        if self.is_firestore_active:
            try:
                doc = self.firestore_db.collection("medicines").document(med_id).get()
                return doc.to_dict() if doc.exists else None
            except Exception as e:
                logger.error(f"Firestore get_medicine error: {e}. Falling back to local store.")
        return self.local_store.get_medicine(med_id)

    def save_medicine(self, med: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_firestore_active:
            try:
                self.firestore_db.collection("medicines").document(med["id"]).set(med)
                # Keep local mirror up to date
                self.local_store.save_medicine(med)
                return med
            except Exception as e:
                logger.error(f"Firestore save_medicine error: {e}. Falling back to local store.")
        return self.local_store.save_medicine(med)

    def delete_medicine(self, med_id: str) -> bool:
        if self.is_firestore_active:
            try:
                self.firestore_db.collection("medicines").document(med_id).delete()
                self.local_store.delete_medicine(med_id)
                return True
            except Exception as e:
                logger.error(f"Firestore delete_medicine error: {e}. Falling back to local store.")
        return self.local_store.delete_medicine(med_id)

    def get_wards(self) -> List[Dict[str, Any]]:
        if self.is_firestore_active:
            try:
                docs = self.firestore_db.collection("wards").stream()
                return [d.to_dict() for d in docs]
            except Exception as e:
                logger.error(f"Firestore get_wards error: {e}. Falling back to local store.")
        return self.local_store.get_wards()

    def get_ward(self, ward_id: str) -> Optional[Dict[str, Any]]:
        if self.is_firestore_active:
            try:
                doc = self.firestore_db.collection("wards").document(ward_id).get()
                return doc.to_dict() if doc.exists else None
            except Exception as e:
                logger.error(f"Firestore get_ward error: {e}. Falling back to local store.")
        return self.local_store.get_ward(ward_id)

    def update_ward(self, ward_id: str, occupied: int, cleaning: int) -> Optional[Dict[str, Any]]:
        updated = self.local_store.update_ward(ward_id, occupied, cleaning)
        if updated and self.is_firestore_active:
            try:
                self.firestore_db.collection("wards").document(ward_id).set(updated)
            except Exception as e:
                logger.error(f"Firestore update_ward error: {e}")
        return updated

    def get_doctors(self) -> List[Dict[str, Any]]:
        if self.is_firestore_active:
            try:
                docs = self.firestore_db.collection("doctors").stream()
                return [d.to_dict() for d in docs]
            except Exception as e:
                logger.error(f"Firestore get_doctors error: {e}. Falling back to local store.")
        return self.local_store.get_doctors()

    def get_doctor(self, doc_id: str) -> Optional[Dict[str, Any]]:
        if self.is_firestore_active:
            try:
                doc = self.firestore_db.collection("doctors").document(doc_id).get()
                return doc.to_dict() if doc.exists else None
            except Exception as e:
                logger.error(f"Firestore get_doctor error: {e}. Falling back to local store.")
        return self.local_store.get_doctor(doc_id)

    def save_doctor(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_firestore_active:
            try:
                self.firestore_db.collection("doctors").document(doc["doctor_id"]).set(doc)
                self.local_store.save_doctor(doc)
                return doc
            except Exception as e:
                logger.error(f"Firestore save_doctor error: {e}. Falling back to local store.")
        return self.local_store.save_doctor(doc)

    def update_doctor_attendance(self, doc_id: str, is_present: bool, status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        updated = self.local_store.update_doctor_attendance(doc_id, is_present, status)
        if updated and self.is_firestore_active:
            try:
                self.firestore_db.collection("doctors").document(doc_id).set(updated)
            except Exception as e:
                logger.error(f"Firestore update_doctor_attendance error: {e}")
        return updated

    def get_footfall(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.is_firestore_active:
            try:
                docs = self.firestore_db.collection("footfall").order_by(
                    "recorded_at", direction="DESCENDING"
                ).limit(limit).stream()
                return [d.to_dict() for d in docs]
            except Exception as e:
                logger.error(f"Firestore get_footfall error: {e}. Falling back to local store.")
        return self.local_store.get_footfall(limit)

    def add_footfall(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        saved = self.local_store.add_footfall(entry)
        if self.is_firestore_active:
            try:
                self.firestore_db.collection("footfall").document(entry["id"]).set(entry)
            except Exception as e:
                logger.error(f"Firestore add_footfall error: {e}")
        return saved

    def reset_for_tests(self):
        """Resets store back to clean seed data for isolated unit tests."""
        self.local_store.reset()


# Global shared singleton repository
repo = DataRepository()
