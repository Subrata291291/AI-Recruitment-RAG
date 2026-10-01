from typing import Any

from app.rag.router import route_query
from app.rag.pipeline import run_multi_query_pipeline
from app.retrieval.hybrid import hybrid_search
from app.rag.verification import verify_candidates


def run_adaptive_rag(
    query: str,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    top_k: int | None = None,
    company_id: str | None = None,
) -> dict[str, Any]:

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if company_id is not None and not company_id.strip():
        raise ValueError("company_id cannot be empty when provided.")

    company_id = company_id.strip() if company_id else None

    required_skills = required_skills or []
    preferred_skills = preferred_skills or []

    # ---------------------------------------------------------
    # 1. Route the query
    # ---------------------------------------------------------
    routing = route_query(
        query=query,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    strategy = routing["strategy"]

    # ---------------------------------------------------------
    # 2. Run the selected retrieval strategy
    # ---------------------------------------------------------
    if strategy in {"hybrid", "hybrid_mmr"}:

        candidates = hybrid_search(
            query=query,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            top_k=top_k,
            company_id=company_id,
        )

    elif strategy == "multi_query_hybrid_mmr":

        candidates = run_multi_query_pipeline(
            query=query,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            top_k=top_k,
            company_id=company_id,
        )

    else:
        raise ValueError(
            f"Unsupported RAG strategy: {strategy}"
        )

    # ---------------------------------------------------------
    # 3. Verify final candidates
    # ---------------------------------------------------------
    verified_candidates = verify_candidates(candidates)

    # ---------------------------------------------------------
    # 4. Return complete adaptive RAG result
    # ---------------------------------------------------------
    return {
        "routing": routing,
        "company_id": company_id,
        "candidate_count": len(verified_candidates),
        "candidates": verified_candidates,
    }