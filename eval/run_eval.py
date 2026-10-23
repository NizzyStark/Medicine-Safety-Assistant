import os
import sys
import json
from pathlib import Path

# Ensure root is in path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.extract import extract_prescription

def run_evaluation():
    print("=" * 60)
    print("RUNNING EXTRACTION EVALUATION AGAINST GROUND TRUTH")
    print("=" * 60)
    
    samples_dir = ROOT / "samples"
    test_cases = [
        ("synthetic_rx_1.png", "synthetic_rx_1_gt.json")
    ]
    
    total_fields = 0
    correct_fields = 0

    for img_name, gt_name in test_cases:
        img_path = samples_dir / img_name
        gt_path = samples_dir / gt_name
        
        if not img_path.exists() or not gt_path.exists():
            print(f"Skipping {img_name}: missing file")
            continue
            
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)
            
        print(f"\nEvaluating: {img_name}...")
        extracted = extract_prescription(str(img_path))
        
        gt_meds = gt_data.get("medicines", [])
        ext_meds = extracted.medicines
        
        print(f"Ground truth items: {len(gt_meds)} | Extracted items: {len(ext_meds)}")
        
        # Field level accuracy check
        fields_to_check = ["name", "strength", "frequency_raw"]
        
        for i, gt_item in enumerate(gt_meds):
            # Find matching extracted item by name keyword
            match = None
            for ext in ext_meds:
                if ext.name and gt_item["name"].lower() in ext.name.lower():
                    match = ext
                    break
            
            for field in fields_to_check:
                total_fields += 1
                gt_val = (gt_item.get(field) or "").lower().strip()
                if match:
                    ext_val = (getattr(match, field) or "").lower().strip()
                    # Fuzzy match or contains
                    if gt_val in ext_val or ext_val in gt_val:
                        correct_fields += 1
                        print(f"  [PASS] {gt_item['name']} - {field}: '{ext_val}'")
                    else:
                        print(f"  [FAIL] {gt_item['name']} - {field}: got '{ext_val}', expected '{gt_val}'")
                else:
                    print(f"  [FAIL] {gt_item['name']} - Missing medicine in extraction")
                    
    accuracy = (correct_fields / total_fields * 100) if total_fields > 0 else 0
    print("\n" + "=" * 60)
    print(f"EVAL SUMMARY: Total Checked Fields: {total_fields}")
    print(f"Matched: {correct_fields} | Accuracy: {accuracy:.1f}%")
    print("=" * 60)
    return accuracy

if __name__ == "__main__":
    acc = run_evaluation()
    sys.exit(0 if acc >= 80.0 else 1)
