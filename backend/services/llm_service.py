"""OpenAI-compatible LLM service. Works with Groq, DeepSeek, Gemini, OpenRouter, etc."""

import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

_client = AsyncOpenAI(
    api_key=os.getenv("LLM_API_KEY", ""),
    base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
)

MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")


async def call_llm(prompt: str, system_instruction: str = "") -> str:
    """Send a prompt to the LLM and return the raw text response."""
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    response = await _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content or ""


async def call_llm_json(prompt: str, system_instruction: str = "") -> dict:
    """Send a prompt and parse the response as JSON. Retries once on parse failure."""
    for attempt in range(2):
        raw = await call_llm(prompt, system_instruction)
        # Strip markdown code fences if the LLM wraps the response
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            if attempt == 0:
                prompt = (
                    f"Your previous response was not valid JSON. "
                    f"Please fix it and respond ONLY with valid JSON, no extra text.\n\n"
                    f"Previous response:\n{raw}"
                )
    return {}
