import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
from backend.schemas import MedicineItem

DATA_DIR = Path(__file__).resolve().parent / "data"

def load_sig_map() -> Dict[str, dict]:
    sig_path = DATA_DIR / "sig_map.json"
    if not sig_path.exists():
        return {}
    with open(sig_path, "r", encoding="utf-8") as f:
        return json.load(f)

class ScheduledDose(BaseModel):
    medicine_name: str
    strength: Optional[str] = None
    meal_relation: str  # "before_meal", "after_meal", "with_meal", "bedtime", "unspecified"
    instructions: Optional[str] = None
    raw_frequency: Optional[str] = None
    pill_visual: Optional[str] = None

class DailySchedule(BaseModel):
    morning: List[ScheduledDose] = []
    afternoon: List[ScheduledDose] = []
    evening: List[ScheduledDose] = []
    night: List[ScheduledDose] = []
    as_needed: List[ScheduledDose] = []
    unassigned: List[ScheduledDose] = []

def determine_meal_relation(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ["hs", "bedtime", "night"]):
        return "bedtime"
    if any(k in lower for k in ["ac", "before meal", "before food", "empty stomach"]):
        return "before_meal"
    if any(k in lower for k in ["pc", "after meal", "after lunch", "after dinner", "after breakfast", "after food"]):
        return "after_meal"
    if any(k in lower for k in ["with meal", "with food"]):
        return "with_meal"
    return "unspecified"

def normalize_frequency(freq_raw: Optional[str], instructions: Optional[str] = None) -> List[str]:
    """
    Deterministic rule engine mapping frequency strings and instructions to daily time slots.
    Considers meal anchors (lunch, dinner, breakfast, bedtime, evening, etc.).
    """
    combined = f"{freq_raw or ''} {instructions or ''}".strip().lower()
    if not combined:
        return ["unassigned"]

    # 1. Check for explicit meal or time-of-day anchors in the text
    has_lunch = any(k in combined for k in ["lunch", "afternoon", "midday", "noon"])
    has_breakfast = any(k in combined for k in ["breakfast", "morning", "mane"])
    has_dinner = any(k in combined for k in ["dinner", "evening", "nocte", "night", "bedtime", "hs"])
    
    # 2. Check 3-part or 4-part numeric patterns like 1-0-1, 0-1-0, 1-1-1, 0-0-1, 1-0-0
    pattern_match = re.search(r"\b([0-9])-([0-9])-([0-9])\b", combined)
    if pattern_match:
        slots = []
        m, a, n = pattern_match.groups()
        if int(m) > 0: slots.append("morning")
        if int(a) > 0: slots.append("afternoon")
        if int(n) > 0: slots.append("night")
        return slots or ["unassigned"]

    # Pattern match for 4-part: 1-0-1-1 etc.
    pattern_4 = re.search(r"\b([0-9])-([0-9])-([0-9])-([0-9])\b", combined)
    if pattern_4:
        slots = []
        m, a, e, n = pattern_4.groups()
        if int(m) > 0: slots.append("morning")
        if int(a) > 0: slots.append("afternoon")
        if int(e) > 0: slots.append("evening")
        if int(n) > 0: slots.append("night")
        return slots or ["unassigned"]

    # 3. As needed / SOS / PRN
    if any(k in combined for k in ["sos", "prn", "as needed", "when needed", "if needed"]):
        return ["as_needed"]

    # 4. Check 4 times daily (QID) first
    if any(k in combined for k in ["qid", "4 times a day", "4 times daily", "4 times"]):
        return ["morning", "afternoon", "evening", "night"]

    # 5. Check 3 times daily (TDS / TID / 3 times a day) BEFORE "daily" or "day" match!
    if any(k in combined for k in ["tds", "tid", "thrice daily", "thrice a day", "3 times a day", "3 times daily", "3 times"]):
        return ["morning", "afternoon", "night"]

    # 6. Check 2 times daily (BD / BID / twice daily) BEFORE "daily" or "day" match!
    if any(k in combined for k in ["bd", "bid", "twice daily", "twice a day", "2 times a day", "2 times daily", "2 times"]):
        if has_lunch and has_dinner:
            return ["afternoon", "night"]
        return ["morning", "night"]

    # 7. Bedtime / Night only (HS)
    if any(k in combined for k in ["hs", "bedtime", "at night", "before sleep"]):
        return ["night"]

    # 8. OD / Once daily
    if any(k in combined for k in ["od", "once daily", "once a day", "1 time a day", "1 time daily", "1 time", "daily"]):
        if has_lunch:
            return ["afternoon"]
        if has_dinner or "night" in combined:
            return ["night"]
        if any(k in combined for k in ["evening", "tea"]):
            return ["evening"]
        # Default OD is morning (e.g. after breakfast)
        return ["morning"]

    # 9. Fallback to exact dictionary lookup from sig_map.json
    sig_map = load_sig_map()
    cleaned_upper = (freq_raw or '').strip().upper()
    if cleaned_upper in sig_map:
        return sig_map[cleaned_upper]["slots"]

    # 10. Direct single anchor match
    if has_lunch:
        return ["afternoon"]
    if has_breakfast:
        return ["morning"]
    if has_dinner:
        return ["night"]

    return ["unassigned"]

def build_daily_schedule(confirmed_medicines: List[MedicineItem]) -> DailySchedule:
    """
    Constructs a deterministic 4-part schedule + as_needed from verified medicines.
    """
    schedule = DailySchedule()
    
    for med in confirmed_medicines:
        if not med.name:
            continue
            
        full_text = f"{med.frequency_raw or ''} {med.instructions or ''}"
        meal_relation = determine_meal_relation(full_text)
        
        dose = ScheduledDose(
            medicine_name=med.name,
            strength=med.strength,
            meal_relation=meal_relation,
            instructions=med.instructions,
            raw_frequency=med.frequency_raw,
            pill_visual=med.pill_visual
        )
        
        slots = normalize_frequency(med.frequency_raw, med.instructions)
        
        for slot in slots:
            if slot == "morning":
                schedule.morning.append(dose)
            elif slot == "afternoon":
                schedule.afternoon.append(dose)
            elif slot == "evening":
                schedule.evening.append(dose)
            elif slot == "night":
                schedule.night.append(dose)
            elif slot == "as_needed":
                schedule.as_needed.append(dose)
            else:
                schedule.unassigned.append(dose)
                
    return schedule
