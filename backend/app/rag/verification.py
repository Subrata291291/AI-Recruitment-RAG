from typing import Any


def verify_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    matching = candidate.get("matching", {})

    required_matches = matching.get("required_matches", [])
    required_missing = matching.get("required_missing", [])

    all_evidence = candidate.get("all_evidence", [])
    evidence = candidate.get("evidence", [])

    verified = True
    reasons: list[str] = []

    # ---------------------------------------------------------
    # 1. Candidate identity
    # ---------------------------------------------------------
    candidate_id = candidate.get("candidate_id")

    if not candidate_id:
        verified = False
        reasons.append("Candidate ID is missing.")

    # ---------------------------------------------------------
    # 2. Evidence availability
    # ---------------------------------------------------------
    if not all_evidence and not evidence:
        verified = False
        reasons.append("No supporting evidence was retrieved.")

    # ---------------------------------------------------------
    # 3. Required skill verification
    # ---------------------------------------------------------
    if required_missing:
        verified = False
        reasons.append(
            f"{len(required_missing)} required skill(s) are missing."
        )

    # ---------------------------------------------------------
    # 4. Evidence identity verification
    # ---------------------------------------------------------
    evidence_items = all_evidence or evidence

    invalid_evidence = []

    for item in evidence_items:
        evidence_candidate_id = item.get("candidate_id")

        if evidence_candidate_id and candidate_id:
            if evidence_candidate_id != candidate_id:
                invalid_evidence.append(item.get("id"))

    if invalid_evidence:
        verified = False
        reasons.append(
            "Evidence contains data belonging to a different candidate."
        )

    # ---------------------------------------------------------
    # 5. Company / tenant verification
    # ---------------------------------------------------------
    candidate_company_id = candidate.get("company_id")

    invalid_company_evidence = []

    for item in evidence_items:
        evidence_company_id = item.get("company_id")

        if evidence_company_id and candidate_company_id:
            if evidence_company_id != candidate_company_id:
                invalid_company_evidence.append(item.get("id"))

    if invalid_company_evidence:
        verified = False
        reasons.append(
            "Evidence contains data belonging to a different company."
        )

    # ---------------------------------------------------------
    # 6. Build verification result
    # ---------------------------------------------------------
    return {
        "candidate_id": candidate_id,
        "company_id": candidate_company_id,
        "verified": verified,
        "required_skill_count": len(
            required_matches
        ) + len(required_missing),
        "required_matches": required_matches,
        "required_missing": required_missing,
        "evidence_count": len(evidence_items),
        "reasons": reasons,
    }


def verify_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    verified_candidates = []

    for candidate in candidates:
        verification = verify_candidate(candidate)

        verified_candidate = {
            **candidate,
            "verification": verification,
        }

        verified_candidates.append(verified_candidate)

    return verified_candidates