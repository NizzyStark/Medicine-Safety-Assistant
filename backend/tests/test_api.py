from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_process_confirmed_pipeline():
    payload = {
        "confirmed_medicines": [
            {
                "name": "Metformin",
                "strength": "500mg",
                "frequency_raw": "BD",
                "duration": "30 days",
                "instructions": "after meals",
                "source_text": "Metformin 500 BD after meals",
                "confidence": 0.95
            },
            {
                "name": "Atorvastatin",
                "strength": "20mg",
                "frequency_raw": "HS",
                "duration": "30 days",
                "instructions": "at bedtime",
                "source_text": "Atorvastatin 20 HS",
                "confidence": 0.95
            }
        ],
        "language": "en"
    }
    
    res = client.post("/api/process-confirmed", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "schedule" in data
    assert len(data["schedule"]["morning"]) == 1
    assert len(data["schedule"]["night"]) == 2
    assert "spoken_explanation" in data
    assert "Please confirm with your doctor or pharmacist" in data["spoken_explanation"] or "doctor" in data["spoken_explanation"]
