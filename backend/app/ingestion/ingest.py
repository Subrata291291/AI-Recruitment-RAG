from pathlib import Path

from app.ingestion.resume_loader import load_resume
from app.ingestion.metadata import add_resume_metadata
from app.ingestion.chunker import chunk_resume
from app.embeddings.embedding_model import get_embedding_model
from app.vectorstore.pinecone_store import upsert_vectors


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def create_vector_id(metadata: dict) -> str:
    return (
        f"{metadata['company_id']}"
        f"_{metadata['candidate_id']}"
        f"_{metadata['section']}"
        f"_{metadata['chunk_index']}"
    )


def ingest_all_resumes(
    company_id: str,
    resume_dir: str | Path,
) -> dict:
    """
    Ingest resumes for a specific company.

    resume_dir contains only the resumes belonging
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

    pdf_files = sorted(
        resume_dir.glob("*.pdf")
    )

    if not pdf_files:
        raise FileNotFoundError(
            f"No resume PDFs found in: {resume_dir}"
        )

    embedding_model = get_embedding_model()

    total_resumes = 0
    total_chunks = 0
    total_vectors = 0

    for pdf_path in pdf_files:

        print(
            f"\nProcessing: {pdf_path.name}"
        )

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

        print(
            f"Chunks created: {len(chunks)}"
        )

        texts = [
            chunk.page_content
            for chunk in chunks
        ]

        embeddings = embedding_model.embed_documents(
            texts
        )

        vectors = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):
            vector_id = create_vector_id(
                chunk.metadata
            )

            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    **chunk.metadata,
                    "text": chunk.page_content,
                },
            })

        if vectors:
            upsert_vectors(
                vectors
            )

        total_resumes += 1
        total_chunks += len(chunks)
        total_vectors += len(vectors)

    return {
        "company_id": company_id,
        "resume_dir": str(resume_dir),
        "resumes": total_resumes,
        "chunks": total_chunks,
        "vectors": total_vectors,
    }