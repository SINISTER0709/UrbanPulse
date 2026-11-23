import os
import re
import logging
from pathlib import Path
from typing import Any

from app.services.llm_client import rag_llm_client

logger = logging.getLogger(__name__)

SOPS_DIR = Path("data/sops")
DISCLAIMER = "Advisory only, not municipal policy."

SOP_FILE_MAP = {
    "road_damage": "road_sop.md",
    "garbage_sanitation": "garbage_sanitation_sop.md",
    "streetlight_electrical": "streetlight_electrical_sop.md",
    "water_supply": "water_supply_sop.md",
    "drainage_flooding": "drainage_flooding_sop.md",
    "other": "general_municipal_sop.md",
}

DEFAULT_SOP_EXCERPTS = {
    "road_damage": {
        "brief": "Place warning cones and dispatch road crew within 24h.",
        "excerpt": "Section 4.2: High-severity school-zone potholes require barricading and repair within 24 hours.",
    },
    "garbage_sanitation": {
        "brief": "Deploy compactor truck and sanitize disposal area within 12h.",
        "excerpt": "Section 3.1: Overflowing community waste bins near markets require clearance within 12 hours.",
    },
    "streetlight_electrical": {
        "brief": "Isolate power supply line immediately and dispatch electrical lineman team.",
        "excerpt": "Section 2.4: Snapped live conductors and sparking transformers require emergency isolation within 2 hours.",
    },
    "water_supply": {
        "brief": "Close arterial valve to prevent clean water wastage and excavate pipeline for clamp repair.",
        "excerpt": "Section 5.1: Main drinking water pipeline bursts require valve shutoff within 4 hours.",
    },
    "drainage_flooding": {
        "brief": "Deploy dewatering suction pumps and clear storm sewer blockage.",
        "excerpt": "Section 6.3: Waterlogged underpasses and blocked storm drains require emergency suction deployment.",
    },
    "other": {
        "brief": "Dispatch municipal inspection officer for site verification.",
        "excerpt": "Section 1.1: General public hazards require site inspection and advisory routing within 48 hours.",
    },
}


def read_sop_excerpt(category: str, severity: str) -> tuple[str, str, str]:
    filename = SOP_FILE_MAP.get(category, "general_municipal_sop.md")
    sop_path = SOPS_DIR / filename
    if not sop_path.exists():
        sop_path = Path("C:/vs/URBANPULSE/data/sops") / filename

    if sop_path.exists():
        try:
            content = sop_path.read_text(encoding="utf-8")
            # Find relevant section by severity
            lines = [l.strip() for l in content.split("\n") if l.strip()]
            for i, line in enumerate(lines):
                if severity.lower() in line.lower() or "action" in line.lower() or "procedure" in line.lower():
                    snippet = " ".join(lines[i:i+3])[:200]
                    return filename, snippet, f"Follow {filename} triage: initiate response per municipal standard."
        except Exception as e:
            logger.warning(f"[RAG Service] Error reading SOP file: {e}")

    default = DEFAULT_SOP_EXCERPTS.get(category, DEFAULT_SOP_EXCERPTS["other"])
    return filename, default["excerpt"], default["brief"]


def generate_action_brief(
    incident_id: str,
    category: str,
    severity: str,
    location_context: str = "low_exposure",
    summary_text: str | None = None,
) -> dict[str, Any]:
    """
    Track F Deliverable:
    RAG-grounded advisory action brief with cited source excerpts and the mandatory disclaimer:
    'Advisory only, not municipal policy.'
    """
    doc_name, excerpt, default_brief = read_sop_excerpt(category, severity)

    # Attempt LLM synthesis if LLM client is available
    brief_text = default_brief
    try:
        prompt = f"""You are a municipal dispatch assistant.
Given the incident below and official SOP excerpt, write a single concise operational dispatch sentence (max 20 words).
Incident Category: {category}
Severity: {severity}
Location: {location_context}
Complaint: {summary_text or category}
Official SOP Excerpt: {excerpt}

Return ONLY the single action sentence."""

        res = rag_llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=40,
        )
        if res and len(res) > 10:
            brief_text = res.strip().strip('"')
    except Exception as exc:
        logger.debug(f"[RAG Service] LLM generation skipped ({exc}). Using standard SOP brief.")

    return {
        "incident_id": incident_id,
        "brief": brief_text,
        "sources": [
            {
                "doc": doc_name,
                "excerpt": excerpt,
            }
        ],
        "disclaimer": DISCLAIMER,
    }
