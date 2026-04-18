"""
GenAI service for InsureVision AI.

Uses Groq (llama-3.1-8b-instant) to produce educational insurance copy,
then builds a Pollinations.ai image URL from a derived visual prompt.
"""

from __future__ import annotations

import os
import urllib.parse

from dotenv import load_dotenv
from groq import Groq
import base64
import time

# Load environment variables from a local .env when present.
load_dotenv()

GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = (
    "You are an insurance expert. Given a topic, provide a clear, "
    "detailed explanation in 4-5 paragraphs suitable for both "
    "educational and professional use. Use simple language."
)


def _get_groq_client() -> Groq:
    """Create a Groq client using GROQ_API_KEY from the environment."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
    return Groq(api_key=api_key)


def generate_insurance_content(query: str) -> dict[str, str]:
    """
    Generate explanatory text (Groq) plus an infographic image URL (Pollinations).

    Returns:
        dict with keys ``text`` and ``image_url``.
    """
    client = _get_groq_client()
    
    #Gen Text Groq
    
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0.6,
    )

    groq_response = (completion.choices[0].message.content or "").strip()
    
    # TEMP: mocked to save Groq API usage while fixing image
    #groq_response = "This is a placeholder explanation. Groq is temporarily disabled to save API usage."
    
    

    image_prompt = (
        f"professional insurance infographic about {query}, "
        "minimalist flat design, blue and white colors, no text"
    )
    image_url = (
        "https://image.pollinations.ai/prompt/"
        f"{urllib.parse.quote(image_prompt)}"
    )

    # Download image in backend to avoid CORS issues
    image_b64 = None
    for attempt in range(3):  # retry 3 times
        try:
            import requests as req
            time.sleep(2)  # give pollinations time to generate
            img_response = req.get(image_url, timeout=30)
            if img_response.status_code == 200:
                image_b64 = "data:image/jpeg;base64," + base64.b64encode(img_response.content).decode()
                break
        except Exception:
            time.sleep(3)  # wait before retry

    return {
        "text": groq_response,
        "image_url": image_b64 if image_b64 else image_url
    }
