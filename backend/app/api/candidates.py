from pathlib import Path
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from langchain_community.document_loaders import PyPDFLoader

from app.config import BASE_DIR
from app.retrieval.sparse import load_bm25_corpus


router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)


# =========================================================
# Helpers
# =========================================================

def _clean_value(value: str | None) -> str | None:
    if not value:
        return None

    value = " ".join(value.split()).strip()

    return value if value else None


def _extract_candidate_profile(
    company_id: str,
    candidate_id: str,
) -> dict[str, str | None]:

    empty_profile = {
        "full_name": None,
        "phone": None,
        "email": None,
        "address": None,
    }

    # -----------------------------------------------------
    # Validate IDs
    # -----------------------------------------------------

    if not re.fullmatch(r"[A-Za-z0-9_-]+", company_id):
        return empty_profile

    if not re.fullmatch(r"[A-Za-z0-9_-]+", candidate_id):
        return empty_profile

    # -----------------------------------------------------
    # Resume path
    # -----------------------------------------------------

    resume_path = (
        BASE_DIR
        / "data"
        / "companies"
        / company_id
        / "resumes"
        / f"{candidate_id}.pdf"
    )

    if not resume_path.exists():
        return empty_profile

    # -----------------------------------------------------
    # Load PDF
    # -----------------------------------------------------

    try:
        loader = PyPDFLoader(str(resume_path))
        documents = loader.load()
    except Exception:
        return empty_profile

    text = "\n".join(
        document.page_content
        for document in documents
        if document.page_content.strip()
    )

    if not text.strip():
        return empty_profile

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    profile = {
        "full_name": None,
        "phone": None,
        "email": None,
        "address": None,
    }

    # =====================================================
    # EMAIL
    # =====================================================

    email_pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    email_match = re.search(
        email_pattern,
        text,
    )

    if email_match:
        profile["email"] = _clean_value(
            email_match.group(0)
        )

    # =====================================================
    # PHONE
    # =====================================================

    phone_pattern = (
        r"(?<!\d)"
        r"(?:\+\d{1,3}[\s.-]?)?"
        r"(?:\(\d{2,5}\)[\s.-]?)?"
        r"\d{3,5}[\s.-]?"
        r"\d{3,5}"
        r"(?!\d)"
    )

    phone_match = re.search(
        phone_pattern,
        text,
    )

    if phone_match:
        profile["phone"] = _clean_value(
            phone_match.group(0)
        )

    # =====================================================
    # FULL NAME
    # =====================================================

    # Resume names are normally found near the beginning.
    # We intentionally inspect several initial lines instead
    # of assuming a particular capitalization format.

    ignored_headings = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "candidate profile",
        "professional summary",
        "summary",
        "experience",
        "education",
        "skills",
        "core technical skills",
    }

    job_or_skill_terms = {
        "developer",
        "engineer",
        "designer",
        "manager",
        "analyst",
        "consultant",
        "intern",
        "frontend",
        "backend",
        "full stack",
        "software",
        "javascript",
        "typescript",
        "react",
        "wordpress",
        "woocommerce",
        "python",
        "java",
        "html",
        "css",
        "ai",
        "llm",
    }

    for line in lines[:8]:

        candidate = line.strip(" |:-")

        if not candidate:
            continue

        # Don't use contact lines as names.
        if "@" in candidate:
            continue

        # Don't use lines containing phone numbers.
        if re.search(r"\d{3,}", candidate):
            continue

        normalized = re.sub(
            r"[^a-zA-Z ]",
            "",
            candidate,
        ).strip()

        normalized_lower = normalized.lower()

        if normalized_lower in ignored_headings:
            continue

        words = normalized.split()

        # Candidate name should normally contain 2-6 words.
        if not (2 <= len(words) <= 6):
            continue

        # Avoid selecting obvious job title / skill lines.
        lower_line = candidate.lower()

        # Only reject when the line strongly resembles a job title.
        if any(
            term in lower_line
            for term in job_or_skill_terms
        ):
            continue

        profile["full_name"] = candidate
        break

    # =====================================================
    # CONTACT / LOCATION
    # =====================================================

    # IMPORTANT:
    # Do NOT assume lines[1] or lines[2].
    #
    # Find the line that actually contains the email or phone.

    contact_line = None

    for line in lines[:10]:

        has_email = re.search(
            email_pattern,
            line,
        )

        has_phone = re.search(
            phone_pattern,
            line,
        )

        if has_email or has_phone:
            contact_line = line
            break

    if contact_line:

        contact_without_email = re.sub(
            email_pattern,
            "",
            contact_line,
        )

        contact_without_phone = re.sub(
            phone_pattern,
            "",
            contact_without_email,
        )

        parts = [
            part.strip()
            for part in contact_without_phone.split("|")
            if part.strip()
        ]

        # Look for a location-like value.
        for part in parts:

            part_lower = part.lower()

            # Don't use obvious job/skill values.
            if any(
                term in part_lower
                for term in job_or_skill_terms
            ):
                continue

            # Avoid very long sentences.
            if len(part.split()) > 8:
                continue

            # Location should contain alphabetic characters.
            if not re.search(
                r"[A-Za-z]",
                part,
            ):
                continue

            profile["address"] = _clean_value(part)
            break

    return {
        "full_name": _clean_value(
            profile["full_name"]
        ),
        "phone": _clean_value(
            profile["phone"]
        ),
        "email": _clean_value(
            profile["email"]
        ),
        "address": _clean_value(
            profile["address"]
        ),
    }


# =========================================================
# Candidate List
# =========================================================

@router.get("")
def list_candidates(
    company_id: str = Query(...),
) -> dict[str, Any]:

    if not company_id or not company_id.strip():
        raise HTTPException(
            status_code=400,
            detail="company_id cannot be empty.",
        )

    company_id = company_id.strip()

    try:
        corpus = load_bm25_corpus()

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Candidate index is not available.",
        ) from exc

    company_items = [
        item
        for item in corpus
        if item.get("metadata", {}).get("company_id")
        == company_id
    ]

    candidates: dict[str, dict[str, Any]] = {}

    for item in company_items:

        metadata = item.get("metadata", {})

        candidate_id = metadata.get("candidate_id")

        if not candidate_id:
            continue

        if candidate_id not in candidates:

            candidates[candidate_id] = {
                "candidate_id": candidate_id,
                "company_id": company_id,
                "sections": set(),
                "chunk_count": 0,
            }

        candidate = candidates[candidate_id]

        section = metadata.get("section")

        if section:
            candidate["sections"].add(section)

        candidate["chunk_count"] += 1

    result = []

    for candidate in candidates.values():

        candidate["sections"] = sorted(
            candidate["sections"]
        )

        result.append(candidate)

    result.sort(
        key=lambda candidate:
        candidate["candidate_id"]
    )

    return {
        "company_id": company_id,
        "candidate_count": len(result),
        "candidates": result,
    }


# =========================================================
# Candidate Details
# =========================================================

@router.get("/{candidate_id}")
def get_candidate(
    candidate_id: str,
    company_id: str = Query(...),
) -> dict[str, Any]:

    if not candidate_id or not candidate_id.strip():
        raise HTTPException(
            status_code=400,
            detail="candidate_id cannot be empty.",
        )

    if not company_id or not company_id.strip():
        raise HTTPException(
            status_code=400,
            detail="company_id cannot be empty.",
        )

    candidate_id = candidate_id.strip()
    company_id = company_id.strip()

    try:
        corpus = load_bm25_corpus()

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Candidate index is not available.",
        ) from exc

    candidate_items = [
        item
        for item in corpus
        if (
            item.get("metadata", {}).get("company_id")
            == company_id
            and
            item.get("metadata", {}).get("candidate_id")
            == candidate_id
        )
    ]

    if not candidate_items:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    sections = set()
    evidence = []

    for item in candidate_items:

        metadata = item.get("metadata", {})

        section = metadata.get("section")

        if section:
            sections.add(section)

        evidence.append({
            "id": item.get("id"),
            "section": section,
            "text": item.get("text", ""),
        })

    # =====================================================
    # Extract actual candidate profile from resume PDF
    # =====================================================

    profile = _extract_candidate_profile(
        company_id=company_id,
        candidate_id=candidate_id,
    )

    return {
        "candidate_id": candidate_id,

        "company_id": company_id,

        "profile": {
            "full_name": profile.get("full_name"),
            "phone": profile.get("phone"),
            "email": profile.get("email"),
            "address": profile.get("address"),
        },

        "sections": sorted(sections),

        "chunk_count": len(evidence),

        "evidence": evidence,
    }