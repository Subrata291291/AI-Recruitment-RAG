import re
from typing import Any


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for generic requirement matching.

    No skill-specific aliases are used.
    """

    if not text:
        return ""

    text = text.lower()

    # Normalize common dash variants.
    text = (
        text
        .replace("–", "-")
        .replace("—", "-")
        .replace("-", "-")
    )

    # Convert punctuation to spaces while preserving
    # letters and numbers.
    text = re.sub(
        r"[^a-z0-9+#./-]+",
        " ",
        text,
    )

    # Normalize whitespace.
    return " ".join(
        text.split()
    )


# =========================================================
# TOKENIZATION
# =========================================================

def tokenize(text: str) -> list[str]:
    """
    Convert normalized text into tokens.
    """

    normalized = normalize_text(
        text
    )

    if not normalized:
        return []

    return normalized.split()


# =========================================================
# COMPACT TEXT
# =========================================================

def compact_text(text: str) -> str:
    """
    Remove separators from normalized text.

    This helps generic cases such as:

        react.js
        reactjs

    without maintaining a manual alias dictionary.
    """

    return re.sub(
        r"[^a-z0-9]+",
        "",
        normalize_text(text),
    )


# =========================================================
# REQUIREMENT VARIANTS
# =========================================================

def build_requirement_variants(
    requirement: str,
) -> list[str]:
    """
    Build generic textual variants of a requirement.

    This is algorithmic and does not contain
    skill-specific aliases.
    """

    normalized = normalize_text(
        requirement
    )

    if not normalized:
        return []

    variants = {
        normalized,
        compact_text(normalized),
    }

    # Parenthetical content is often a version,
    # abbreviation, or qualification.
    #
    # Example:
    # JavaScript (ES6+)
    #
    # produces:
    # JavaScript
    # JavaScript ES6+
    parenthesis_removed = re.sub(
        r"\([^)]*\)",
        "",
        normalized,
    ).strip()

    if parenthesis_removed:
        variants.add(
            parenthesis_removed
        )
        variants.add(
            compact_text(
                parenthesis_removed
            )
        )

    # Slash-separated terms can appear as:
    #
    # Git/GitHub
    #
    # Treat the complete phrase as well as its
    # individual components.
    slash_parts = [
        part.strip()
        for part in normalized.split("/")
        if part.strip()
    ]

    for part in slash_parts:

        variants.add(part)

        compact_part = compact_text(
            part
        )

        if compact_part:
            variants.add(
                compact_part
            )

    return [
        variant
        for variant in variants
        if variant
    ]


# =========================================================
# REQUIREMENT MATCHING
# =========================================================

def requirement_in_text(
    requirement: str,
    text: str,
) -> bool:
    """
    Determine whether a requirement is supported
    by candidate evidence.

    Matching is generic and does not depend on a
    hardcoded skill dictionary.
    """

    if not requirement or not text:
        return False

    normalized_text = normalize_text(
        text
    )

    if not normalized_text:
        return False

    # -----------------------------------------------------
    # Exact phrase / compact matching
    # -----------------------------------------------------

    variants = build_requirement_variants(
        requirement
    )

    for variant in variants:

        if not variant:
            continue

        # Compact variant
        if (
            variant == compact_text(
                variant
            )
        ):

            if variant in compact_text(
                normalized_text
            ):
                return True

            continue

        # Word-boundary phrase matching.
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(variant)
            + r"(?![a-z0-9])"
        )

        if re.search(
            pattern,
            normalized_text,
        ):
            return True

    # -----------------------------------------------------
    # Token overlap fallback
    # -----------------------------------------------------

    requirement_tokens = set(
        tokenize(requirement)
    )

    text_tokens = set(
        tokenize(text)
    )

    if not requirement_tokens:
        return False

    matched_tokens = (
        requirement_tokens
        & text_tokens
    )

    overlap_ratio = (
        len(matched_tokens)
        / len(requirement_tokens)
    )

    # For multi-word requirements, require meaningful
    # lexical overlap rather than an exact phrase.
    #
    # Example:
    # "REST API integration"
    #
    # can match evidence containing:
    # "REST APIs"
    #
    # without requiring a manually maintained alias.
    if (
        len(requirement_tokens) >= 2
        and overlap_ratio >= 0.5
    ):
        return True

    # Single-token requirements require an exact
    # token match to avoid false positives.
    if (
        len(requirement_tokens) == 1
        and matched_tokens
    ):
        return True

    return False


# =========================================================
# CANDIDATE TEXT
# =========================================================

def collect_candidate_text(
    candidate: dict[str, Any],
) -> str:
    """
    Collect candidate evidence text.

    Prefer all_evidence when available so that
    requirement matching is not limited by MMR compression.
    """

    evidence_source = candidate.get(
        "all_evidence"
    )

    if not evidence_source:
        evidence_source = candidate.get(
            "evidence",
            [],
        )

    evidence_texts = []

    for evidence in evidence_source:

        text = evidence.get(
            "text",
            "",
        ).strip()

        if text:
            evidence_texts.append(
                text
            )

    return "\n".join(
        evidence_texts
    )


# =========================================================
# SINGLE CANDIDATE SCORING
# =========================================================

def score_candidate(
    candidate: dict[str, Any],
    required_skills: list[str],
    preferred_skills: list[str] | None = None,
) -> dict[str, Any]:
    """
    Calculate job-related requirement matching
    for a single candidate.

    Required requirements carry 80% weight.
    Preferred requirements carry 20% weight.
    """

    preferred_skills = (
        preferred_skills or []
    )

    candidate_text = (
        collect_candidate_text(
            candidate
        )
    )

    # -----------------------------------------------------
    # Required requirements
    # -----------------------------------------------------

    required_matches = []
    required_missing = []

    for requirement in required_skills:

        if requirement_in_text(
            requirement=requirement,
            text=candidate_text,
        ):
            required_matches.append(
                requirement
            )
        else:
            required_missing.append(
                requirement
            )

    # -----------------------------------------------------
    # Preferred requirements
    # -----------------------------------------------------

    preferred_matches = []
    preferred_missing = []

    for requirement in preferred_skills:

        if requirement_in_text(
            requirement=requirement,
            text=candidate_text,
        ):
            preferred_matches.append(
                requirement
            )
        else:
            preferred_missing.append(
                requirement
            )

    # -----------------------------------------------------
    # Scores
    # -----------------------------------------------------

    required_total = len(
        required_skills
    )

    preferred_total = len(
        preferred_skills
    )

    required_score = (
        len(required_matches)
        / required_total
        if required_total
        else 1.0
    )

    preferred_score = (
        len(preferred_matches)
        / preferred_total
        if preferred_total
        else 0.0
    )

    # Required requirements have higher weight.
    final_score = (
        required_score * 0.80
        + preferred_score * 0.20
    )

    return {
        **candidate,
        "matching": {
            "required_matches": (
                required_matches
            ),
            "required_missing": (
                required_missing
            ),
            "preferred_matches": (
                preferred_matches
            ),
            "preferred_missing": (
                preferred_missing
            ),
            "required_score": round(
                required_score,
                4,
            ),
            "preferred_score": round(
                preferred_score,
                4,
            ),
            "match_score": round(
                final_score,
                4,
            ),
        },
    }


# =========================================================
# MULTIPLE CANDIDATES
# =========================================================

def score_candidates(
    candidates: list[dict[str, Any]],
    required_skills: list[str],
    preferred_skills: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Score and sort multiple candidates.
    """

    scored_candidates = [
        score_candidate(
            candidate=candidate,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
        )
        for candidate in candidates
    ]

    scored_candidates.sort(
        key=lambda candidate: (
            candidate["matching"][
                "match_score"
            ],
            candidate["matching"][
                "required_score"
            ],
        ),
        reverse=True,
    )

    return scored_candidates