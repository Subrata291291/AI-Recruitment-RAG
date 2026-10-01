from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def load_resume(pdf_path: str | Path) -> list[Document]:
    """
    Load a single resume PDF and return its pages
    as LangChain Document objects.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Resume file not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected a PDF file, got: {pdf_path.suffix}"
        )

    loader = PyPDFLoader(str(pdf_path))

    documents = loader.load()

    return documents