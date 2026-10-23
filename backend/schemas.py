from typing import List, Optional
from pydantic import BaseModel, Field

class MedicineItem(BaseModel):
    name: Optional[str] = Field(
        None, 
        description="Brand or generic name of medicine. Null if unreadable."
    )
    strength: Optional[str] = Field(
        None, 
        description="Dosage strength (e.g. '500mg', '20mg'). Null if unreadable."
    )
    frequency_raw: Optional[str] = Field(
        None, 
        description="Prescribed frequency abbreviation or text (e.g. 'BD', 'OD after meals'). Null if unreadable."
    )
    duration: Optional[str] = Field(
        None, 
        description="Duration prescribed (e.g. '30 days', '5 days'). Null if unreadable."
    )
    instructions: Optional[str] = Field(
        None, 
        description="Additional directions (e.g. 'after lunch', 'with warm water')."
    )
    source_text: str = Field(
        ..., 
        description="Exact verbatim line/words from prescription backing this medicine entry."
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score from 0.0 to 1.0. If unsure about name or dose, must be low (<0.8)."
    )
    pill_visual: Optional[str] = Field(
        None,
        description="Optional visual descriptor like '🟡 Yellow round tablet', '⚪ White capsule'."
    )

class UnreadableRegion(BaseModel):
    description: str = Field(
        ..., 
        description="Description or location of unreadable or smudged handwriting on the prescription."
    )

class ExtractionResult(BaseModel):
    language_detected: str = Field(
        default="en", 
        description="Language detected on the prescription (e.g. 'en', 'es', 'hi')."
    )
    medicines: List[MedicineItem] = Field(
        default_factory=list, 
        description="List of extracted medications."
    )
    unreadable_regions: List[UnreadableRegion] = Field(
        default_factory=list, 
        description="List of regions that could not be deciphered safely."
    )

# Schema for packaging / strip inspection (Phase 3b)
class StripExtractionResult(BaseModel):
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    source_text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
