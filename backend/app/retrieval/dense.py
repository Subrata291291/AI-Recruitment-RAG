from app.config import settings
from app.embeddings.embedding_model import get_embedding_model
from app.vectorstore.pinecone_store import get_pinecone_index


def dense_search(
    query: str,
    top_k: int | None = None,
    company_id: str | None = None,
) -> list[dict]:

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if company_id is not None and not company_id.strip():
        raise ValueError("company_id cannot be empty when provided.")

    # ---------------------------------------------------------
    # 1. Generate query embedding
    # ---------------------------------------------------------
    try:
        embedding_model = get_embedding_model()
        query_vector = embedding_model.embed_query(query)

    except Exception as exc:
        print(
            "Dense retrieval unavailable. "
            "Falling back to sparse retrieval: "
            f"{type(exc).__name__}: {exc}"
        )
        return []

    # ---------------------------------------------------------
    # 2. Query Pinecone
    # ---------------------------------------------------------
    index = get_pinecone_index()

    query_kwargs = {
        "vector": query_vector,
        "top_k": top_k or settings.DENSE_TOP_K,
        "include_metadata": True,
    }

    # ---------------------------------------------------------
    # 3. Apply company / tenant isolation
    # ---------------------------------------------------------
    if company_id:
        query_kwargs["filter"] = {
            "company_id": company_id.strip()
        }

    results = index.query(**query_kwargs)

    # ---------------------------------------------------------
    # 4. Normalize Pinecone results
    # ---------------------------------------------------------
    matches = []

    for match in results.matches:
        matches.append(
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata,
            }
        )

    return matches