from collections import defaultdict

from app.retrieval.mmr import mmr_select


def aggregate_candidates(
    retrieval_results: list[dict],
    query: str,
) -> list[dict]:
    candidates = defaultdict(
        lambda: {
            "company_id": None,
            "candidate_id": None,
            "best_rrf_score": 0.0,
            "best_dense_score": 0.0,
            "best_sparse_score": 0.0,
            "all_evidence": [],
            "evidence": [],
        }
    )

    # ---------------------------------------------------------
    # 1. Group retrieved chunks by candidate
    # ---------------------------------------------------------
    for result in retrieval_results:
        metadata = result["metadata"]
        candidate_id = metadata.get("candidate_id")

        if not candidate_id:
            continue

        candidate = candidates[candidate_id]

        candidate["candidate_id"] = candidate_id
        candidate["company_id"] = metadata.get("company_id")

        candidate["best_rrf_score"] = max(
            candidate["best_rrf_score"],
            result["rrf_score"],
        )

        candidate["best_dense_score"] = max(
            candidate["best_dense_score"],
            result["dense_score"],
        )

        candidate["best_sparse_score"] = max(
            candidate["best_sparse_score"],
            result["sparse_score"],
        )

        evidence_item = {
            "id": result["id"],
            "company_id": metadata.get("company_id"),
            "candidate_id": metadata.get("candidate_id"),
            "section": metadata.get("section"),
            "text": metadata.get("text", ""),
            "rrf_score": result["rrf_score"],
            "dense_score": result["dense_score"],
            "sparse_score": result["sparse_score"],
        }

        candidate["all_evidence"].append(evidence_item)

    # ---------------------------------------------------------
    # 2. Apply MMR only to the evidence used for diversity
    # ---------------------------------------------------------
    results = list(candidates.values())

    for candidate in results:
        all_evidence = candidate["all_evidence"]

        if not all_evidence:
            candidate["evidence"] = []
            continue

        if len(all_evidence) == 1:
            candidate["evidence"] = all_evidence.copy()
            continue

        mmr_documents = []

        for item in all_evidence:
            mmr_documents.append(
                {
                    **item,
                    "metadata": {
                        "text": item["text"],
                    },
                }
            )

        selected_evidence = mmr_select(
            query=query,
            documents=mmr_documents,
            top_k=min(5, len(all_evidence)),
            lambda_mult=0.7,
        )

        candidate["evidence"] = selected_evidence

    # ---------------------------------------------------------
    # 3. Sort candidates by strongest RRF evidence
    # ---------------------------------------------------------
    results.sort(
        key=lambda candidate: candidate["best_rrf_score"],
        reverse=True,
    )

    return results