from pathlib import Path
from typing import Any

from app.matching.jd_parser import (
    parse_job_description_file,
)
from app.rag.adaptive import (
    run_adaptive_rag,
)


# =========================================================
# SEARCH QUERY
# =========================================================

def build_matching_query(
    jd: dict[str, Any],
) -> str:
    """
    Build a generic retrieval query from the
    structured JD requirements.

    No role, company, candidate, or skill is hardcoded.
    """

    parts: list[str] = []

    job_title = jd.get(
        "job_title"
    )

    if job_title:
        parts.append(
            f"Job title: {job_title}."
        )

    required_skills = jd.get(
        "required_skills",
        [],
    )

    if required_skills:

        parts.append(
            "Required skills: "
            + ", ".join(
                required_skills
            )
            + "."
        )

    preferred_skills = jd.get(
        "preferred_skills",
        [],
    )

    if preferred_skills:

        parts.append(
            "Preferred skills: "
            + ", ".join(
                preferred_skills
            )
            + "."
        )

    required_experience = jd.get(
        "required_experience"
    )

    if required_experience:

        parts.append(
            "Required experience: "
            + str(
                required_experience
            )
            + "."
        )

    preferred_experience = jd.get(
        "preferred_experience"
    )

    if preferred_experience:

        parts.append(
            "Preferred experience: "
            + str(
                preferred_experience
            )
            + "."
        )

    education = jd.get(
        "education_requirements",
        [],
    )

    if education:

        parts.append(
            "Education requirements: "
            + "; ".join(
                education
            )
            + "."
        )

    certifications = jd.get(
        "certifications",
        [],
    )

    if certifications:

        parts.append(
            "Certifications: "
            + ", ".join(
                certifications
            )
            + "."
        )

    other_requirements = jd.get(
        "other_requirements",
        [],
    )

    if other_requirements:

        parts.append(
            "Other requirements: "
            + "; ".join(
                other_requirements
            )
            + "."
        )

    if not parts:

        raise ValueError(
            "No searchable requirements found in JD."
        )

    return " ".join(
        parts
    )


# =========================================================
# CANDIDATE RESPONSE
# =========================================================

def build_candidate_result(
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert internal candidate data into a clean
    API-friendly response structure.
    """

    matching = candidate.get(
        "matching",
        {},
    )

    verification = candidate.get(
        "verification",
        {},
    )

    return {
        "candidate_id": candidate.get(
            "candidate_id"
        ),

        "company_id": candidate.get(
            "company_id"
        ),

        "scores": {
            "match_score": matching.get(
                "match_score",
                0.0,
            ),
            "required_score": matching.get(
                "required_score",
                0.0,
            ),
            "preferred_score": matching.get(
                "preferred_score",
                0.0,
            ),
            "reranker_score": candidate.get(
                "reranker_score",
                0.0,
            ),
            "final_score": candidate.get(
                "final_score",
                0.0,
            ),
        },

        "matching": {
            "required_matches": matching.get(
                "required_matches",
                [],
            ),
            "required_missing": matching.get(
                "required_missing",
                [],
            ),
            "preferred_matches": matching.get(
                "preferred_matches",
                [],
            ),
            "preferred_missing": matching.get(
                "preferred_missing",
                [],
            ),
        },

        "verification": {
            "verified": verification.get(
                "verified",
                False,
            ),
            "required_skill_count": verification.get(
                "required_skill_count",
                0,
            ),
            "evidence_count": verification.get(
                "evidence_count",
                0,
            ),
            "reasons": verification.get(
                "reasons",
                [],
            ),
        },

        "evidence": candidate.get(
            "evidence",
            [],
        ),
    }



# =========================================================
# JD → CANDIDATE MATCHING
# =========================================================

def match_candidates_to_jd(
    jd_path: str | Path,
    company_id: str,
    top_k: int | None = None,
) -> dict[str, Any]:
    """
    Parse a JD PDF and find matching candidates
    belonging to the specified company.
    """

    if not company_id or not company_id.strip():

        raise ValueError(
            "company_id cannot be empty."
        )

    company_id = company_id.strip()

    jd_path = Path(
        jd_path
    )

    if not jd_path.exists():

        raise FileNotFoundError(
            f"JD file not found: {jd_path}"
        )

    # -----------------------------------------------------
    # 1. Parse JD
    # -----------------------------------------------------

    jd = parse_job_description_file(
        jd_path
    )

    # -----------------------------------------------------
    # 2. Build retrieval query
    # -----------------------------------------------------

    query = build_matching_query(
        jd
    )

    # -----------------------------------------------------
    # 3. Extract requirements
    # -----------------------------------------------------

    required_skills = jd.get(
        "required_skills",
        [],
    )

    preferred_skills = jd.get(
        "preferred_skills",
        [],
    )

    # -----------------------------------------------------
    # 4. Run Adaptive RAG
    # -----------------------------------------------------

    rag_result = run_adaptive_rag(
        query=query,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        top_k=top_k,
        company_id=company_id,
    )

    candidates = [
        build_candidate_result(candidate)
        for candidate in rag_result.get(
            "candidates",
            [],
        )
    ]

    # -----------------------------------------------------
    # 5. Return structured result
    # -----------------------------------------------------

    return {
        "company_id": company_id,
        "job_description": {
            "source": jd.get(
                "source"
            ),
            "job_title": jd.get(
                "job_title"
            ),
            "required_skills": (
                required_skills
            ),
            "preferred_skills": (
                preferred_skills
            ),
            "required_experience": jd.get(
                "required_experience"
            ),
            "preferred_experience": jd.get(
                "preferred_experience"
            ),
            "education_requirements": jd.get(
                "education_requirements",
                [],
            ),
            "certifications": jd.get(
                "certifications",
                [],
            ),
            "responsibilities": jd.get(
                "responsibilities",
                [],
            ),
            "other_requirements": jd.get(
                "other_requirements",
                [],
            ),
        },
        "query": query,
        "routing": rag_result.get(
            "routing"
        ),
        "candidate_count": rag_result.get(
            "candidate_count",
            0,
        ),
        "candidates": candidates,
    }