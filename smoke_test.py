import os
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
model_name = os.environ.get("GEMMA_MODEL", "gemini-2.5-flash")

print(f"Testing API connection with model: {model_name}...")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)

try:
    # 1. Text test
    resp = client.models.generate_content(
        model=model_name,
        contents="Say hello and confirm you are ready as a medicine safety assistant helper in one short sentence.",
    )
    print("API Text Response:", resp.text.strip())

    # 2. Image test with synthetic prescription
    img = Image.open("samples/synthetic_rx_1.png")
    vision_resp = client.models.generate_content(
        model=model_name,
        contents=[img, "List the medicine names you see in this image."],
    )
    print("\nAPI Vision Response:\n", vision_resp.text.strip())
    print("\nPhase 0 Smoke Test: ALL PASSED SUCCESSFUL!")

except Exception as e:
    print(f"Error during smoke test: {e}")
    # Also check available models if there's a model ID issue
    try:
        print("\nListing available models:")
        for m in client.models.list():
            if "gemma" in m.name.lower() or "flash" in m.name.lower():
                print(f" - {m.name}")
    except Exception as inner_e:
        print(f"Could not list models: {inner_e}")
