from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs("samples", exist_ok=True)

# Generate a synthetic prescription image
img = Image.new("RGB", (800, 600), color=(250, 250, 248))
draw = ImageDraw.Draw(img)

# Header
draw.rectangle([(20, 20), (780, 80)], fill=(230, 240, 250), outline=(100, 150, 200))
draw.text((40, 35), "CITY HEALTH CLINIC - Dr. A. Sharma, MD", fill=(20, 50, 90))
draw.text((40, 55), "Synthetic Patient: John Doe | Age: 68 | Date: 2026-10-23", fill=(80, 80, 80))

# Rx Symbol
draw.text((40, 110), "Rx", fill=(30, 30, 30))

# Medicine 1: Metformin 500mg
draw.text((60, 160), "1. Tab. Metformin 500mg", fill=(20, 20, 20))
draw.text((90, 190), "1 tab BD after meals x 30 days", fill=(40, 40, 40))

# Medicine 2: Atorvastatin 20mg
draw.text((60, 240), "2. Tab. Atorvastatin 20mg", fill=(20, 20, 20))
draw.text((90, 270), "1 tab HS (at bedtime) x 30 days", fill=(40, 40, 40))

# Medicine 3: Aspirin 75mg
draw.text((60, 320), "3. Tab. Aspirin 75mg", fill=(20, 20, 20))
draw.text((90, 350), "1 tab OD after lunch x 30 days", fill=(40, 40, 40))

# Doctor signature block
draw.line([(550, 520), (750, 520)], fill=(100, 100, 100), width=1)
draw.text((560, 530), "Dr. A. Sharma (Reg #98765)", fill=(80, 80, 80))
draw.text((40, 560), "* Synthetic test data only. Not a real prescription.", fill=(150, 50, 50))

sample_path = "samples/synthetic_rx_1.png"
img.save(sample_path)
print(f"Created {sample_path}")
