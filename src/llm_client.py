from __future__ import annotations

import json
from typing import Any, Dict

from .utils import get_env


def _call_openai(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    from openai import OpenAI

    api_key = get_env("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def _call_gemini(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    import google.generativeai as genai

    api_key = get_env("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(model)
    response = model_obj.generate_content(
        prompt,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        },
    )
    return response.text or ""


def run_llm(prompt: str, config: Dict[str, Any]) -> str:
    provider = config["llm"]["provider"]
    temperature = config["llm"]["temperature"]
    max_tokens = config["llm"]["max_tokens"]

    if provider == "openai":
        return _call_openai(prompt, config["llm"]["model_openai"], temperature, max_tokens)
    if provider == "gemini":
        return _call_gemini(prompt, config["llm"]["model_gemini"], temperature, max_tokens)
    raise RuntimeError("LLM provider not supported")


def parse_json_response(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
    return {"error": "invalid_json", "raw": text}
