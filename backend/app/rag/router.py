from typing import Any

from app.config import settings


def calculate_query_complexity(
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    query: str = "",
) -> dict[str, Any]:
    """
    Estimate recruiter query complexity using structured
    requirements and query characteristics.

    Routing thresholds are loaded from application settings.
    No company-specific or role-specific values are hardcoded.
    """

    required_skills = [
        skill.strip()
        for skill in (required_skills or [])
        if skill and skill.strip()
    ]

    preferred_skills = [
        skill.strip()
        for skill in (preferred_skills or [])
        if skill and skill.strip()
    ]

    query_words = len(query.split())

    required_count = len(required_skills)
    preferred_count = len(preferred_skills)

    total_skills = (
        required_count
        + preferred_count
    )

    # ---------------------------------------------------------
    # Complexity classification
    # ---------------------------------------------------------

    if (
        required_count
        >= settings.ROUTER_COMPLEX_REQUIRED_SKILLS
    ):
        complexity = "complex"

    elif (
        total_skills
        >= settings.ROUTER_COMPLEX_TOTAL_SKILLS
    ):
        complexity = "complex"

    elif (
        required_count
        >= settings.ROUTER_MODERATE_REQUIRED_SKILLS
    ):
        complexity = "moderate"

    elif (
        query_words
        >= settings.ROUTER_MODERATE_QUERY_WORDS
    ):
        complexity = "moderate"

    else:
        complexity = "simple"

    # ---------------------------------------------------------
    # Retrieval strategy
    # ---------------------------------------------------------

    if complexity == "simple":
        strategy = "hybrid"

    elif complexity == "moderate":
        strategy = "hybrid_mmr"

    else:
        strategy = "multi_query_hybrid_mmr"

    return {
        "complexity": complexity,
        "strategy": strategy,
        "required_skill_count": required_count,
        "preferred_skill_count": preferred_count,
        "total_skill_count": total_skills,
        "query_word_count": query_words,
    }


def route_query(
    query: str,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
) -> dict[str, Any]:
    """
    Route a recruiter query to an appropriate RAG strategy.
    """

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    return calculate_query_complexity(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        query=query,
    )