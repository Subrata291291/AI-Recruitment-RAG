# Project Structure

This repository contains a full-stack AI recruitment application with a Python backend and a React frontend.

```text
ai-recruitment-rag/
├── .gitignore
├── README.md
├── workflow.txt
├── working-structure.txt
├── PROJECT_STRUCTURE.md
│
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── README.md
│   ├── requirements.txt
│   ├── venv/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── candidates.py
│   │   │   ├── health.py
│   │   │   ├── matching.py
│   │   │   └── search.py
│   │   ├── embeddings/
│   │   │   ├── __init__.py
│   │   │   └── embedding_model.py
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── chunker.py
│   │   │   ├── ingest_jd.py
│   │   │   ├── ingest.py
│   │   │   ├── jd_chunker.py
│   │   │   ├── jd_loader.py
│   │   │   ├── jd_metadata.py
│   │   │   ├── metadata.py
│   │   │   ├── parser.py
│   │   │   └── resume_loader.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── fallback.py
│   │   │   ├── prompts.py
│   │   │   └── provider.py
│   │   ├── matching/
│   │   │   ├── __init__.py
│   │   │   ├── candidate_aggregator.py
│   │   │   ├── candidate_scorer.py
│   │   │   ├── fit_analysis.py
│   │   │   ├── jd_parser.py
│   │   │   └── query_builder.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── adaptive.py
│   │   │   ├── compression.py
│   │   │   ├── corrective.py
│   │   │   ├── multi_query.py
│   │   │   ├── pipeline.py
│   │   │   ├── router.py
│   │   │   └── verification.py
│   │   ├── retrieval/
│   │   │   ├── __init__.py
│   │   │   ├── dense.py
│   │   │   ├── filters.py
│   │   │   ├── hybrid.py
│   │   │   ├── mmr.py
│   │   │   ├── reranker.py
│   │   │   └── sparse.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── logging.py
│   │   │   └── text.py
│   │   └── vectorstore/
│   │       ├── __init__.py
│   │       └── pinecone_store.py
│   │
│   ├── data/
│   │   ├── bm25_chunks.json
│   │   ├── companies/
│   │   │   └── company_001/
│   │   │       └── resumes/
│   │   ├── job_descriptions/
│   │   └── tmp/
│   │
│   ├── scripts/
│   │   ├── build_bm25.py
│   │   ├── ingest_jds.py
│   │   ├── ingest_resumes.py
│   │   └── search_resumes.py
│   │
│   └── tests/
│
├── frontend/
│   ├── .gitignore
│   ├── .oxlintrc.json
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── README.md
│   ├── vite.config.js
│   ├── node_modules/
│   ├── public/
│   └── src/
│       ├── App.jsx
│       ├── index.css
│       ├── main.jsx
│       ├── assets/
│       ├── components/
│       │   ├── CandidateCard.jsx
│       │   ├── CandidateDetails.jsx
│       │   ├── CandidateList.jsx
│       │   ├── Loading.jsx
│       │   ├── MatchSkills.jsx
│       │   └── SearchBar.jsx
│       ├── hooks/
│       │   └── useCandidateSearch.js
│       ├── pages/
│       │   ├── CandidateProfile.jsx
│       │   └── Dashboard.jsx
│       │   └── SearchResults.jsx
│       ├── services/
│       │   └── api.js
│       └── types/
│           └── candidate.js
│
└── docs / optional notes
    └── (not present in repo) 
```

## Overview

- Backend: Python FastAPI application for ingestion, matching, retrieval, and AI/RAG logic.
- Frontend: Vite + React app for searching and viewing candidate profiles.
- Data: Resume and job description data used for indexing and matching.
- Scripts: Utility modules for ingesting and searching data.

## Main purpose

This project is designed to support AI-based recruitment workflows, including:

- ingesting resumes and job descriptions
- building embeddings and search indexes
- matching candidates against job requirements
- exposing APIs for frontend consumption
- displaying ranked candidates in a user interface
