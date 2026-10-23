import logging
import os
import time
from typing import Any, List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

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
    Central function for all Gemma model calls.
    All model calls in the project must go through backend/llm.py.
    Uses Gemma 4 models only, with an automatic Gemma fallback if the primary model is unavailable.
    """
    client = get_client()
    primary_model = model or os.environ.get("GEMMA_MODEL", "gemma-4-31b-it")
    fallback_model = "gemma-4-26b-a4b-it"

    # Gemma models only, preserving order without duplicate
    candidate_models = [primary_model]
    if fallback_model not in candidate_models:
        candidate_models.append(fallback_model)

    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
    if json_mode:
        config.response_mime_type = "application/json"

    last_error = None
    for idx, target_model in enumerate(candidate_models):
        if idx > 0:
            msg = f"[NOTICE] Primary model '{candidate_models[0]}' unavailable. Switching to fallback Gemma model '{target_model}'."
            print(msg)
            logger.warning(msg)

        for attempt in range(2):
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
                # Backoff slightly on transient 500/503/429
                time.sleep(1.0 * (attempt + 1))

    raise ValueError(
        f"All Gemma models ({', '.join(candidate_models)}) are currently unavailable. "
        f"Please try again later. Last error: {last_error}"
    )
