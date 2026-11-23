import json
import re
from pydantic import ValidationError
from app.config import load_department_map
from app.llm_client import LLMClient, shared_llm_client
from app.prompts import build_classification_messages
from app.schemas import AnalyzeCategoryResponse, CategoryEnum, LLMCategoryOutput


def _extract_json_object(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def classify_complaint(
    text: str,
    client: LLMClient = shared_llm_client,
    max_retries: int = 1,
) -> AnalyzeCategoryResponse:
    dept_map = load_department_map()
    messages = build_classification_messages(text)

    for _ in range(max_retries + 1):
        try:
            raw = client.chat(
                messages=messages,
                temperature=0.0,
                max_tokens=32,
                json_mode=True,
            )
            payload = _extract_json_object(raw)
            parsed = LLMCategoryOutput.model_validate(payload)
            return AnalyzeCategoryResponse(
                category=parsed.category,
                department=dept_map[parsed.category.value],
                fallback_used=False,
            )
        except (json.JSONDecodeError, ValidationError, KeyError, Exception):
            continue

    return AnalyzeCategoryResponse(
        category=CategoryEnum.other,
        department=dept_map[CategoryEnum.other.value],
        fallback_used=True,
    )