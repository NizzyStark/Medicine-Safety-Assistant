from PIL import Image, ImageDraw
import os

os.makedirs("samples", exist_ok=True)

img = Image.new("RGB", (700, 300), color=(220, 225, 230))
draw = ImageDraw.Draw(img)

# Strip foil markings
draw.rectangle([(10, 10), (690, 290)], outline=(180, 185, 190), width=4)
draw.text((30, 40), "GLUCOPHAGE (Metformin Hydrochloride)", fill=(10, 30, 80))
draw.text((30, 75), "Each film-coated tablet contains: Metformin HCl 500 mg", fill=(20, 20, 20))
draw.text((30, 110), "Mfg Lic No: 28/UA/2021", fill=(60, 60, 60))
draw.text((30, 140), "Batch No: B90421", fill=(30, 30, 30))
draw.text((30, 170), "Mfg Date: 03/2025    Exp Date: 02/2028", fill=(180, 20, 20))
draw.text((30, 210), "Keep in cool and dry place. Protect from light.", fill=(70, 70, 70))
draw.text((30, 260), "* Synthetic strip sample for testing", fill=(120, 50, 50))

sample_path = "samples/synthetic_strip_1.png"
img.save(sample_path)
print(f"Created {sample_path}")
