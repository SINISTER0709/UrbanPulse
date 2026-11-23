import os
import re
from pathlib import Path
from typing import Any

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from app.dedup_service import get_embedding_model

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
RAG_LLM_MODEL = os.getenv("RAG_LLM_MODEL", "llama3.2:3b")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db"))
SOPS_DIR = Path(os.getenv("SOPS_DIR", "data/sops"))

DISCLAIMER = "Advisory only, not municipal policy."

FILE_TO_CATEGORY = {
    "road_sop.md": "road_damage",
    "garbage_sanitation_sop.md": "garbage_sanitation",
    "streetlight_electrical_sop.md": "streetlight_electrical",
    "water_supply_sop.md": "water_supply",
    "drainage_flooding_sop.md": "drainage_flooding",
    "general_municipal_sop.md": "other",
}

_collection = None


def _chunk_markdown(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8").strip()
    sections = re.split(r"\n(?=##\s+)", text)
    chunks = []
    for idx, sec in enumerate(sections):
        cleaned = sec.strip()
        if len(cleaned) < 40 or cleaned.startswith("# ") and "## " not in cleaned:
            continue
        chunks.append({
            "id": f"{path.stem}_sec_{idx}",
            "doc": path.name,
            "category": FILE_TO_CATEGORY.get(path.name, "other"),
            "text": cleaned,
        })
    return chunks


def get_sop_collection(force_reindex: bool = False):
    global _collection
    if _collection is not None and not force_reindex:
        return _collection

    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    collection = client.get_or_create_collection(
        name="municipal_sops",
        metadata={"hnsw:space": "cosine"},
    )

    if collection.count() == 0 or force_reindex:
        sop_files = sorted(SOPS_DIR.glob("*.md"))
        all_chunks: list[dict[str, str]] = []
        for fpath in sop_files:
            all_chunks.extend(_chunk_markdown(fpath))

        if all_chunks:
            emb_model = get_embedding_model()
            vectors = emb_model.encode(
                [c["text"] for c in all_chunks], normalize_embeddings=True
            ).tolist()
            collection.upsert(
                ids=[c["id"] for c in all_chunks],
                documents=[c["text"] for c in all_chunks],
                metadatas=[{"doc": c["doc"], "category": c["category"]} for c in all_chunks],
                embeddings=vectors,
            )

    _collection = collection
    return _collection


def generate_action_brief(
    incident_id: str,
    category: str,
    severity: str,
    location_context: str = "low_exposure",
    summary_text: str | None = None,
    top_k: int = 2,
) -> dict[str, Any]:
    collection = get_sop_collection()
    if collection.count() == 0:
        return {
            "incident_id": incident_id,
            "brief": "No reference SOP documents indexed yet. Review manually per ward procedure.",
            "sources": [],
            "disclaimer": DISCLAIMER,
            "llm_used": False,
        }

    query_text = (
        f"Category: {category}. Severity: {severity}. "
        f"Location: {location_context}. "
        f"Incident: {summary_text or f'{severity} {category} near {location_context}'}"
    )
    emb_model = get_embedding_model()
    q_vec = emb_model.encode([query_text], normalize_embeddings=True).tolist()

    # Prefer SOP chunks matching the incident category; fall back to full corpus if none
    results = collection.query(
        query_embeddings=q_vec,
        n_results=top_k,
        where={"category": category},
    )
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        results = collection.query(query_embeddings=q_vec, n_results=top_k)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

    sources = [
        {
            "doc": meta["doc"],
            "excerpt": doc.replace("\n", " ")[:240].strip(),
        }
        for doc, meta in zip(docs, metas)
    ]

    context_block = "\n\n".join(
        f"[{meta['doc']}]\n{doc}" for doc, meta in zip(docs, metas)
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a municipal operations assistant. Using ONLY the SOP section matching "
                "the incident's exact severity level, write 2-3 plain sentences (no markdown headers, "
                "no bullet lists, do not repeat incident metadata) stating immediate safety steps, "
                "responsible crew, and target SLA. Do not mix Critical SLAs into High/Medium/Low incidents."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Incident ID: {incident_id} | Category: {category} | "
                f"Severity: {severity} | Location: {location_context}\n"
                f"Summary: {summary_text or 'N/A'}\n\n"
                f"Reference SOP Excerpts:\n{context_block}\n\n"
                "Write the 2-3 sentence advisory action brief:"
            ),
        },
    ]

    llm_used = True
    try:
        llm = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY, timeout=LLM_TIMEOUT_SECONDS)
        resp = llm.chat.completions.create(
            model=RAG_LLM_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=260,
        )
        brief = (resp.choices[0].message.content or "").strip()
    except Exception:
        # Fault-tolerant fallback: return grounded SOP excerpt directly if Ollama is unavailable
        llm_used = False
        brief = f"Follow SOP guidance ({sources[0]['doc']}): {sources[0]['excerpt']}"

    return {
        "incident_id": incident_id,
        "brief": brief,
        "sources": sources,
        "disclaimer": DISCLAIMER,
        "llm_used": llm_used,
    }