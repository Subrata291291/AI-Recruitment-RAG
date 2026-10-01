from pathlib import Path
import json

from rank_bm25 import BM25Okapi

from app.ingestion.resume_loader import load_resume
from app.ingestion.metadata import add_resume_metadata
from app.ingestion.chunker import chunk_resume


BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESUME_DIR = BASE_DIR / "data" / "resumes"
BM25_DATA_FILE = BASE_DIR / "data" / "bm25_chunks.json"


def tokenize(text: str) -> list[str]:
    return text.lower().split()


def build_bm25_corpus(
    company_id: str,
    resume_dir: str | Path,
) -> list[dict]:
    """
    Build BM25 documents for one company.

    resume_dir contains only resumes belonging
    to this company.
    """

    if not company_id or not company_id.strip():
        raise ValueError(
            "company_id cannot be empty."
        )

    company_id = company_id.strip()

    resume_dir = Path(resume_dir)

    if not resume_dir.exists():
        raise FileNotFoundError(
            f"Resume directory not found: {resume_dir}"
        )

    if not resume_dir.is_dir():
        raise ValueError(
            f"resume_dir must be a directory: {resume_dir}"
        )

    corpus = []

    pdf_files = sorted(
        resume_dir.glob("*.pdf")
    )

    if not pdf_files:
        raise FileNotFoundError(
            f"No resume PDFs found in: {resume_dir}"
        )

    for pdf_path in pdf_files:

        documents = load_resume(
            pdf_path
        )

        documents = add_resume_metadata(
            documents,
            pdf_path,
            company_id,
        )

        chunks = chunk_resume(
            documents
        )

        for chunk in chunks:

            vector_id = (
                f"{chunk.metadata['company_id']}"
                f"_{chunk.metadata['candidate_id']}"
                f"_{chunk.metadata['section']}"
                f"_{chunk.metadata['chunk_index']}"
            )

            corpus.append({
                "id": vector_id,
                "text": chunk.page_content,
                "metadata": chunk.metadata,
            })

    return corpus


def save_bm25_corpus(
    corpus: list[dict],
) -> None:
    """
    Save the complete shared BM25 corpus.

    Existing companies are preserved. New company records
    are merged instead of replacing the entire corpus.
    """

    BM25_DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_corpus = []

    if BM25_DATA_FILE.exists():

        with open(
            BM25_DATA_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            existing_corpus = json.load(
                file
            )

    existing_by_id = {
        item["id"]: item
        for item in existing_corpus
    }

    for item in corpus:
        existing_by_id[item["id"]] = item

    merged_corpus = list(
        existing_by_id.values()
    )

    with open(
        BM25_DATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            merged_corpus,
            file,
            ensure_ascii=False,
            indent=2,
        )


def load_bm25_corpus() -> list[dict]:
    """
    Load the shared BM25 corpus containing all companies.
    """

    if not BM25_DATA_FILE.exists():
        raise FileNotFoundError(
            f"BM25 corpus not found: {BM25_DATA_FILE}"
        )

    with open(
        BM25_DATA_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def build_bm25_index(
    corpus: list[dict],
) -> BM25Okapi:
    """
    Build a BM25 index from the supplied corpus.
    """

    tokenized_corpus = [
        tokenize(item["text"])
        for item in corpus
    ]

    return BM25Okapi(
        tokenized_corpus
    )

def build_and_save_bm25_index(
    company_id: str,
    resume_dir: str | Path,
) -> dict:
    """
    Build BM25 chunks for one company and merge them
    into the shared multi-company corpus.
    """

    if not company_id or not company_id.strip():
        raise ValueError(
            "company_id cannot be empty."
        )

    company_id = company_id.strip()

    corpus = build_bm25_corpus(
        company_id=company_id,
        resume_dir=resume_dir,
    )

    save_bm25_corpus(
        corpus
    )

    complete_corpus = load_bm25_corpus()

    company_chunks = [
        item
        for item in complete_corpus
        if item["metadata"].get(
            "company_id"
        ) == company_id
    ]

    return {
        "company_id": company_id,
        "chunks": len(company_chunks),
        "total_chunks": len(complete_corpus),
        "file": str(
            BM25_DATA_FILE
        ),
    }

def sparse_search(
    query: str,
    top_k: int = 20,
    company_id: str | None = None,
) -> list[dict]:
    """
    Perform BM25 sparse retrieval.

    If company_id is supplied, only documents belonging
    to that company are searched.
    """

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if (
        company_id is not None
        and not company_id.strip()
    ):
        raise ValueError(
            "company_id cannot be empty when provided."
        )

    corpus = load_bm25_corpus()

    # ---------------------------------------------------------
    # Tenant filtering
    # ---------------------------------------------------------

    if company_id:

        company_id = company_id.strip()

        corpus = [
            item
            for item in corpus
            if item["metadata"].get(
                "company_id"
            ) == company_id
        ]

    if not corpus:
        return []

    # ---------------------------------------------------------
    # BM25 index
    # ---------------------------------------------------------

    bm25 = build_bm25_index(
        corpus
    )

    tokenized_query = tokenize(
        query
    )

    scores = bm25.get_scores(
        tokenized_query
    )

    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True,
    )[:top_k]

    results = []

    for index in ranked_indexes:

        metadata = {
            **corpus[index]["metadata"],
            "text": corpus[index]["text"],
        }

        results.append({
            "id": corpus[index]["id"],
            "score": float(
                scores[index]
            ),
            "metadata": metadata,
        })

    return results