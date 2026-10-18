"""Medicines and inventory management router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from app.models.schemas import MedicineItem, MedicineCreate, MedicineStockUpdate
from app.models.roles import Role, require_roles
from app.services.inventory_service import (
    get_all_medicines,
    get_medicine_by_id,
    add_medicine,
    update_medicine_stock,
    delete_medicine,
)

router = APIRouter(prefix="/api/medicines", tags=["Medicines"])


@router.get("", response_model=List[MedicineItem])
def list_medicines(
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR, Role.PHARMACIST])),
):
    """Lists medicines with optional filtering. Open to all roles."""
    return get_all_medicines(category=category, status_filter=status)


@router.get("/{med_id}", response_model=MedicineItem)
def get_medicine(
    med_id: str,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.DOCTOR, Role.PHARMACIST])),
):
    """Fetches single medicine item."""
    return get_medicine_by_id(med_id)


@router.post("", response_model=MedicineItem, status_code=status.HTTP_201_CREATED)
def create_medicine(
    payload: MedicineCreate,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.PHARMACIST])),
):
    """Adds a new medicine to inventory. Restricted to Pharmacist and Admin."""
    return add_medicine(payload)


@router.put("/{med_id}/stock", response_model=MedicineItem)
def adjust_stock(
    med_id: str,
    payload: MedicineStockUpdate,
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.PHARMACIST])),
):
    """Quick stock adjustment (Dispense / Restock). Restricted to Pharmacist and Admin."""
    return update_medicine_stock(med_id, payload.action, payload.quantity, payload.notes)


@router.delete("/{med_id}", status_code=status.HTTP_200_OK)
def remove_medicine(
    med_id: str,
    current_role: Role = Depends(require_roles([Role.ADMIN])),
):
    """Deletes medicine record. Restricted to Admin only."""
    delete_medicine(med_id)
    return {"message": f"Medicine '{med_id}' deleted successfully."}


@router.get("/export/indent", tags=["Medicines"])
def export_drug_indent_csv(
    current_role: Role = Depends(require_roles([Role.ADMIN, Role.PHARMACIST])),
):
    """
    Generates official NHM District Drug Warehouse Indent Sheet (CSV).
    Computes required procurement quantities for out-of-stock and low-stock drugs.
    """
    import csv
    import io
    from fastapi.responses import Response
    from app.services.inventory_service import get_all_medicines

    meds = get_all_medicines()
    output = io.StringIO()
    writer = csv.writer(output)

    # Official Requisition Header
    writer.writerow([
        "Indent Item ID",
        "Medicine Name & Strength",
        "Therapeutic Category",
        "Dosage Form",
        "Current Available Stock",
        "Dispensing Unit",
        "Minimum Buffer Threshold",
        "Recommended Indent Quantity",
        "Priority Urgency",
        "Batch Number",
        "Expiry Date"
    ])

    for m in meds:
        # Calculate procurement need
        if m.current_quantity == 0:
            indent_qty = m.reorder_level * 2
            urgency = "EMERGENCY - STOCK-OUT"
        elif m.current_quantity <= m.reorder_level:
            indent_qty = (m.reorder_level * 2) - m.current_quantity
            urgency = "URGENT - LOW STOCK"
        else:
            indent_qty = 0
            urgency = "ROUTINE"

        writer.writerow([
            m.id,
            m.name,
            m.category,
            m.dosage_form,
            m.current_quantity,
            m.unit,
            m.reorder_level,
            indent_qty,
            urgency,
            m.batch_number,
            m.expiry_date
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=PHC_CHC_Drug_Warehouse_Indent.csv"
        }
    )

