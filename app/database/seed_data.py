"""Realistic baseline dataset for PHC/CHC Smart Health facility."""
from datetime import datetime, timedelta, date

def get_initial_medicines():
    today = date.today()
    exp_far = (today + timedelta(days=365)).isoformat()
    exp_near = (today + timedelta(days=45)).isoformat()
    now_str = datetime.now().isoformat()

    return [
        {
            "id": "med-paracetamol-500",
            "name": "Paracetamol 500mg",
            "category": "Analgesic & Antipyretic",
            "dosage_form": "Tablet",
            "current_quantity": 850,
            "unit": "strips",
            "reorder_level": 400,
            "batch_number": "PCM-2026-A1",
            "expiry_date": exp_far,
            "last_updated_at": now_str,
            "status": "IN_STOCK",
        },
        {
            "id": "med-amoxicillin-500",
            "name": "Amoxicillin 500mg",
            "category": "Antibiotic",
            "dosage_form": "Capsule",
            "current_quantity": 40,
            "unit": "strips",
            "reorder_level": 200,
            "batch_number": "AMX-2026-B4",
            "expiry_date": exp_far,
            "last_updated_at": now_str,
            "status": "LOW_STOCK",
        },
        {
            "id": "med-ors-sachets",
            "name": "Oral Rehydration Salts (ORS)",
            "category": "Electrolyte & Hydration",
            "dosage_form": "Sachet",
            "current_quantity": 0,
            "unit": "sachets",
            "reorder_level": 300,
            "batch_number": "ORS-2026-C2",
            "expiry_date": exp_far,
            "last_updated_at": now_str,
            "status": "OUT_OF_STOCK",
        },
        {
            "id": "med-rabies-vaccine",
            "name": "Anti-Rabies Vaccine (ARV) 2.5 IU",
            "category": "Emergency Vaccine",
            "dosage_form": "Vial",
            "current_quantity": 5,
            "unit": "vials",
            "reorder_level": 25,
            "batch_number": "ARV-2026-09",
            "expiry_date": exp_near,
            "last_updated_at": now_str,
            "status": "LOW_STOCK",
        },
        {
            "id": "med-tetanus-toxoid",
            "name": "Tetanus Toxoid 0.5ml",
            "category": "Emergency Vaccine",
            "dosage_form": "Ampoule",
            "current_quantity": 180,
            "unit": "ampoules",
            "reorder_level": 100,
            "batch_number": "TT-2026-X1",
            "expiry_date": exp_far,
            "last_updated_at": now_str,
            "status": "IN_STOCK",
        },
        {
            "id": "med-metformin-500",
            "name": "Metformin 500mg",
            "category": "Chronic Disease (NCD)",
            "dosage_form": "Tablet",
            "current_quantity": 620,
            "unit": "strips",
            "reorder_level": 300,
            "batch_number": "MET-2026-M3",
            "expiry_date": exp_far,
            "last_updated_at": now_str,
            "status": "IN_STOCK",
        },
        {
            "id": "med-amlodipine-5",
            "name": "Amlodipine 5mg",
            "category": "Cardiovascular (NCD)",
            "dosage_form": "Tablet",
            "current_quantity": 540,
            "unit": "strips",
            "reorder_level": 250,
            "batch_number": "AML-2026-N1",
            "expiry_date": exp_far,
            "last_updated_at": now_str,
            "status": "IN_STOCK",
        },
        {
            "id": "med-ifa-tablets",
            "name": "Iron & Folic Acid (IFA) Tablets",
            "category": "Maternal & Child Health",
            "dosage_form": "Tablet",
            "current_quantity": 1200,
            "unit": "strips",
            "reorder_level": 500,
            "batch_number": "IFA-2026-K9",
            "expiry_date": exp_far,
            "last_updated_at": now_str,
            "status": "IN_STOCK",
        },
        {
            "id": "med-oxytocin-inj",
            "name": "Oxytocin Injection 10 IU",
            "category": "Maternal & Child Health",
            "dosage_form": "Ampoule",
            "current_quantity": 8,
            "unit": "ampoules",
            "reorder_level": 30,
            "batch_number": "OXY-2026-L5",
            "expiry_date": exp_near,
            "last_updated_at": now_str,
            "status": "LOW_STOCK",
        },
        {
            "id": "med-artesunate-inj",
            "name": "Artesunate 60mg Injection",
            "category": "Antimalarial Emergency",
            "dosage_form": "Vial",
            "current_quantity": 0,
            "unit": "vials",
            "reorder_level": 20,
            "batch_number": "ART-2026-Z8",
            "expiry_date": exp_far,
            "last_updated_at": now_str,
            "status": "OUT_OF_STOCK",
        },
        {
            "id": "med-iv-normal-saline",
            "name": "Normal Saline (0.9% NaCl) 500ml",
            "category": "IV Fluid",
            "dosage_form": "IV Bottle",
            "current_quantity": 140,
            "unit": "bottles",
            "reorder_level": 80,
            "batch_number": "NS-2026-W3",
            "expiry_date": exp_far,
            "last_updated_at": now_str,
            "status": "IN_STOCK",
        },
    ]


def get_initial_wards():
    now_str = datetime.now().isoformat()
    return [
        {
            "ward_id": "ward-emergency",
            "ward_name": "Emergency & Trauma Care",
            "total_beds": 6,
            "occupied_beds": 5,
            "cleaning_beds": 0,
            "available_beds": 1,
            "occupancy_rate": 83.3,
            "last_updated_at": now_str,
        },
        {
            "ward_id": "ward-gen-male",
            "ward_name": "General Ward - Male",
            "total_beds": 15,
            "occupied_beds": 11,
            "cleaning_beds": 1,
            "available_beds": 3,
            "occupancy_rate": 73.3,
            "last_updated_at": now_str,
        },
        {
            "ward_id": "ward-gen-female",
            "ward_name": "General Ward - Female",
            "total_beds": 15,
            "occupied_beds": 9,
            "cleaning_beds": 2,
            "available_beds": 4,
            "occupancy_rate": 60.0,
            "last_updated_at": now_str,
        },
        {
            "ward_id": "ward-maternity",
            "ward_name": "Maternity & Labour Care",
            "total_beds": 8,
            "occupied_beds": 7,
            "cleaning_beds": 0,
            "available_beds": 1,
            "occupancy_rate": 87.5,
            "last_updated_at": now_str,
        },
        {
            "ward_id": "ward-pediatric",
            "ward_name": "Pediatric Ward",
            "total_beds": 10,
            "occupied_beds": 6,
            "cleaning_beds": 1,
            "available_beds": 3,
            "occupancy_rate": 60.0,
            "last_updated_at": now_str,
        },
        {
            "ward_id": "ward-hdu",
            "ward_name": "High Dependency Unit (HDU)",
            "total_beds": 4,
            "occupied_beds": 3,
            "cleaning_beds": 0,
            "available_beds": 1,
            "occupancy_rate": 75.0,
            "last_updated_at": now_str,
        },
    ]


def get_initial_doctors():
    now_str = datetime.now().isoformat()
    return [
        {
            "doctor_id": "doc-ramesh",
            "name": "Dr. Ramesh Verma",
            "specialization": "General Medicine / MOIC",
            "shift": "Morning (08:00 - 14:00)",
            "room_number": "OPD Room 1",
            "is_present": True,
            "status": "ON_DUTY",
            "last_updated_at": now_str,
        },
        {
            "doctor_id": "doc-priya",
            "name": "Dr. Priya Sharma",
            "specialization": "Obstetrics & Gynecology (OBGYN)",
            "shift": "Morning (08:00 - 14:00)",
            "room_number": "Maternity Wing",
            "is_present": True,
            "status": "ON_DUTY",
            "last_updated_at": now_str,
        },
        {
            "doctor_id": "doc-arvind",
            "name": "Dr. Arvind Patel",
            "specialization": "Pediatrics & Child Health",
            "shift": "Morning (08:00 - 14:00)",
            "room_number": "OPD Room 2",
            "is_present": False,
            "status": "OFF_DUTY",
            "last_updated_at": now_str,
        },
        {
            "doctor_id": "doc-neha",
            "name": "Dr. Neha Gupta",
            "specialization": "Emergency & Casualty Medical Officer",
            "shift": "Day Shift (08:00 - 20:00)",
            "room_number": "Casualty Bay",
            "is_present": True,
            "status": "ON_DUTY",
            "last_updated_at": now_str,
        },
        {
            "doctor_id": "doc-suresh",
            "name": "Dr. Suresh Nair",
            "specialization": "AYUSH Medical Officer",
            "shift": "Evening (14:00 - 20:00)",
            "room_number": "OPD Room 3",
            "is_present": False,
            "status": "OFF_DUTY",
            "last_updated_at": now_str,
        },
    ]


def get_initial_footfall():
    today = date.today()
    records = []
    
    # 7-day historical simulated footfall
    daily_distributions = [
        (6, 142), # 6 days ago
        (5, 168), # 5 days ago
        (4, 185), # 4 days ago
        (3, 192), # 3 days ago
        (2, 210), # 2 days ago (e.g. Immunization day)
        (1, 155), # yesterday
        (0, 118), # today so far
    ]

    for days_ago, total in daily_distributions:
        d = (today - timedelta(days=days_ago)).isoformat()
        records.append({
            "id": f"ff-{d}-opd",
            "department": "General OPD",
            "patient_count": int(total * 0.65),
            "date": d,
            "hour": 10,
            "recorded_at": f"{d}T10:00:00",
        })
        records.append({
            "id": f"ff-{d}-emergency",
            "department": "Emergency & Casualty",
            "patient_count": int(total * 0.15),
            "date": d,
            "hour": 11,
            "recorded_at": f"{d}T11:00:00",
        })
        records.append({
            "id": f"ff-{d}-mch",
            "department": "Maternal & Child Health",
            "patient_count": int(total * 0.20),
            "date": d,
            "hour": 11,
            "recorded_at": f"{d}T11:30:00",
        })

    return records
