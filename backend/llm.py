import os
import time
from typing import Any, List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_client: Optional[genai.Client] = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        _client = genai.Client(api_key=api_key)
    return _client

def generate(
    contents: List[Any],
    system_instruction: Optional[str] = None,
    json_mode: bool = False,
    model: Optional[str] = None,
) -> str:
    """
    Central function for all Gemini/Gemma calls.
    All model calls in the project must go through backend/llm.py.
    Includes fallback retry and backup model support on transient 503 high demand spikes.
    """
    client = get_client()
    candidate_models = [
        model or os.environ.get("GEMMA_MODEL", "gemini-3.8-flash"),
        "gemini-3.1-flash-lite",
        "gemini-flash-latest"
    ]
    # Remove duplicates preserving order
    candidate_models = list(dict.fromkeys(candidate_models))

    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
    if json_mode:
        config.response_mime_type = "application/json"

    last_error = None
    for target_model in candidate_models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=target_model,
                    contents=contents,
                    config=config,
                )
                if response.text:
                    return response.text.strip()
            except Exception as e:
                last_error = e
                # Backoff slightly on transient 503/429
                time.sleep(1.0 * (attempt + 1))

    raise ValueError(f"All model calls failed. Last error: {last_error}")

