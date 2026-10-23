import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
db_path = DATA_DIR / "interactions.db"

def init_db():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drug_a TEXT NOT NULL,
        drug_b TEXT NOT NULL,
        severity TEXT NOT NULL, -- mild, moderate, severe
        description TEXT NOT NULL,
        source TEXT NOT NULL
    )
    """)
    
    # Pre-populate with verified, curated interaction rules from public clinical references
    curated_data = [
        (
            "aspirin",
            "ibuprofen",
            "moderate",
            "Ibuprofen may interfere with the antiplatelet effect of low-dose aspirin and increase gastrointestinal bleeding risk.",
            "FDA / DailyMed Guidance (Aspirin & NSAIDs)"
        ),
        (
            "aspirin",
            "warfarin",
            "severe",
            "Concurrent use significantly increases the risk of major bleeding.",
            "NIH PubChem / clinical guideline on anticoagulants"
        ),
        (
            "metformin",
            "contrast_dye",
            "severe",
            "Iodinated radiocontrast agents can cause acute renal failure and lactic acidosis in patients taking metformin.",
            "FDA Black Box Warning / ACR Guidelines"
        ),
        (
            "atorvastatin",
            "clarithromycin",
            "severe",
            "Clarithromycin significantly increases atorvastatin exposure, increasing risk of myopathy or rhabdomyolysis.",
            "FDA Drug Safety Communication / Prescribing Info"
        ),
        (
            "lisinopril",
            "spironolactone",
            "moderate",
            "Concomitant use may lead to hyperkalemia (high blood potassium levels).",
            "AHA / ACC Heart Failure Guidelines"
        ),
        (
            "metformin",
            "alcohol",
            "moderate",
            "Alcohol may potentiate the effect of metformin on lactate metabolism.",
            "FDA Metformin Package Insert"
        )
    ]
    
    cursor.execute("DELETE FROM interactions")
    for drug_a, drug_b, severity, desc, source in curated_data:
        cursor.execute(
            "INSERT INTO interactions (drug_a, drug_b, severity, description, source) VALUES (?, ?, ?, ?, ?)",
            (drug_a.lower(), drug_b.lower(), severity, desc, source)
        )
        
    conn.commit()
    conn.close()
    print(f"Initialized {db_path} with {len(curated_data)} curated rules.")

if __name__ == "__main__":
    init_db()
