from typing import Any

from app.embeddings.embedding_model import get_embedding_model


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        return 0.0

    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )

    norm_a = sum(a * a for a in vector_a) ** 0.5
    norm_b = sum(b * b for b in vector_b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def mmr_select(
    query: str,
    documents: list[dict[str, Any]],
    top_k: int = 5,
    lambda_mult: float = 0.7,
) -> list[dict[str, Any]]:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not documents:
        return []

    top_k = min(top_k, len(documents))

    if top_k <= 0:
        return []

    if not 0.0 <= lambda_mult <= 1.0:
        raise ValueError("lambda_mult must be between 0 and 1.")

    try:
        embedding_model = get_embedding_model()

        # Query embedding
        query_embedding = embedding_model.embed_query(query)

        # Document embeddings
        document_texts = [
            document.get("page_content")
            or document.get("text")
            or document.get("metadata", {}).get("text", "")
            for document in documents
        ]

        document_embeddings = embedding_model.embed_documents(
            document_texts
        )

    except Exception as exc:
        # -----------------------------------------------------
        # Embedding unavailable:
        # return original documents instead of crashing RAG
        # -----------------------------------------------------
        print(
            "MMR unavailable. Using original evidence order: "
            f"{type(exc).__name__}: {exc}"
        )

        return documents[:top_k]

    selected_indexes: list[int] = []
    remaining_indexes = list(range(len(documents)))

    # ---------------------------------------------------------
    # MMR selection
    # ---------------------------------------------------------
    while remaining_indexes and len(selected_indexes) < top_k:

        best_index = None
        best_score = float("-inf")

        for index in remaining_indexes:

            relevance = cosine_similarity(
                query_embedding,
                document_embeddings[index],
            )

            if not selected_indexes:
                diversity = 0.0

            else:
                similarity_to_selected = max(
                    cosine_similarity(
                        document_embeddings[index],
                        document_embeddings[selected_index],
                    )
                    for selected_index in selected_indexes
                )

                diversity = similarity_to_selected

            mmr_score = (
                lambda_mult * relevance
                - (1 - lambda_mult) * diversity
            )

            if mmr_score > best_score:
                best_score = mmr_score
                best_index = index

        if best_index is None:
            break

        selected_indexes.append(best_index)
        remaining_indexes.remove(best_index)

    return [
        documents[index]
        for index in selected_indexes
    ]