import os
import json
import re
import logging
from typing import Any
from openai import OpenAI

from app.core.shared_config import LOCKED_CATEGORIES, CATEGORY_DEPARTMENT_MAPPINGS

logger = logging.getLogger(__name__)

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
RAG_LLM_MODEL = os.getenv("RAG_LLM_MODEL", "llama3.2:3b")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "15"))

SYSTEM_PROMPT = """You are a civic complaint triage classifier for a municipal corporation.
Classify each citizen complaint into EXACTLY ONE of the following 6 category keys:
- road_damage: Potholes, broken/cracked roads, sinkholes, damaged footpaths, speed breakers, bridge/flyover surface damage.
- garbage_sanitation: Uncollected garbage, overflowing bins, illegal dumping, burning trash, dead animals, filthy public toilets, biomedical/hazardous waste.
- streetlight_electrical: Dead/flickering streetlights, leaning/fallen electric poles, sparking transformers, open feeder boxes, snapped/live power wires.
- water_supply: Clean drinking-water pipe leaks/bursts, low/no water pressure, contaminated/muddy tap water, broken standposts/handpumps.
- drainage_flooding: Blocked/overflowing storm drains or nallahs, sewage backup, open/missing manhole covers, waterlogging/flooded streets or underpasses.
- other: Noise, stray/rabid animals, illegal parking/encroachment, fallen dry trees (no power lines), unstable hoardings/walls, construction hazards, park maintenance.

Rules:
- If multiple issues appear, pick the PRIMARY physical hazard requiring immediate action.
- Output ONLY valid JSON: {"category": "<one_of_the_6_keys>"} with no extra text."""

FEW_SHOT_EXAMPLES: list[dict[str, str]] = [
    {"role": "user", "content": "Huge pothole outside St. Mary School gate causing bikes to slip."},
    {"role": "assistant", "content": '{"category": "road_damage"}'},
    {"role": "user", "content": "garbge not picked up for 5 days near sector 14 market, bad smel"},
    {"role": "assistant", "content": '{"category": "garbage_sanitation"}'},
    {"role": "user", "content": "Three street lamps dead on main park road, pitch dark after 7pm."},
    {"role": "assistant", "content": '{"category": "streetlight_electrical"}'},
    {"role": "user", "content": "Main drinking water pipeline burst near block C, clean water wasting since morning."},
    {"role": "assistant", "content": '{"category": "water_supply"}'},
    {"role": "user", "content": "Nala is choked with plastic and dirty sewage water is flooding the whole lane."},
    {"role": "assistant", "content": '{"category": "drainage_flooding"}'},
    {"role": "user", "content": "Loudspeakers playing music past midnight near the community hall."},
    {"role": "assistant", "content": '{"category": "other"}'},
]

# Robust keyword fallback map for when LLM inference is offline
KEYWORD_HEURISTICS: list[tuple[str, list[str]]] = [
    ("road_damage", ["pothole", "cracked road", "broken road", "asphalt", "sinkhole", "footpath", "speed breaker", "pavement"]),
    ("garbage_sanitation", ["garbage", "trash", "rubbish", "waste", "dustbin", "litter", "dump", "filth", "dead animal", "smell"]),
    ("streetlight_electrical", ["streetlight", "street light", "electric pole", "live wire", "sparking", "transformer", "blackout", "lamp post"]),
    ("water_supply", ["water supply", "pipeline burst", "clean water", "drinking water", "tap water", "water leakage", "no water"]),
    ("drainage_flooding", ["drain", "sewage", "gutter", "waterlogging", "flooding", "manhole", "overflowing drain", "choked nala", "flooded"]),
]


class LLMClient:
    """Reusable OpenAI-SDK wrapper for local Ollama, Groq, or OpenRouter (Track A)."""

    def __init__(
        self,
        base_url: str = LLM_BASE_URL,
        api_key: str = LLM_API_KEY,
        model: str = LLM_MODEL,
        timeout: float = LLM_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url
        self.default_model = model
        try:
            self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
            self.client = None

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 128,
        json_mode: bool = False,
    ) -> str:
        if self.client is None:
            raise RuntimeError("LLM client not available")
        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return (response.choices[0].message.content or "").strip()


shared_llm_client = LLMClient(model=LLM_MODEL)
rag_llm_client = LLMClient(model=RAG_LLM_MODEL)


def _heuristic_classify(text: str) -> str:
    low = text.lower()
    for cat, kws in KEYWORD_HEURISTICS:
        if any(kw in low for kw in kws):
            return cat
    return "other"


def classify_complaint_text(
    text: str,
    client: LLMClient = shared_llm_client,
    use_few_shot: bool = True,
) -> dict[str, Any]:
    """
    Track A: Classify complaint text into one of 6 locked categories.
    Returns: {"category": "road_damage", "department": "Public Works", "fallback_used": False}
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if use_few_shot:
        messages.extend(FEW_SHOT_EXAMPLES)
    messages.append({"role": "user", "content": text.strip()})

    try:
        raw = client.chat(messages=messages, temperature=0.0, max_tokens=32, json_mode=True)
        # Parse JSON
        cleaned = raw.strip()
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
            if not match:
                raise
            payload = json.loads(match.group(0))

        cat = payload.get("category", "").strip().lower()
        if cat in LOCKED_CATEGORIES:
            return {
                "category": cat,
                "department": CATEGORY_DEPARTMENT_MAPPINGS.get(cat, "General Administration"),
                "fallback_used": False,
            }
    except Exception as exc:
        logger.debug(f"[LLM Classifier] LLM inference unavailable or timed out ({exc}). Using heuristic fallback.")

    # Graceful heuristic fallback
    fallback_cat = _heuristic_classify(text)
    return {
        "category": fallback_cat,
        "department": CATEGORY_DEPARTMENT_MAPPINGS.get(fallback_cat, "General Administration"),
        "fallback_used": True,
    }
