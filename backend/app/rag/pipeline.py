from typing import Any

from app.config import settings
from app.retrieval.dense import dense_search
from app.retrieval.sparse import sparse_search
from app.retrieval.hybrid import (
    reciprocal_rank_fusion,
    apply_final_ranking,
)
from app.matching.candidate_aggregator import aggregate_candidates
from app.matching.candidate_scorer import score_candidates
from app.retrieval.reranker import rerank_candidates
from app.rag.multi_query import generate_multi_query_plan


def retrieve_multi_query_results(
    queries: list[str],
    company_id: str | None = None,
) -> dict[str, list[dict]]:
    """
    Run dense and sparse retrieval for every query.

    Candidate aggregation and reranking are intentionally NOT
    performed here. They happen once after all query results
    have been collected.

    company_id is passed to both dense and sparse retrieval
    so that only the current company's data is retrieved.
    """

    if not queries:
        return {
            "dense_results": [],
            "sparse_results": [],
        }

    if company_id is not None and not company_id.strip():
        raise ValueError(
            "company_id cannot be empty when provided."
        )

    all_dense_results = []
    all_sparse_results = []

    for query in queries:

        if not query.strip():
            continue

        dense_results = dense_search(
            query,
            top_k=settings.DENSE_TOP_K,
            company_id=company_id,
        )

        sparse_results = sparse_search(
            query,
            top_k=settings.SPARSE_TOP_K,
            company_id=company_id,
        )

        all_dense_results.extend(
            dense_results
        )

        all_sparse_results.extend(
            sparse_results
        )

    return {
        "dense_results": all_dense_results,
        "sparse_results": all_sparse_results,
    }


def merge_multi_query_results(
    dense_results: list[dict],
    sparse_results: list[dict],
) -> list[dict]:
    """
    Merge retrieval results from multiple query perspectives
    using Reciprocal Rank Fusion.
    """

    return reciprocal_rank_fusion(
        dense_results=dense_results,
        sparse_results=sparse_results,
    )


def run_multi_query_pipeline(
    query: str,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    top_k: int | None = None,
    company_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Execute the complete multi-query recruitment retrieval pipeline.

    Flow:

        Query
          ↓
        MultiQuery generation
          ↓
        Company-aware Dense + Sparse retrieval
          ↓
        RRF
          ↓
        Candidate aggregation
          ↓
        Requirement scoring
          ↓
        Reranking
          ↓
        Final ranking
    """

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if company_id is not None and not company_id.strip():
        raise ValueError(
            "company_id cannot be empty when provided."
        )

    final_top_k = (
        top_k
        or settings.FINAL_TOP_K
    )

    # ---------------------------------------------------------
    # 1. Generate retrieval queries
    # ---------------------------------------------------------

    query_plan = generate_multi_query_plan(
        query=query,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    queries = query_plan["queries"]

    # ---------------------------------------------------------
    # 2. Retrieve using every query
    # ---------------------------------------------------------

    retrieval_results = retrieve_multi_query_results(
        queries=queries,
        company_id=company_id,
    )

    dense_results = retrieval_results[
        "dense_results"
    ]

    sparse_results = retrieval_results[
        "sparse_results"
    ]

    # ---------------------------------------------------------
    # 3. Merge all retrieval results with RRF
    # ---------------------------------------------------------

    fused_results = merge_multi_query_results(
        dense_results=dense_results,
        sparse_results=sparse_results,
    )

    # ---------------------------------------------------------
    # 4. Aggregate chunks into candidates
    # ---------------------------------------------------------

    candidates = aggregate_candidates(
        retrieval_results=fused_results,
        query=query,
    )

    # ---------------------------------------------------------
    # 5. Apply JD requirement matching
    # ---------------------------------------------------------

    if required_skills or preferred_skills:

        candidates = score_candidates(
            candidates=candidates,
            required_skills=required_skills or [],
            preferred_skills=preferred_skills or [],
        )

    # ---------------------------------------------------------
    # 6. Rerank candidates
    # ---------------------------------------------------------

    candidates = rerank_candidates(
        query=query,
        candidates=candidates,
        top_k=len(candidates),
    )

    # ---------------------------------------------------------
    # 7. Final ranking
    # ---------------------------------------------------------

    candidates = apply_final_ranking(
        candidates
    )

    return candidates[:final_top_k]


def build_pipeline_result(
    query: str,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    top_k: int | None = None,
    company_id: str | None = None,
) -> dict[str, Any]:
    """
    Return both the retrieval plan and candidate results.

    Useful for API responses and debugging because the caller
    can see which retrieval queries were generated.

    company_id is propagated into the complete retrieval
    pipeline to maintain tenant isolation.
    """

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if company_id is not None and not company_id.strip():
        raise ValueError(
            "company_id cannot be empty when provided."
        )

    query_plan = generate_multi_query_plan(
        query=query,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    candidates = run_multi_query_pipeline(
        query=query,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        top_k=top_k,
        company_id=company_id,
    )

    return {
        "query_plan": query_plan,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }