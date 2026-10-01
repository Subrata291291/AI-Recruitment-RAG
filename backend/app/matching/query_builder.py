from typing import Any


def build_jd_query(
    required_skills: list[str],
    preferred_skills: list[str] | None = None,
    role_title: str | None = None,
) -> str:
    """
    Build a recruiter search query from structured JD requirements.
    """

    required = [
        skill.strip()
        for skill in required_skills
        if skill and skill.strip()
    ]

    preferred = [
        skill.strip()
        for skill in (preferred_skills or [])
        if skill and skill.strip()
    ]

    parts = []

    if role_title:
        parts.append(
            f"Find candidates for the {role_title} role."
        )

    if required:
        parts.append(
            "Required skills: "
            + ", ".join(required)
            + "."
        )

    if preferred:
        parts.append(
            "Preferred skills: "
            + ", ".join(preferred)
            + "."
        )

    parts.append(
        "Find candidates with relevant professional "
        "experience and projects matching these requirements."
    )

    return " ".join(parts)