from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # -------------------------
    # Application
    # -------------------------
    APP_NAME: str = "AI Recruitment RAG"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # -------------------------
    # API
    # -------------------------
    API_PREFIX: str = "/api"

    # -------------------------
    # Pinecone
    # -------------------------
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str = "ai-recruitment"

    # -------------------------
    # LLM Providers
    # -------------------------
    GROQ_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    # -------------------------
    # LLM Models
    # -------------------------
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENAI_MODEL: str = "gpt-4o-mini"
    GOOGLE_MODEL: str = "gemini-3.8-flash"

    # -------------------------
    # Embedding
    # -------------------------
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768

    # -------------------------
    # Retrieval
    # -------------------------
    DENSE_TOP_K: int = 20
    SPARSE_TOP_K: int = 20
    FINAL_TOP_K: int = 10

    # ---------------------------------------------------------
    # Adaptive RAG / Query Router
    # ---------------------------------------------------------
    ROUTER_COMPLEX_REQUIRED_SKILLS: int = 6
    ROUTER_COMPLEX_TOTAL_SKILLS: int = 8
    ROUTER_MODERATE_REQUIRED_SKILLS: int = 3
    ROUTER_MODERATE_QUERY_WORDS: int = 15

    # -------------------------
    # Environment file
    # -------------------------
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()