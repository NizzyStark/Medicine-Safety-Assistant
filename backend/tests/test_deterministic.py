import pytest
from backend.schemas import MedicineItem
from backend.schedule import normalize_frequency, determine_meal_relation, build_daily_schedule
from backend.interactions import check_interactions
from backend.init_db import init_db

def test_normalize_frequency():
    assert "morning" in normalize_frequency("OD")
    assert "afternoon" in normalize_frequency("OD", "after lunch")
    assert "morning" in normalize_frequency("BD") and "night" in normalize_frequency("BD")
    assert "night" in normalize_frequency("HS")
    assert "as_needed" in normalize_frequency("SOS")
    assert "morning" in normalize_frequency("1-0-1") and "night" in normalize_frequency("1-0-1")
    assert "afternoon" in normalize_frequency("0-1-0")
    # Multi-word frequencies
    slots_3x = normalize_frequency("3 times a day", "after food")
    assert "morning" in slots_3x and "afternoon" in slots_3x and "night" in slots_3x

def test_determine_meal_relation():
    assert determine_meal_relation("1 tab after meals") == "after_meal"
    assert determine_meal_relation("before food AC") == "before_meal"
    assert determine_meal_relation("HS at bedtime") == "bedtime"
    assert determine_meal_relation("just swallow") == "unspecified"

def test_build_daily_schedule():
    meds = [
        MedicineItem(name="Metformin", strength="500mg", frequency_raw="BD", source_text="Metformin 500 BD", confidence=0.9),
        MedicineItem(name="Atorvastatin", strength="20mg", frequency_raw="HS", instructions="bedtime", source_text="Atorva 20 HS", confidence=0.95),
    ]
    schedule = build_daily_schedule(meds)
    
    assert len(schedule.morning) == 1
    assert schedule.morning[0].medicine_name == "Metformin"
    assert len(schedule.night) == 2  # Metformin (BD) + Atorvastatin (HS)

def test_interactions_check():
    # Aspirin + Ibuprofen conflict
    meds = [
        MedicineItem(name="Aspirin", strength="75mg", frequency_raw="OD", source_text="Aspirin 75", confidence=0.95),
        MedicineItem(name="Ibuprofen", strength="400mg", frequency_raw="SOS", source_text="Ibuprofen 400", confidence=0.9),
    ]
    alerts = check_interactions(meds)
    assert len(alerts) >= 1
    assert "possible conflict" in alerts[0].message
    assert "FDA" in alerts[0].source or "DailyMed" in alerts[0].source
