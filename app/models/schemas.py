"""Pydantic v2 schemas and data validation models."""
from datetime import datetime, date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class StockStatus(str, Enum):
    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    EXPIRED = "EXPIRED"


class StockAction(str, Enum):
    ADD = "ADD"
    DEDUCT = "DEDUCT"


class MedicineBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of medicine")
    category: str = Field(..., min_length=2, max_length=50, description="Therapeutic category")
    dosage_form: str = Field(..., min_length=2, max_length=30, description="Tablet, Syrup, Injection, etc.")
    current_quantity: int = Field(..., ge=0, description="Available stock units")
    unit: str = Field(default="units", min_length=1, max_length=20, description="Dispensing unit (strip, vial, bottle)")
    reorder_level: int = Field(..., ge=1, description="Minimum safe stock threshold")
    batch_number: str = Field(default="BATCH-GEN", min_length=1, max_length=50)
    expiry_date: str = Field(..., description="Expiry date in YYYY-MM-DD")

    @field_validator("name", "category", "dosage_form")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or only whitespace")
        return cleaned

    @field_validator("expiry_date")
    @classmethod
    def validate_expiry(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Expiry date must be in YYYY-MM-DD format")
        return v


class MedicineCreate(MedicineBase):
    pass


class MedicineItem(MedicineBase):
    id: str
    last_updated_at: str
    status: StockStatus


class MedicineStockUpdate(BaseModel):
    action: StockAction
    quantity: int = Field(..., gt=0, description="Number of units to add or dispense")
    notes: Optional[str] = Field(default=None, max_length=200)


# ============================================================
# Bed Availability Schemas
# ============================================================

class BedWard(BaseModel):
    ward_id: str
    ward_name: str
    total_beds: int = Field(..., ge=1)
    occupied_beds: int = Field(..., ge=0)
    cleaning_beds: int = Field(default=0, ge=0)
    available_beds: int = Field(default=0)
    occupancy_rate: float = Field(default=0.0)
    last_updated_at: str

    @model_validator(mode="after")
    def compute_and_validate(self):
        if self.occupied_beds + self.cleaning_beds > self.total_beds:
            raise ValueError(
                f"Occupied beds ({self.occupied_beds}) + cleaning beds ({self.cleaning_beds}) "
                f"cannot exceed total beds ({self.total_beds}) in ward '{self.ward_name}'"
            )
        self.available_beds = self.total_beds - (self.occupied_beds + self.cleaning_beds)
        self.occupancy_rate = round((self.occupied_beds / self.total_beds) * 100, 1)
        return self


class BedUpdate(BaseModel):
    occupied_beds: int = Field(..., ge=0)
    cleaning_beds: int = Field(default=0, ge=0)


# ============================================================
# Doctor Attendance Schemas
# ============================================================

class DoctorStatus(str, Enum):
    ON_DUTY = "ON_DUTY"
    OFF_DUTY = "OFF_DUTY"
    ON_LEAVE = "ON_LEAVE"


class DoctorAttendance(BaseModel):
    doctor_id: str
    name: str = Field(..., min_length=2, max_length=100)
    specialization: str = Field(..., min_length=2, max_length=100)
    shift: str = Field(default="Morning")
    is_present: bool = True
    room_number: str = Field(default="OPD-1")
    status: DoctorStatus = DoctorStatus.ON_DUTY
    last_updated_at: str


class DoctorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    specialization: str = Field(..., min_length=2, max_length=100)
    shift: str = Field(default="Morning")
    room_number: str = Field(default="OPD-1")
    is_present: bool = True
    status: DoctorStatus = DoctorStatus.ON_DUTY


class DoctorToggleAttendance(BaseModel):
    is_present: bool
    status: Optional[DoctorStatus] = None


# ============================================================
# Footfall Schemas
# ============================================================

class FootfallRecord(BaseModel):
    id: str
    department: str
    patient_count: int = Field(..., ge=0)
    date: str
    hour: int = Field(..., ge=0, le=23)
    recorded_at: str


class FootfallCreate(BaseModel):
    department: str = Field(..., min_length=2, max_length=50)
    patient_count: int = Field(..., ge=1, le=1000)
    date: Optional[str] = None
    hour: Optional[int] = Field(default=None, ge=0, le=23)


# ============================================================
# Alerts Schemas
# ============================================================

class Alert(BaseModel):
    id: str
    severity: str = Field(..., description="DANGER, WARNING, INFO")
    category: str = Field(..., description="MEDICINE, BED, STAFF")
    title: str
    message: str
    timestamp: str


# ============================================================
# Dashboard Aggregated Schema
# ============================================================

class DashboardStats(BaseModel):
    facility_name: str
    current_time: str
    total_beds: int
    occupied_beds: int
    available_beds: int
    bed_occupancy_percent: float
    total_medicines: int
    low_stock_medicines: int
    out_of_stock_medicines: int
    doctors_on_duty: int
    total_doctors: int
    today_footfall: int
    alerts_count: int
    active_alerts: List[Alert]


# ============================================================
# AI Prediction Schemas
# ============================================================

class MedicineForecastItem(BaseModel):
    medicine_name: str
    current_stock: int
    projected_7day_demand: int
    days_until_stockout: int
    suggested_reorder_qty: int
    risk_level: str  # CRITICAL, MODERATE, LOW
    rationale: str


class FootfallForecastItem(BaseModel):
    day_or_window: str
    predicted_patient_count: int
    peak_hours: str
    critical_department: str
    recommended_staff: int


class AIPredictionResponse(BaseModel):
    forecast_type: str
    generated_at: str
    engine_source: str
    summary: str
    medicine_forecasts: Optional[List[MedicineForecastItem]] = None
    footfall_forecasts: Optional[List[FootfallForecastItem]] = None
    recommendations: List[str]
