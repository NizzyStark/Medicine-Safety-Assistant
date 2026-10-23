import sqlite3
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from backend.schemas import MedicineItem

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "interactions.db"

class InteractionAlert(BaseModel):
    drug_a: str
    drug_b: str
    severity: str
    description: str
    source: str
    message: str = "possible conflict, check with your pharmacist or doctor."

def check_interactions(medicines: List[MedicineItem]) -> List[InteractionAlert]:
    """
    Deterministic check strictly querying local curated SQLite database.
    Does NOT hallucinate or originate interactions from the LLM.
    """
    if not DB_PATH.exists():
        return []
        
    names = [m.name.strip().lower() for m in medicines if m.name]
    if len(names) < 2:
        return []
        
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    alerts: List[InteractionAlert] = []
    seen_pairs = set()

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            med1, med2 = names[i], names[j]
            pair_key = tuple(sorted([med1, med2]))
            if pair_key in seen_pairs:
                continue
                
            cursor.execute("""
                SELECT drug_a, drug_b, severity, description, source
                FROM interactions
                WHERE (instr(?, drug_a) > 0 AND instr(?, drug_b) > 0)
                   OR (instr(?, drug_b) > 0 AND instr(?, drug_a) > 0)
            """, (med1, med2, med1, med2))
            
            rows = cursor.fetchall()
            for row in rows:
                seen_pairs.add(pair_key)
                alerts.append(
                    InteractionAlert(
                        drug_a=med1.capitalize(),
                        drug_b=med2.capitalize(),
                        severity=row[2],
                        description=row[3],
                        source=row[4],
                        message="possible conflict, check with your pharmacist or doctor."
                    )
                )

    conn.close()
    return alerts
