"""Inventory management service with real-time stock alert evaluation."""
import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from app.config import settings
from app.database.firestore_client import repo
from app.models.schemas import (
    MedicineItem,
    MedicineCreate,
    StockStatus,
    StockAction,
    Alert,
)


def compute_stock_status(quantity: int, reorder_level: int, expiry_date_str: str) -> StockStatus:
    """Calculates operational stock status based on quantity and expiration date."""
    try:
        exp_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        if exp_date <= date.today():
            return StockStatus.EXPIRED
    except Exception:
        pass

    if quantity <= 0:
        return StockStatus.OUT_OF_STOCK
    elif quantity <= reorder_level:
        return StockStatus.LOW_STOCK
    return StockStatus.IN_STOCK


def get_all_medicines(category: Optional[str] = None, status_filter: Optional[str] = None) -> List[MedicineItem]:
    """Retrieves all medicines with optional category and status filtering."""
    raw_list = repo.get_medicines()
    items = []
    for item in raw_list:
        current_status = compute_stock_status(
            item["current_quantity"], item["reorder_level"], item["expiry_date"]
        )
        item["status"] = current_status.value
        if category and item.get("category", "").lower() != category.lower():
            continue
        if status_filter and current_status.value.lower() != status_filter.lower():
            continue
        items.append(MedicineItem(**item))
    return items


def get_medicine_by_id(med_id: str) -> MedicineItem:
    item = repo.get_medicine(med_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID '{med_id}' not found."
        )
    item["status"] = compute_stock_status(
        item["current_quantity"], item["reorder_level"], item["expiry_date"]
    ).value
    return MedicineItem(**item)


def add_medicine(payload: MedicineCreate) -> MedicineItem:
    """Creates a new medicine inventory item."""
    now_str = datetime.now().isoformat()
    med_id = f"med-{uuid.uuid4().hex[:8]}"
    item_status = compute_stock_status(
        payload.current_quantity, payload.reorder_level, payload.expiry_date
    )
    
    data = payload.model_dump()
    data.update({
        "id": med_id,
        "last_updated_at": now_str,
        "status": item_status.value,
    })
    saved = repo.save_medicine(data)
    return MedicineItem(**saved)


def update_medicine_stock(med_id: str, action: StockAction, quantity: int, notes: Optional[str] = None) -> MedicineItem:
    """
    Adjusts stock quantity safely with bounds checking.
    Rejects over-dispensation with a clear HTTP 400 error.
    """
    item = repo.get_medicine(med_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID '{med_id}' not found."
        )

    current_qty = item["current_quantity"]
    unit = item.get("unit", "units")

    if action == StockAction.DEDUCT:
        if quantity > current_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot dispense {quantity} {unit}; only {current_qty} {unit} available in stock."
            )
        new_qty = current_qty - quantity
    else:  # ADD
        new_qty = current_qty + quantity

    item_status = compute_stock_status(new_qty, item["reorder_level"], item["expiry_date"])
    now_str = datetime.now().isoformat()

    item["current_quantity"] = new_qty
    item["status"] = item_status.value
    item["last_updated_at"] = now_str

    saved = repo.save_medicine(item)
    return MedicineItem(**saved)


def delete_medicine(med_id: str) -> bool:
    success = repo.delete_medicine(med_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID '{med_id}' not found."
        )
    return True


def evaluate_stock_alerts() -> List[Alert]:
    """Generates active low-stock, stock-out, and impending expiry alerts."""
    alerts = []
    meds = repo.get_medicines()
    today = date.today()
    exp_warning_limit = today + timedelta(days=settings.expiry_warning_days)

    for m in meds:
        qty = m["current_quantity"]
        reorder = m["reorder_level"]
        name = m["name"]
        unit = m.get("unit", "units")
        now_str = datetime.now().isoformat()

        # Check Expiry
        try:
            exp_date = datetime.strptime(m["expiry_date"], "%Y-%m-%d").date()
            if exp_date <= today:
                alerts.append(Alert(
                    id=f"alert-exp-{m['id']}",
                    severity="DANGER",
                    category="MEDICINE",
                    title="Medicine Expired",
                    message=f"{name} (Batch {m.get('batch_number')}) expired on {m['expiry_date']}. Quarantine immediately.",
                    timestamp=now_str
                ))
            elif exp_date <= exp_warning_limit:
                alerts.append(Alert(
                    id=f"alert-near-exp-{m['id']}",
                    severity="WARNING",
                    category="MEDICINE",
                    title="Impending Expiry",
                    message=f"{name} expires soon on {m['expiry_date']} ({qty} {unit} remaining).",
                    timestamp=now_str
                ))
        except Exception:
            pass

        # Check Stock Level
        if qty == 0:
            alerts.append(Alert(
                id=f"alert-out-{m['id']}",
                severity="DANGER",
                category="MEDICINE",
                title="Stock-Out Emergency",
                message=f"Critical medicine '{name}' is completely OUT OF STOCK! Reorder immediately.",
                timestamp=now_str
            ))
        elif qty <= reorder:
            severity = "DANGER" if qty <= (reorder * 0.4) else "WARNING"
            alerts.append(Alert(
                id=f"alert-low-{m['id']}",
                severity=severity,
                category="MEDICINE",
                title="Low Stock Alert",
                message=f"'{name}' is below reorder threshold ({qty} {unit} remaining, reorder level: {reorder}).",
                timestamp=now_str
            ))

    return alerts
