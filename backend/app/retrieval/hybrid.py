from app.config import settings

from app.retrieval.dense import dense_search
from app.retrieval.sparse import sparse_search
from app.matching.candidate_aggregator import aggregate_candidates
from app.matching.candidate_scorer import score_candidates
from app.retrieval.reranker import rerank_candidates


def reciprocal_rank_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """
    Combine dense and sparse retrieval results using
    Reciprocal Rank Fusion (RRF).
    """

    fused = {}

    # ---------------------------------------------------------
    # Dense results
    # ---------------------------------------------------------

    for rank, result in enumerate(
        dense_results,
        start=1,
    ):
        result_id = result["id"]

        if result_id not in fused:
            fused[result_id] = {
                "id": result_id,
                "metadata": result["metadata"],
                "dense_score": result["score"],
                "sparse_score": 0.0,
                "rrf_score": 0.0,
            }

        fused[result_id]["rrf_score"] += (
            1 / (k + rank)
        )

    # ---------------------------------------------------------
    # Sparse results
    # ---------------------------------------------------------

    for rank, result in enumerate(
        sparse_results,
        start=1,
    ):
        result_id = result["id"]

        if result_id not in fused:
            fused[result_id] = {
                "id": result_id,
                "metadata": result["metadata"],
                "dense_score": 0.0,
                "sparse_score": result["score"],
                "rrf_score": 0.0,
            }
        else:
            fused[result_id]["sparse_score"] = (
                result["score"]
            )

        fused[result_id]["rrf_score"] += (
            1 / (k + rank)
        )

    results = sorted(
        fused.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )

    return results


def calculate_final_rank_score(
    candidate: dict,
) -> float:
    """
    Calculate the final candidate ranking score.

    Required skills are the strongest signal.
    Preferred skills, reranking relevance, and retrieval
    relevance provide supporting signals.
    """

    matching = candidate.get(
        "matching",
        {},
    )

    required_score = float(
        matching.get(
            "required_score",
            0.0,
        )
    )

    preferred_score = float(
        matching.get(
            "preferred_score",
            0.0,
        )
    )

    rerank_score = float(
        candidate.get(
            "rerank_score",
            0.0,
        )
    )

    rrf_score = float(
        candidate.get(
            "best_rrf_score",
            0.0,
        )
    )

    # Normalize RRF into an approximate 0-1 range.
    normalized_rrf = min(
        rrf_score / 0.05,
        1.0,
    )

    # ---------------------------------------------------------
    # Final ranking weights
    # ---------------------------------------------------------
    #
    # Required skills : 60%
    # Preferred skills: 15%
    # Reranker        : 20%
    # RRF             : 5%
    # ---------------------------------------------------------

    final_score = (
        required_score * 0.60
        + preferred_score * 0.15
        + rerank_score * 0.20
        + normalized_rrf * 0.05
    )

    return round(
        max(0.0, min(1.0, final_score)),
        4,
    )


def apply_final_ranking(
    candidates: list[dict],
) -> list[dict]:
    """
    Apply final candidate ranking.

    Candidates with complete required-skill evidence are
    kept ahead of candidates with incomplete required-skill
    evidence.

    This is based only on retrieved resume evidence.

    A missing skill in retrieved evidence does not prove
    that the candidate actually lacks that skill.
    """

    ranked_candidates = []

    for candidate in candidates:

        final_score = calculate_final_rank_score(
            candidate
        )

        matching = candidate.get(
            "matching",
            {},
        )

        required_score = float(
            matching.get(
                "required_score",
                0.0,
            )
        )

        # -----------------------------------------------------
        # Required-skill evidence bucket
        # -----------------------------------------------------

        required_complete = (
            1
            if required_score >= 1.0
            else 0
        )

        ranked_candidates.append(
            {
                **candidate,
                "final_score": final_score,
                "required_complete": required_complete,
            }
        )

    # ---------------------------------------------------------
    # Final ordering
    # ---------------------------------------------------------

    ranked_candidates.sort(
        key=lambda candidate: (
            candidate.get("required_complete", 0),
            candidate.get("matching", {}).get("required_score", 0.0),
            candidate.get("final_score", 0.0),
            candidate.get("matching", {}).get("preferred_score", 0.0),
            candidate.get("best_rrf_score", 0.0),
        ),
        reverse=True,
    )

    return ranked_candidates


def hybrid_search(
    query: str,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    top_k: int | None = None,
    company_id: str | None = None,
) -> list[dict]:
    """
    Perform company-aware dense + sparse hybrid retrieval,
    candidate aggregation, requirement scoring, reranking,
    and final candidate ranking.
    """

    if company_id is not None and not company_id.strip():
        raise ValueError(
            "company_id cannot be empty when provided."
        )

    final_top_k = (
        top_k
        or settings.FINAL_TOP_K
    )

    # ---------------------------------------------------------
    # 1. Dense retrieval
    # ---------------------------------------------------------

    dense_results = dense_search(
        query,
        top_k=settings.DENSE_TOP_K,
        company_id=company_id,
    )

    # ---------------------------------------------------------
    # 2. Sparse retrieval
    # ---------------------------------------------------------

    sparse_results = sparse_search(
        query,
        top_k=settings.SPARSE_TOP_K,
        company_id=company_id,
    )

    # ---------------------------------------------------------
    # 3. Reciprocal Rank Fusion
    # ---------------------------------------------------------

    fused_results = reciprocal_rank_fusion(
        dense_results,
        sparse_results,
    )

    # ---------------------------------------------------------
    # 4. Candidate-level aggregation
    # ---------------------------------------------------------

    candidate_results = aggregate_candidates(
        fused_results,
        query,
    )

    # ---------------------------------------------------------
    # 5. Requirement scoring
    # ---------------------------------------------------------

    if required_skills or preferred_skills:
        candidate_results = score_candidates(
            candidates=candidate_results,
            required_skills=required_skills or [],
            preferred_skills=preferred_skills or [],
        )

    # ---------------------------------------------------------
    # 6. LLM / fallback reranking
    # ---------------------------------------------------------

    reranked_results = rerank_candidates(
        query=query,
        candidates=candidate_results,
        top_k=len(candidate_results),
    )

    # ---------------------------------------------------------
    # 7. Final ranking
    # ---------------------------------------------------------

    final_results = apply_final_ranking(
        reranked_results
    )

    return final_results[:final_top_k]