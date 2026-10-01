import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from app.config import settings
from langchain_community.document_loaders import PyPDFLoader


# =========================================================
# LLM
# =========================================================

def get_jd_parser_llm() -> ChatGroq:
    """
    Create the LLM used for extracting structured
    requirements from a job description.
    """

    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0,
    )


# =========================================================
# PROMPT
# =========================================================

def build_jd_parser_prompt(
    jd_text: str,
) -> str:
    """
    Build a generic job-description extraction prompt.

    No company, role, skill, or candidate is hardcoded.
    """

    return f"""
You are a job-description information extraction system.

Analyze the job description below and return ONLY valid JSON.

Do not invent information.
Do not infer requirements that are not supported
by the job description.

If a field is not available:

- use an empty list for list fields
- use null for single-value fields

Extract the following information:

1. job_title
2. required_skills
3. preferred_skills
4. required_experience
5. preferred_experience
6. education_requirements
7. certifications
8. responsibilities
9. other_requirements

Rules:

- required_skills:
  Include skills explicitly stated as required,
  mandatory, must-have, or equivalent.

- preferred_skills:
  Include skills explicitly described as preferred,
  optional, nice-to-have, plus, or equivalent.

- Do not treat every skill mentioned in responsibilities
  as a required skill.

- Keep skill names concise.

- Preserve the meaning of experience requirements.

- Preserve education requirements.

- Preserve certification requirements.

- Preserve important additional requirements.

- Do not create information that is not present
  in the job description.

- Return arrays for list fields.

Return exactly this JSON structure:

{{
    "job_title": null,
    "required_skills": [],
    "preferred_skills": [],
    "required_experience": null,
    "preferred_experience": null,
    "education_requirements": [],
    "certifications": [],
    "responsibilities": [],
    "other_requirements": []
}}

JOB DESCRIPTION:

{jd_text}
"""


# =========================================================
# JSON PARSING
# =========================================================

def parse_json_response(
    response_text: str,
) -> dict[str, Any]:
    """
    Parse JSON returned by the LLM.

    Handles occasional markdown code fences.
    """

    cleaned = response_text.strip()

    if cleaned.startswith("```"):

        lines = cleaned.splitlines()

        if (
            lines
            and lines[0].strip().startswith("```")
        ):
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        cleaned = "\n".join(
            lines
        ).strip()

    try:

        result = json.loads(
            cleaned
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "JD parser returned invalid JSON."
        ) from exc

    if not isinstance(result, dict):

        raise ValueError(
            "JD parser response must be a JSON object."
        )

    return result


# =========================================================
# RESULT NORMALIZATION
# =========================================================

def normalize_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize the structured JD result.

    This function does not add any role-specific
    or skill-specific values.
    """

    list_fields = [
        "required_skills",
        "preferred_skills",
        "education_requirements",
        "certifications",
        "responsibilities",
        "other_requirements",
    ]

    normalized = {
        "job_title": result.get(
            "job_title"
        ),
        "required_skills": [],
        "preferred_skills": [],
        "required_experience": result.get(
            "required_experience"
        ),
        "preferred_experience": result.get(
            "preferred_experience"
        ),
        "education_requirements": [],
        "certifications": [],
        "responsibilities": [],
        "other_requirements": [],
    }

    for field in list_fields:

        value = result.get(
            field,
            [],
        )

        if value is None:
            value = []

        if not isinstance(
            value,
            list,
        ):
            value = [value]

        normalized[field] = [
            str(item).strip()
            for item in value
            if item is not None
            and str(item).strip()
        ]

    if (
        normalized["job_title"]
        is not None
    ):

        normalized["job_title"] = str(
            normalized["job_title"]
        ).strip()

    normalized["required_skills"] = list(
        dict.fromkeys(
            normalized["required_skills"]
        )
    )

    normalized["preferred_skills"] = list(
        dict.fromkeys(
            skill
            for skill in normalized[
                "preferred_skills"
            ]
            if skill
            not in normalized[
                "required_skills"
            ]
        )
    )

    return normalized


# =========================================================
# TEXT → STRUCTURED JD
# =========================================================

def parse_job_description(
    jd_text: str,
) -> dict[str, Any]:
    """
    Extract structured requirements from
    raw job-description text.
    """

    if not jd_text or not jd_text.strip():

        raise ValueError(
            "Job description cannot be empty."
        )

    llm = get_jd_parser_llm()

    prompt = build_jd_parser_prompt(
        jd_text=jd_text
    )

    response = llm.invoke(
        [
            HumanMessage(
                content=prompt
            )
        ]
    )

    response_text = response.content

    if isinstance(
        response_text,
        list,
    ):

        response_text = "".join(
            str(item)
            for item in response_text
        )

    result = parse_json_response(
        str(response_text)
    )

    return normalize_result(
        result
    )


# =========================================================
# PDF → STRUCTURED JD
# =========================================================
def parse_job_description_file(
    pdf_path: str | Path,
) -> dict[str, Any]:
    """
    Load a JD PDF and extract structured requirements.

    The uploaded JD is used only as input for parsing.
    It is not chunked or stored in Pinecone.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"JD file not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected a PDF file, got: {pdf_path.suffix}"
        )

    loader = PyPDFLoader(str(pdf_path))

    documents = loader.load()

    if not documents:
        raise ValueError(
            "No content found in the JD PDF."
        )

    jd_text = "\n\n".join(
        document.page_content
        for document in documents
        if document.page_content.strip()
    )

    if not jd_text.strip():
        raise ValueError(
            "JD PDF contains no readable text."
        )

    result = parse_job_description(jd_text)

    result["source"] = pdf_path.name

    return result

# =========================================================
# LANGCHAIN DOCUMENTS → STRUCTURED JD
# =========================================================

def parse_jd_documents(
    documents: list[Any],
) -> dict[str, Any]:
    """
    Combine LangChain JD documents and
    extract structured requirements.
    """

    if not documents:

        raise ValueError(
            "No JD documents provided."
        )

    text = "\n\n".join(
        document.page_content
        for document in documents
        if document.page_content.strip()
    )

    if not text.strip():

        raise ValueError(
            "JD documents contain no readable text."
        )

    return parse_job_description(
        text
    )