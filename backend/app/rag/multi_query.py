from typing import Any


def build_multi_queries(
    query: str,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
) -> list[str]:
    """
    Generate multiple retrieval-focused queries dynamically
    from a recruiter query and structured JD requirements.

    No company-specific or role-specific values are hardcoded.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty.")

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

    queries: list[str] = []

    # ---------------------------------------------------------
    # Query 1: Original recruiter query
    # ---------------------------------------------------------

    queries.append(query.strip())

    # ---------------------------------------------------------
    # Query 2: Required-skill focused retrieval
    # ---------------------------------------------------------

    if required_skills:
        queries.append(
            "Candidates with required skills: "
            + ", ".join(required_skills)
            + "."
        )

    # ---------------------------------------------------------
    # Query 3: Experience-focused retrieval
    # ---------------------------------------------------------

    if required_skills:
        queries.append(
            "Find candidates with professional experience "
            "and projects demonstrating: "
            + ", ".join(required_skills)
            + "."
        )

    # ---------------------------------------------------------
    # Query 4: Preferred-skill focused retrieval
    # ---------------------------------------------------------

    if preferred_skills:
        queries.append(
            "Candidates with preferred skills: "
            + ", ".join(preferred_skills)
            + "."
        )

    # ---------------------------------------------------------
    # Query 5: Combined requirement retrieval
    # ---------------------------------------------------------

    if required_skills and preferred_skills:
        queries.append(
            "Find candidates matching these required skills: "
            + ", ".join(required_skills)
            + "; and these preferred skills: "
            + ", ".join(preferred_skills)
            + "."
        )

    # ---------------------------------------------------------
    # Remove duplicate queries
    # ---------------------------------------------------------

    unique_queries = []

    seen = set()

    for item in queries:
        normalized = " ".join(
            item.lower().split()
        )

        if normalized not in seen:
            seen.add(normalized)
            unique_queries.append(item)

    return unique_queries


def generate_multi_query_plan(
    query: str,
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a structured multi-query retrieval plan.
    """

    queries = build_multi_queries(
        query=query,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    return {
        "original_query": query,
        "queries": queries,
        "query_count": len(queries),
    }