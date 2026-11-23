import json
import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "urbanpulse-classifier")
RAG_LLM_MODEL = os.getenv("RAG_LLM_MODEL", "llama3.2:3b")
LLM_USE_FEW_SHOT = os.getenv("LLM_USE_FEW_SHOT", "false").lower() == "true"
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "config.json"))


@lru_cache(maxsize=1)
def load_department_map() -> dict[str, str]:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["category_department_map"]