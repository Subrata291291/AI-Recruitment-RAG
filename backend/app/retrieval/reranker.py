from typing import Any
import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings


def get_reranker_model() -> ChatGoogleGenerativeAI:
    """
    Create the Google Gemini model used for candidate reranking.
    """

    return ChatGoogleGenerativeAI(
        model=settings.GOOGLE_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
        max_retries=0,
    )


def parse_json_response(
    content: str,
) -> list[dict[str, Any]]:
    """
    Parse the JSON returned by the LLM.
    """

    content = str(content).strip()

    content = re.sub(
        r"^```json\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )

    content = re.sub(
        r"^```\s*",
        "",
        content,
    )

    content = re.sub(
        r"\s*```$",
        "",
        content,
    )

    content = content.strip()

    parsed = json.loads(content)

    if isinstance(parsed, dict):
        parsed = parsed.get("results", [])

    if not isinstance(parsed, list):
        raise ValueError(
            "Reranker response must contain a JSON list."
        )

    return parsed


def calculate_fallback_score(
    candidate: dict[str, Any],
) -> float:
    """
    Calculate a deterministic fallback score when
    LLM reranking is unavailable.

    Requirement matching is weighted more heavily than
    retrieval signals.
    """

    matching = candidate.get("matching", {})

    required_score = float(
        matching.get("required_score", 0.0)
    )

    preferred_score = float(
        matching.get("preferred_score", 0.0)
    )

    rrf_score = float(
        candidate.get("best_rrf_score", 0.0)
    )

    # Normalize RRF approximately into a 0-1 range.
    # This is only a supporting signal.
    normalized_rrf = min(
        rrf_score / 0.05,
        1.0,
    )

    fallback_score = (
        required_score * 0.70
        + preferred_score * 0.20
        + normalized_rrf * 0.10
    )

    return round(
        max(0.0, min(1.0, fallback_score)),
        4,
    )


def fallback_rerank(
    candidates: list[dict[str, Any]],
    top_k: int,
    reason: str,
) -> list[dict[str, Any]]:
    """
    Deterministic fallback ranking.

    Used when Gemini reranking is unavailable.
    """

    fallback_candidates = []

    for candidate in candidates:
        fallback_score = calculate_fallback_score(
            candidate
        )

        fallback_candidates.append(
            {
                **candidate,
                "rerank_score": fallback_score,
                "rerank_reason": (
                    "LLM reranking unavailable. "
                    f"Used deterministic fallback: {reason}"
                ),
                "rerank_method": "fallback",
            }
        )

    fallback_candidates.sort(
        key=lambda candidate: (
            candidate["rerank_score"],
            candidate.get("matching", {}).get(
                "required_score",
                0.0,
            ),
            candidate.get("best_rrf_score", 0.0),
        ),
        reverse=True,
    )

    return fallback_candidates[:top_k]


def rerank_candidates(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """
    Rerank candidates using Gemini.

    If Gemini is unavailable because of quota,
    rate limit, temporary service errors, or another
    exception, use deterministic fallback ranking.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if not candidates:
        return []

    limit = top_k or settings.FINAL_TOP_K

    model = get_reranker_model()

    candidate_blocks = []

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        candidate_id = candidate.get(
            "candidate_id",
            f"candidate_{index}",
        )

        evidence_texts = []

        for evidence in candidate.get(
            "evidence",
            [],
        ):
            text = evidence.get(
                "text",
                "",
            ).strip()

            if text:
                section = evidence.get(
                    "section",
                    "Unknown section",
                )

                evidence_texts.append(
                    f"[{section}]\n{text}"
                )

        evidence_text = "\n\n".join(
            evidence_texts
        )

        candidate_blocks.append(
            f"""
CANDIDATE_ID: {candidate_id}

EVIDENCE:
{evidence_text}
"""
        )

    all_candidates_text = "\n\n".join(
        candidate_blocks
    )

    prompt = f"""
You are a recruitment search reranker.

Evaluate the relevance of each candidate to the recruiter query.

RECRUITER QUERY:
{query}

CANDIDATES:
{all_candidates_text}

For EACH candidate, return:
- candidate_id
- score between 0 and 1
- brief evidence-based reason

Important rules:
1. Consider ONLY information present in the candidate evidence.
2. Do not infer missing skills or experience.
3. Do not invent qualifications.
4. Do not use age, gender, ethnicity, religion,
   or other protected/sensitive attributes.
5. Focus only on job-related skills, technologies,
   experience, projects, certifications,
   and responsibilities.
6. A candidate with direct evidence for the requested
   skills should receive a higher relevance score than
   a candidate with only partially related evidence.
7. Do not treat the retrieval score as the candidate's
   match score.
8. Return ALL candidates exactly once.
9. Return ONLY valid JSON.
10. Do not use markdown code fences.

Required JSON format:
[
    {{
        "candidate_id": "candidate_001",
        "score": 0.85,
        "reason": "Strong evidence of React.js, TypeScript and REST API experience."
    }}
]
"""

    try:
        response = model.invoke(prompt)

        content = response.content

        if isinstance(content, list):
            content = "".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict)
            )

        results = parse_json_response(
            content
        )

        ranking_map = {}

        for item in results:
            candidate_id = str(
                item.get(
                    "candidate_id",
                    "",
                )
            ).strip()

            if not candidate_id:
                continue

            try:
                score = float(
                    item.get(
                        "score",
                        0.0,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                score = 0.0

            score = max(
                0.0,
                min(1.0, score),
            )

            reason = str(
                item.get(
                    "reason",
                    "",
                )
            ).strip()

            ranking_map[candidate_id] = {
                "rerank_score": score,
                "rerank_reason": reason,
            }

        reranked_candidates = []

        for candidate in candidates:
            candidate_id = candidate.get(
                "candidate_id"
            )

            ranking = ranking_map.get(
                candidate_id
            )

            if ranking is None:
                # If Gemini forgot a candidate,
                # use deterministic fallback for that
                # candidate instead of assigning 0.
                fallback_score = calculate_fallback_score(
                    candidate
                )

                updated_candidate = {
                    **candidate,
                    "rerank_score": fallback_score,
                    "rerank_reason": (
                        "Candidate was not returned "
                        "by the LLM; deterministic "
                        "fallback score used."
                    ),
                    "rerank_method": "partial_fallback",
                }

            else:
                updated_candidate = {
                    **candidate,
                    "rerank_score": ranking[
                        "rerank_score"
                    ],
                    "rerank_reason": ranking[
                        "rerank_reason"
                    ],
                    "rerank_method": "llm",
                }

            reranked_candidates.append(
                updated_candidate
            )

        reranked_candidates.sort(
            key=lambda candidate: (
                candidate["rerank_score"],
                candidate.get(
                    "matching",
                    {},
                ).get(
                    "required_score",
                    0.0,
                ),
            ),
            reverse=True,
        )

        return reranked_candidates[:limit]

    except Exception as exc:
        print(
            "LLM reranking unavailable. "
            "Using deterministic fallback: "
            f"{type(exc).__name__}: {exc}"
        )

        return fallback_rerank(
            candidates=candidates,
            top_k=limit,
            reason=type(exc).__name__,
        )