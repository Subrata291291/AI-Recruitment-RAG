from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from app.api.search import router as search_router
from app.api.candidates import router as candidates_router
from app.api.matching import router as matching_router
from app.api.health import router as health_router


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered recruitment search and candidate matching system",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# API ROUTES
# =========================================================

app.include_router(
    search_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    candidates_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    matching_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    health_router,
    prefix=settings.API_PREFIX,
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "AI Recruitment RAG API is running",
        "environment": settings.ENVIRONMENT,
    }