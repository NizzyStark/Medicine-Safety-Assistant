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
