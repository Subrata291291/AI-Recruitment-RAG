from pinecone import Pinecone, ServerlessSpec

from app.config import settings


def get_pinecone_client() -> Pinecone:
    """
    Create and return a Pinecone client.
    """
    return Pinecone(
        api_key=settings.PINECONE_API_KEY
    )


def create_index_if_not_exists() -> None:
    """
    Create the Pinecone index if it does not already exist.
    """

    pc = get_pinecone_client()

    existing_indexes = pc.list_indexes().names()

    if settings.PINECONE_INDEX_NAME in existing_indexes:
        print(
            f"Index '{settings.PINECONE_INDEX_NAME}' already exists."
        )
        return

    pc.create_index(
        name=settings.PINECONE_INDEX_NAME,
        dimension=settings.EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1",
        ),
    )

    print(
        f"Index '{settings.PINECONE_INDEX_NAME}' created successfully."
    )


def get_pinecone_index():
    """
    Return the Pinecone index object.
    """

    pc = get_pinecone_client()

    return pc.Index(
        settings.PINECONE_INDEX_NAME
    )


def upsert_vectors(vectors: list[dict]) -> None:
    """
    Upload vectors and metadata to Pinecone.
    """

    index = get_pinecone_index()

    index.upsert(
        vectors=vectors
    )

def delete_vectors(vector_ids: list[str]) -> None:
    """
    Delete specific vectors from Pinecone.
    """

    index = get_pinecone_index()

    index.delete(
        ids=vector_ids
    )