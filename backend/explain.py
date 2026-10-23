from typing import List, Optional
from backend.schemas import MedicineItem
from backend.schedule import DailySchedule
from backend.interactions import InteractionAlert
from backend.llm import generate

EXPLAIN_SYSTEM_PROMPT = """You are a compassionate, clear healthcare communicator helping elderly patients and family caregivers.
Explain medicine schedules in simple, plain language without medical jargon.

STRICT SAFETY BOUNDARIES:
1. Decision support and education only. NEVER diagnose or advise dose modifications.
2. Only speak about medicines that are explicitly listed in the confirmed schedule.
3. If asked about unlisted drugs or unknown symptoms, instruct the user: "Please consult your doctor or pharmacist."
4. Always conclude any spoken or written explanation with: "Please confirm with your doctor or pharmacist."
"""

LANGUAGE_NAME_MAP = {
    "en": "English",
    "hi": "Hindi (हिंदी)"
}

def explain_schedule(
    schedule: DailySchedule,
    language: str = "en",
    alerts: Optional[List[InteractionAlert]] = None
) -> str:
    """
    Produces a patient-friendly plain-language explanation of their daily routine in their language.
    """
    target_lang_name = LANGUAGE_NAME_MAP.get(language, language)
    schedule_summary = []
    
    if schedule.morning:
        meds = ", ".join([f"{d.medicine_name} ({d.strength or ''}, {d.meal_relation.replace('_', ' ')})" for d in schedule.morning])
        schedule_summary.append(f"Morning: {meds}")
    if schedule.afternoon:
        meds = ", ".join([f"{d.medicine_name} ({d.strength or ''}, {d.meal_relation.replace('_', ' ')})" for d in schedule.afternoon])
        schedule_summary.append(f"Afternoon: {meds}")
    if schedule.evening:
        meds = ", ".join([f"{d.medicine_name} ({d.strength or ''}, {d.meal_relation.replace('_', ' ')})" for d in schedule.evening])
        schedule_summary.append(f"Evening: {meds}")
    if schedule.night:
        meds = ", ".join([f"{d.medicine_name} ({d.strength or ''}, {d.meal_relation.replace('_', ' ')})" for d in schedule.night])
        schedule_summary.append(f"Night / Bedtime: {meds}")
    if schedule.as_needed:
        meds = ", ".join([f"{d.medicine_name} ({d.strength or ''})" for d in schedule.as_needed])
        schedule_summary.append(f"As needed: {meds}")

    prompt = f"""IMPORTANT: You must write your entire response completely in {target_lang_name}.

Confirmed Schedule:
{chr(10).join(schedule_summary)}

Potential conflicts noted from pharmacist DB:
{chr(10).join([f"- {a.drug_a} & {a.drug_b}: {a.description} (Source: {a.source})" for a in (alerts or [])]) if alerts else "None"}

Please produce a short, warm, step-by-step spoken daily routine guide in {target_lang_name} for an elderly patient.
Explain clearly when to take each pill (morning, afternoon, or night) and whether with food.
Conclude strictly with the translation of: "Please confirm with your doctor or pharmacist." in {target_lang_name}.
"""
    return generate(
        contents=[prompt],
        system_instruction=EXPLAIN_SYSTEM_PROMPT,
        json_mode=False
    )

def answer_patient_question(
    question: str,
    confirmed_medicines: List[MedicineItem],
    language: str = "en"
) -> str:
    """
    Restricted voice/text Q&A over confirmed medicines only.
    """
    target_lang_name = LANGUAGE_NAME_MAP.get(language, language)
    med_context = "\n".join([
        f"- {m.name} {m.strength or ''}: instructions='{m.instructions or ''}', frequency='{m.frequency_raw or ''}'"
        for m in confirmed_medicines
    ])
    
    prompt = f"""IMPORTANT: You must write your entire response completely in {target_lang_name}.

The patient asks: "{question}"

Confirmed medicines:
{med_context}

Answer their question warmly and concisely in {target_lang_name} based ONLY on their confirmed prescription details.
If the question is about changing dosage, skipping pills, unlisted drugs, or serious medical advice, politely reply in {target_lang_name} that they must check with their doctor or pharmacist.
"""
    return generate(
        contents=[prompt],
        system_instruction=EXPLAIN_SYSTEM_PROMPT,
        json_mode=False
    )
