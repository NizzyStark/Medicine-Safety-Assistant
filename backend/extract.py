import json
import re
from typing import Union
from PIL import Image
from backend.llm import generate
from backend.schemas import ExtractionResult, StripExtractionResult

PRESCRIPTION_EXTRACTION_SYSTEM_PROMPT = """You are a medical document transcription engine designed for medicine safety decision support.
Your task is to transcribe handwritten or typed prescriptions with absolute fidelity.

CRITICAL SAFETY RULES:
1. Never guess, infer, or "correct" a medicine name, dosage, or frequency.
2. Transcribe exactly what is written. Every medicine must include its verbatim `source_text`.
3. If any field (name, strength, frequency, duration, instructions) is unclear, smudged, or missing, set that field to null.
4. Set `confidence` (float between 0.0 and 1.0) honestly:
   - Clear typed/clean text: 0.90 to 1.0
   - Legible handwriting: 0.80 to 0.90
   - Partially ambiguous or questionable handwriting: < 0.80 (e.g. 0.50 or lower)
   - If unsure about the name or dose, confidence MUST be low (< 0.80).
5. Document any illegible regions under `unreadable_regions`.
6. Return valid JSON only, conforming strictly to the requested schema. Do not wrap in markdown or backticks if possible.
"""

EXTRACTION_PROMPT_TEMPLATE = """Extract all medications and details from this prescription into JSON matching this schema:
{
  "language_detected": "language code e.g. en",
  "medicines": [
    {
      "name": "brand or generic name or null",
      "strength": "e.g. 500mg or null",
      "frequency_raw": "e.g. BD, 1-0-1, OD or null",
      "duration": "e.g. 30 days or null",
      "instructions": "e.g. after meals or null",
      "source_text": "verbatim text line from image",
      "confidence": 0.95
    }
  ],
  "unreadable_regions": [
    {
      "description": "description of any illegible parts"
    }
  ]
}
"""

def _clean_json_markdown(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

def extract_prescription(image_input: Union[str, Image.Image]) -> ExtractionResult:
    """
    Extracts prescription details from an image with single-retry defensive parsing.
    """
    if isinstance(image_input, str):
        img = Image.open(image_input)
    else:
        img = image_input

    attempts = 0
    last_error = None
    prompt = EXTRACTION_PROMPT_TEMPLATE

    while attempts < 2:
        attempts += 1
        try:
            raw_output = generate(
                contents=[img, prompt],
                system_instruction=PRESCRIPTION_EXTRACTION_SYSTEM_PROMPT,
                json_mode=True,
            )
            cleaned = _clean_json_markdown(raw_output)
            data = json.loads(cleaned)
            return ExtractionResult.model_validate(data)
        except Exception as e:
            last_error = e
            # On retry, instruct strictly to return valid JSON
            prompt = EXTRACTION_PROMPT_TEMPLATE + f"\nPrevious attempt failed with error: {str(e)}. Please return valid JSON only."

    raise ValueError(f"Failed to extract and validate prescription JSON after retry: {last_error}")

def extract_pill_strip(image_input: Union[str, Image.Image]) -> StripExtractionResult:
    """
    Extracts brand, generic name, strength, batch, and expiry from a pill strip / packaging.
    """
    if isinstance(image_input, str):
        img = Image.open(image_input)
    else:
        img = image_input

    prompt = """Inspect this pill packaging / medicine strip image. Extract the details into JSON:
{
  "brand_name": "string or null",
  "generic_name": "string or null",
  "strength": "e.g. 500mg or null",
  "batch_number": "string or null",
  "expiry_date": "string or null",
  "source_text": "verbatim text visible on strip",
  "confidence": 0.95
}
"""
    raw_output = generate(
        contents=[img, prompt],
        system_instruction="Extract medicine packaging info. Never guess numbers or names. Output JSON only.",
        json_mode=True,
    )
    cleaned = _clean_json_markdown(raw_output)
    data = json.loads(cleaned)
    return StripExtractionResult.model_validate(data)
