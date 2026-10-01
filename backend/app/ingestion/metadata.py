from pathlib import Path

from langchain_core.documents import Document


def add_resume_metadata(
    documents: list[Document],
    pdf_path: str | Path,
    company_id: str,
) -> list[Document]:
    pdf_path = Path(pdf_path)

    if not company_id or not company_id.strip():
        raise ValueError("company_id cannot be empty.")

    candidate_id = pdf_path.stem

    for document in documents:
        document.metadata.update({
            "company_id": company_id.strip(),
            "candidate_id": candidate_id,
            "document_type": "resume",
            "source": pdf_path.name,
        })

    return documents