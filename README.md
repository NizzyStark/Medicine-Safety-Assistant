# MedSafe: Medicine Safety Assistant

A private-by-design healthcare assistant that helps elderly patients and caregivers understand prescriptions and pill packaging. Take a photo, confirm what was read, get a structured daily routine explained by voice in your preferred language, and detect potential drug interactions to check with a doctor or pharmacist.

Built with **Gemma 4** (`gemma-4-31b-it` & `gemma-4-26b-a4b-it`) via the Google GenAI SDK.

> **Disclaimer:** MedSafe is an educational decision-support tool. It does not diagnose, prescribe, or advise changing any dose. Always confirm with your doctor or pharmacist. Use synthetic or public data only; do not upload real patient records.

---

## Features

1. **Multimodal Extraction:** Extracts handwritten or printed prescription details and pill strip data using Google Gemma 4.
2. **Human-in-the-Loop Verification:** Every extracted field includes source text and confidence scores; unconfirmed/low-confidence readings must be verified before proceeding downstream.
3. **Deterministic Safety Layer:** Dose scheduling (Morning / Afternoon / Night) and drug interaction checks run via deterministic, unit-tested code rather than generative guesses.
4. **Local Drug Interaction Database:** Cross-checks active medications against a local, sourced SQLite database to flag potential adverse drug-drug conflicts.
5. **Multilingual Plain-Language Explanations:** Explains medications and routines clearly across multiple languages (English, Hindi, Spanish, etc.) with spoken audio playback.
6. **Patient Q&A:** Answers patient questions strictly constrained to confirmed prescription details.
7. **Gemma 4 High-Availability Fallback:** Employs `gemma-4-31b-it` as the primary dense model, with automatic failover to `gemma-4-26b-a4b-it` if temporary upstream demand spikes occur.

---

## Architecture & Workflow

```
[Prescription / Pill Strip Image]
              │
              ▼
   [Gemma 4 Multimodal Extraction] ──▶ (Extracts medicines, strength, frequency, confidence)
              │
              ▼
    [Human Verification Step] ───────▶ (User confirms / corrects extracted items)
              │
              ▼
  ┌────────────────────────────────────────────────────────┐
  │              DETERMINISTIC SAFETY PIPELINE             │
  │  1. Normalize Sig & Frequencies (sig_map.json)         │
  │  2. Build Time-Slot Schedule (Morning/Noon/Night/Food) │
  │  3. Check Interactions against Local SQLite DB         │
  └────────────────────────────────────────────────────────┘
              │
              ▼
    [Gemma 4 Explanation & Q&A] ─────▶ (Plain speech audio + interactive patient chat)
```

---

## Tech Stack

| Layer | Tools |
|---|---|
| **AI Models** | Google Gemma 4 (`gemma-4-31b-it`, `gemma-4-26b-a4b-it`) |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, SQLite, Google GenAI SDK |
| **Frontend** | React 18, Vite, TailwindCSS / Vanilla CSS, Web Speech API |
| **Testing & Eval**| Pytest, automated field-level evaluation runner |

---

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI application endpoints
│   ├── llm.py               # Centralized Gemma 4 client with fallback logic
│   ├── schemas.py           # Pydantic data schemas
│   ├── extract.py           # Prescription and pill strip extraction
│   ├── schedule.py          # Deterministic schedule engine & frequency parsing
│   ├── interactions.py      # SQLite-based drug interaction checks
│   ├── explain.py           # Multilingual explanation generation & Q&A
│   ├── init_db.py           # Local interactions database initializer
│   ├── data/                # Local SQLite interaction DB & sig mappings
│   └── tests/               # Comprehensive unit test suite
├── frontend/                # React + Vite web client & PWA
├── samples/                 # Synthetic prescription and packaging images
├── eval/                    # Evaluation suite measuring extraction accuracy
└── AGENTS.md                # Project rules and architectural guidelines
```

---

## Getting Started

### Prerequisites

- Python 3.10+ (tested with 3.12)
- Node.js 18+ & npm
- Google Gemini API key (with Gemma 4 access) from [Google AI Studio](https://aistudio.google.com/)

### 1. Clone & Configure Environment

```bash
git clone https://github.com/NizzyStark/Medicine-Safety-Assistant.git
cd Medicine-Safety-Assistant
```

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMMA_MODEL=gemma-4-31b-it
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install fastapi uvicorn google-genai pillow pydantic python-dotenv pytest httpx

# Initialize local SQLite drug interaction database
python backend/init_db.py

# Start the FastAPI server
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` (docs at `http://localhost:8000/docs`).

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Running Tests & Evaluation

### Run Unit Tests
```bash
python -m pytest backend/tests/ -v
```

### Run Evaluation Suite (Ground Truth Accuracy)
```bash
python eval/run_eval.py
```

Evaluation summary against synthetic test samples:
- **Field Matching Accuracy:** 100% on tested synthetic prescription samples.

---

## Safety Principles

- **No Medical Advice:** The app does not diagnose conditions or advise changing dosage.
- **Source-Cited:** Every extracted instruction links back to verbatim source text on the prescription.
- **Strictly Sourced Warnings:** Drug-drug interaction flags come solely from the local database, never hallucinated by language models.
- **Safe Fallbacks:** Never guesses illegible medication names or dosages.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
