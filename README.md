# MedSafe: Medicine Safety Assistant

A private-by-design assistant that helps elderly patients and caregivers understand handwritten prescriptions and pill packaging. Take a photo, confirm what was read, get a simple daily schedule explained by voice in your own language, and see possible conflicts to check with a doctor or pharmacist.

Built with **Gemma 4** through the **Gemini API**.

> **Disclaimer:** MedSafe is an educational decision-support tool. It does not diagnose, prescribe, or advise changing any dose. Always confirm with your doctor or pharmacist. Use synthetic or public data only; do not upload real patient records.

---

## The problem

Many people, especially elderly patients and their caregivers, manage several medicines from handwritten prescriptions and unlabeled strips, often in languages and jargon they do not fully understand. Mistakes in dose, timing, and combinations are common and can be dangerous. Basic OCR struggles with handwriting and mixed-language text, and most apps assume typed input in English.

## What MedSafe does

1. **Reads** a prescription or pill strip from a photo (Gemma 4 multimodal input).
2. **Shows its work:** the photo appears beside the extracted text, and uncertain fields must be confirmed by a human.
3. **Builds a daily schedule** (Morning / Afternoon / Night) using deterministic code, not model guesses.
4. **Explains in the patient's language** with short, plain sentences and spoken playback.
5. **Flags possible conflicts** from a small, sourced local database, always worded as "check with your pharmacist or doctor."
6. **Cross-checks** pill strips against the prescription to catch mismatches in strength or name.

## What makes it different

- **Verify before trust:** low-confidence fields are highlighted and must be confirmed before anything downstream runs.
- **Source-cited output:** every instruction shows the exact text it came from.
- **Deterministic safety layer:** scheduling and interaction checks run in code against a sourced database. The model explains results but never originates a warning.
- **Honest uncertainty:** unclear text produces "ask your pharmacist," not a guess.
- **Voice-first and caregiver-friendly:** large buttons, high contrast, spoken explanations.

---

## Architecture

```
Photo -> Preprocess -> Gemma 4: extract (JSON + confidence + source text)
      -> Verify screen (human confirms)
      -> Code: normalize frequency -> schedule -> interaction check (local DB)
      -> Gemma 4: explain in patient's language -> voice playback / Q&A
```

All model calls go through `backend/llm.py`, so the model backend can be swapped later (for example, a local model for fully offline use) without changing the rest of the app.

## Tech stack

| Layer | Tools |
|---|---|
| Model | Gemma 4 via Gemini API (`google-genai`) |
| Backend | Python, FastAPI, Pydantic, SQLite |
| Image prep | Pillow, OpenCV |
| Frontend | React + Vite PWA (camera capture, voice buttons) |
| Voice | Browser Web Speech API (speech recognition and synthesis) |

## Project structure

```
medsafe/
  AGENTS.md              # project rules for AI coding agents
  backend/
    main.py              # FastAPI app
    llm.py               # all Gemma calls
    schemas.py           # data models
    preprocess.py        # image cleanup
    extract.py           # prescription and strip extraction
    schedule.py          # frequency normalization, daily schedule
    interactions.py      # local interaction lookup
    explain.py           # plain-language explanation and Q&A
    data/                # sig_map.json, interactions.db
    tests/
  frontend/              # React + Vite app
  samples/               # synthetic prescriptions and strips
  eval/run_eval.py       # field-level accuracy on samples
```

## Getting started

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### Setup

```bash
git clone https://github.com/<username>/<repo>.git
cd <repo>

# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env     # then add your key
```

`.env`:
```
GEMINI_API_KEY=your_key_here
GEMMA_MODEL=gemma-4-31b-it
```

> Check Google AI Studio for the current Gemma 4 model IDs and set `GEMMA_MODEL` accordingly. **Never commit `.env`.**

### Run

```bash
# Backend
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open the local URL shown by Vite. For camera testing, use a real phone on the same network.

### Test and evaluate

```bash
pytest backend/tests
python eval/run_eval.py     # field-level accuracy on samples/
```

---

## Safety design

- No diagnosis; no advice to change, skip, or stop a dose.
- Every result screen reminds the user to confirm with a doctor or pharmacist.
- Confidence below the threshold means the user is asked, never guessed for.
- Interaction warnings come only from the local database and show their source.
- Synthetic or public data only. Images and extracted text are not logged to third parties by this app's code.

> Note: while using the Gemini API, images and text are sent to a hosted model. Fully offline operation requires a local model backend, which is planned (see Roadmap).

## Limitations

- Handwriting recognition is imperfect; results depend on image quality and the writer.
- The interaction database is small and illustrative, not a clinical resource.
- Language and voice quality depend on the model and the browser's speech support.
- Not a medical device and not a substitute for professional advice.

## Roadmap

- [ ] Local model backend (Ollama or on-device Gemma 4) for true offline use
- [ ] Larger, properly sourced interaction database
- [ ] More languages and regional handwriting samples
- [ ] Printable or exportable caregiver summary

## Evaluation results

_Add your numbers here after running `eval/run_eval.py`:_

| Sample type | Fields | Correct | Flagged for review |
|---|---|---|---|
| Typed prescriptions | | | |
| Handwritten prescriptions | | | |
| Mixed-language | | | |
| Pill strips | | | |

## License

Choose a license (for example MIT) and add a `LICENSE` file.

## Acknowledgments

Built for the "Best Use of Gemma 4" track. Thanks to Google for the Gemma 4 open model and Gemini API.
