# Medicine Safety Assistant — Implementation Plan

Built with **Gemma 4 via the Gemini API** (API key), developed in **Google Antigravity**.

> Purpose: help elderly patients and caregivers understand handwritten prescriptions and pill packaging, get a simple daily schedule explained by voice in their own language, and see possible conflicts to check with a doctor or pharmacist.
> Scope: decision support and education only. **Not diagnosis or treatment.** Synthetic or public data only.

---

## 1. Key decisions

| Topic | Decision |
|---|---|
| Model access | Gemini API key, Gemma 4 hosted models (e.g. `gemma-4-31b-it` or `gemma-4-26b-a4b-it`; confirm current IDs in Google AI Studio) |
| SDK | `google-genai` (Python) |
| Offline | Not for now. Keep all model calls behind one `llm.py` module so a local backend can be added later without touching the rest |
| Voice | Browser Web Speech API (`SpeechRecognition` + `speechSynthesis`) by default. Try Gemma audio input only if the hosted model supports it |
| Core rule | **The model reads and explains. Code does scheduling, dose-timing logic, and interaction lookups.** |

---

## 2. Architecture

```
Photo -> Preprocess (OpenCV/Pillow)
      -> Gemma 4: extract -> JSON (+ confidence + verbatim source text)
      -> Verify screen (photo beside editable fields; caregiver confirms)
      -> Deterministic code: normalize frequency -> build schedule -> check interactions (local DB)
      -> Gemma 4: explain in patient's language -> TTS voice -> voice Q&A
```

### Project structure

```
medsafe/
  AGENTS.md                # project rules for Antigravity (see section 8)
  .env                     # GEMINI_API_KEY=...  (never commit)
  .gitignore
  backend/
    main.py                # FastAPI app
    llm.py                 # all Gemma calls live here
    schemas.py             # pydantic models
    preprocess.py          # image cleanup
    extract.py             # prescription + strip extraction
    schedule.py            # frequency normalization + daily schedule
    interactions.py        # local interaction lookup
    explain.py             # plain-language explanation + Q&A
    data/
      sig_map.json         # OD, BD, TDS, QID, HS, SOS, AC, PC ... -> times
      interactions.db      # small curated SQLite DB with sources
    tests/
  frontend/                # React + Vite PWA (or plain HTML)
  samples/                 # synthetic prescriptions and strips
  eval/
    run_eval.py            # field-level accuracy on samples
```

---

## 3. Setup

```bash
pip install google-genai fastapi uvicorn pillow opencv-python pydantic python-dotenv pytest
```

`.env`:
```
GEMINI_API_KEY=your_key_here
GEMMA_MODEL=gemma-4-31b-it
```

- Load the key only on the backend. Never expose it to the browser.
- Add `.env` to `.gitignore` before the first commit.

---

## 4. Phases

### Phase 0: Foundations (about 1 hour)
- [ ] Create the repo and folders above
- [ ] Write `AGENTS.md` (section 8) so every Antigravity agent follows the same rules
- [ ] Build `samples/`: 10-15 **synthetic** images (typed, handwritten, mixed-language prescriptions; pill strips). No real patient data.
- [ ] Smoke test: one image sent to Gemma 4 and a text reply printed

### Phase 1: Extraction (most important)
- [ ] `llm.py`: one function `generate(parts, system, json_schema=None)`
- [ ] `schemas.py`: pydantic model for the extraction result
- [ ] `extract.py`: prompt + call + parse + validate, with one retry on invalid JSON
- [ ] `eval/run_eval.py`: compare output with ground-truth JSON for each sample, report field-level error rate

Extraction schema:

```json
{
  "language_detected": "",
  "medicines": [
    {
      "name": "",
      "strength": "",
      "frequency_raw": "",
      "duration": "",
      "instructions": "",
      "source_text": "",
      "confidence": 0.0
    }
  ],
  "unreadable_regions": []
}
```

Extraction prompt rules:
- Transcribe exactly what is written. Copy `source_text` verbatim.
- If a field is unclear, set it to `null` and give a low `confidence`.
- Never infer or "correct" a dose or drug name.
- Output JSON only.

Call sketch (parse and validate defensively; do not assume JSON mode is available on the hosted model):

```python
from google import genai
from PIL import Image
import os, json

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def extract(image_path: str, prompt: str) -> dict:
    img = Image.open(image_path)
    resp = client.models.generate_content(
        model=os.environ.get("GEMMA_MODEL", "gemma-4-31b-it"),
        contents=[img, prompt],
    )
    text = resp.text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(text)   # validate with pydantic; retry once on failure
```

### Phase 2: Verify screen (safety differentiator)
- [ ] Show the photo beside the extracted fields
- [ ] Highlight any field with `confidence` below a threshold (start at 0.8) or `null`
- [ ] User must confirm or edit highlighted fields before continuing
- [ ] Nothing downstream runs on unconfirmed data

### Phase 3: Schedule and interactions (deterministic code)
- [ ] `sig_map.json`: map abbreviations (OD, BD, TDS, QID, HS, SOS, AC, PC, and regional variants) to times and meal anchors
- [ ] `schedule.py`: confirmed medicines -> Morning / Afternoon / Evening / Night slots, with meal-relation flags
- [ ] `interactions.py`: lookup over a small curated SQLite table built from public sources; each row stores its source
- [ ] Output wording is always "possible conflict, check with your pharmacist or doctor", never "stop taking"
- [ ] Gemma may *explain* a flagged conflict but must never *originate* one
- [ ] Unit tests for schedule and interaction logic

### Phase 3b: Pill strips
- [ ] Packaging prompt: name, strength, expiry, batch
- [ ] Cross-check against the confirmed prescription: flag mismatches (e.g. strip 500 mg vs prescription 250 mg)

### Phase 4: Language and voice
- [ ] Detect the patient's language (from extraction or user selection)
- [ ] `explain.py`: short plain-language explanation per medicine (what it is for, when, with or without food), in the patient's language
- [ ] Frontend: "Play aloud" using `speechSynthesis`; "Ask a question" using `SpeechRecognition`
- [ ] Q&A prompt restricted to the confirmed medicine list; anything outside it gets "please ask your doctor or pharmacist"
- [ ] Test at least 2 languages, including one mixed-language prescription

### Phase 5: Caregiver and elder UX
- [ ] Large buttons, high contrast, one action per screen
- [ ] Daily schedule cards (Morning / Afternoon / Night) with a play button
- [ ] Caregiver summary view (printable or exportable)

### Phase 6: Polish and demo
- [ ] Run the eval script, record the accuracy numbers
- [ ] Test the camera flow on a real phone
- [ ] Record the demo (section 7)
- [ ] README with setup, architecture diagram, safety design, limitations

---

## 5. Differentiators (build these in, mention them in the pitch)

1. **Verify-before-trust:** photo beside extracted text, low-confidence fields forced to human confirmation.
2. **Source-cited output:** every instruction shows the verbatim text it came from; if absent, the app says so.
3. **Deterministic safety layer:** scheduling and interaction checks in code and a sourced local DB, not model memory.
4. **Prescription + strip cross-check:** catches mismatches between what was prescribed and what is in the pack.
5. **Local-language, voice-first, caregiver-friendly UX.**
6. **Honest uncertainty:** "unclear, ask your pharmacist" instead of guessing.

---

## 6. Safety rules

- No diagnosis. No advice to change, skip, or stop a dose.
- Every result screen ends with: *"Please confirm with your doctor or pharmacist."*
- Below-threshold confidence means ask the user, never guess.
- No real patient data in the repo, samples, or demo.
- Do not log images or extracted text to external services.

---

## 7. Demo script (about 3 minutes)

1. Elder or caregiver photographs a handwritten prescription.
2. App flags one unclear field. The caregiver corrects it on the verify screen.
3. Daily schedule appears (Morning / Afternoon / Night).
4. Spoken explanation plays in the local language.
5. A pill strip is scanned and a mismatch is flagged.
6. A possible interaction is shown with its source and a "check with your pharmacist" note.
7. Closing slide: eval accuracy numbers and the safety design.

---

## 8. `AGENTS.md` (paste into the repo root for Antigravity)

```markdown
# Project rules

- Project: medicine safety assistant. Decision support only; never diagnose or advise dose changes.
- All model calls go through backend/llm.py. Read GEMINI_API_KEY from the environment. Never hardcode keys or expose them to the frontend.
- The model extracts and explains. Scheduling, dose timing, and interaction checks are deterministic code with unit tests.
- Every extracted field must include source_text and confidence. If unsure, return null and a low confidence. Never guess a drug name or dose.
- Nothing downstream may run on unconfirmed extraction results.
- Interaction results come only from the local DB, with a source shown. Wording: "possible conflict, check with your pharmacist or doctor."
- Use synthetic or public data only. Do not commit real patient data.
- Run pytest and eval/run_eval.py after any prompt or logic change and report results.
- Keep code small and readable. Add or update tests with every change.
```

### Suggested agent split in Antigravity
- **Agent A:** `llm.py`, `extract.py`, `schemas.py`, `eval/run_eval.py`
- **Agent B:** `schedule.py`, `sig_map.json`, `interactions.py`, tests
- **Agent C:** frontend (camera capture, verify screen, schedule cards, voice buttons)
- Review each agent's plan and diff before merging. Test the final UI on a real phone.

---

## 9. Minimum viable version (if time is short)

**Keep:** extraction, verify screen, schedule, one language with voice, 3-5 interaction rules, eval numbers.
**Drop first:** pill strips, extra languages, PDF export.

---

## 10. Later (not now)

- Add a local model backend (Ollama or on-device Gemma 4) behind `llm.py` for true offline use.
- Larger, properly sourced interaction database.
- More languages and regional handwriting samples.
