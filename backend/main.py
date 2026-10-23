import os
import io
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

from backend.schemas import ExtractionResult, StripExtractionResult, MedicineItem
from backend.extract import extract_prescription, extract_pill_strip
from backend.schedule import build_daily_schedule, DailySchedule
from backend.interactions import check_interactions, InteractionAlert
from backend.explain import explain_schedule, answer_patient_question

app = FastAPI(
    title="Medicine Safety Assistant API",
    description="Decision-support assistant for prescription readability, scheduling, and drug interaction safety checks."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "medicine-safety-assistant"}

@app.post("/api/extract/prescription", response_model=ExtractionResult)
async def api_extract_prescription(file: UploadFile = File(...)):
    """
    Extracts medications from prescription photo.
    Flags confidence < 0.8 and unreadable regions for caregiver confirmation.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        return extract_prescription(image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.post("/api/extract/strip", response_model=StripExtractionResult)
async def api_extract_strip(file: UploadFile = File(...)):
    """
    Extracts pill packaging/strip details (brand, generic, strength, batch, expiry).
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        return extract_pill_strip(image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strip extraction failed: {str(e)}")

class ConfirmRequest(BaseModel):
    confirmed_medicines: List[MedicineItem]
    language: str = "en"

class ScheduleResponse(BaseModel):
    schedule: DailySchedule
    interactions: List[InteractionAlert]
    spoken_explanation: str
    safety_disclaimer: str = "Please confirm with your doctor or pharmacist."

@app.post("/api/process-confirmed", response_model=ScheduleResponse)
def api_process_confirmed(req: ConfirmRequest):
    """
    Downstream processing ONLY runs on confirmed medicines.
    Computes deterministic schedule, local DB interactions, and plain language explanation.
    """
    if not req.confirmed_medicines:
        raise HTTPException(status_code=400, detail="No confirmed medicines provided.")
        
    # 1. Deterministic Daily Schedule
    schedule = build_daily_schedule(req.confirmed_medicines)
    
    # 2. Curated Local DB Interaction Check
    interactions = check_interactions(req.confirmed_medicines)
    
    # 3. Plain language voice-ready explanation
    spoken_explanation = explain_schedule(
        schedule=schedule,
        language=req.language,
        alerts=interactions
    )
    
    return ScheduleResponse(
        schedule=schedule,
        interactions=interactions,
        spoken_explanation=spoken_explanation
    )

class QuestionRequest(BaseModel):
    question: str
    confirmed_medicines: List[MedicineItem]
    language: str = "en"

@app.post("/api/qa")
def api_question_answer(req: QuestionRequest):
    """
    Patient voice/text Q&A restricted solely to confirmed medicines.
    """
    answer = answer_patient_question(
        question=req.question,
        confirmed_medicines=req.confirmed_medicines,
        language=req.language
    )
    return {"answer": answer, "safety_disclaimer": "Please confirm with your doctor or pharmacist."}
