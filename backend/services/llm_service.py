"""Wrapper for Google Gemini API calls."""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


async def call_llm(prompt: str, system_instruction: str = "") -> str:
    """Call Gemini and return the text response.

    TODO: implement actual Gemini integration.
    """
    raise NotImplementedError("LLM service not yet implemented")
