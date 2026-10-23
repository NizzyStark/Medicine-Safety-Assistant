from PIL import Image, ImageDraw
import os

img = Image.new("RGB", (800, 500), color=(253, 252, 248))
draw = ImageDraw.Draw(img)

# Header
draw.rectangle([(20, 20), (780, 75)], fill=(245, 235, 230), outline=(200, 150, 130))
draw.text((40, 35), "ORTHOPEDIC & ARTHRITIS CARE - Dr. K. Patel, MS", fill=(100, 40, 30))
draw.text((40, 55), "Synthetic Patient: S. Kumar (Age 72) | Date: 2026-10-23", fill=(70, 70, 70))

# Rx Symbol
draw.text((40, 100), "Rx", fill=(30, 30, 30))

# Drug 1: Aspirin
draw.text((60, 150), "1. Tab. Aspirin 75 mg", fill=(20, 20, 20))
draw.text((90, 175), "1 tab OD after lunch x 30 days", fill=(50, 50, 50))

# Drug 2: Ibuprofen (Conflict!)
draw.text((60, 230), "2. Tab. Ibuprofen 400 mg", fill=(20, 20, 20))
draw.text((90, 255), "1 tab BD after food x 5 days (for knee pain)", fill=(50, 50, 50))

# Drug 3: Pantoprazole
draw.text((60, 310), "3. Cap. Pantoprazole 40 mg", fill=(20, 20, 20))
draw.text((90, 335), "1 cap OD before breakfast (empty stomach) x 15 days", fill=(50, 50, 50))

draw.text((40, 440), "* Synthetic Sample: Clinical Interaction Test Case (Aspirin + Ibuprofen)", fill=(180, 50, 50))

img.save("samples/pain_conflict_rx.png")
img.save("frontend/public/samples/pain_conflict_rx.png")
print("Created pain_conflict_rx.png")
