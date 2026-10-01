from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings


def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    """
    Create and return the Google Gemini embedding model.
    """

    return GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        output_dimensionality=settings.EMBEDDING_DIMENSION,
    )