"""
Enterprise Knowledge Assistant — API entry point.

Run from project root:
    uvicorn main:app --reload
"""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parent / ".env")

from ingestion.api import router as ingestion_router
from processing.api import router as processing_router
from chunking.api import router as chunking_router
from embeddings.api import router as embeddings_router
from vectorstore.api import router as vectorstore_router
from pipeline.api import router as pipeline_router
from retrieval.api import router as retrieval_router
from generation.api import router as generation_router

app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="Ingestion → Processing → Chunking → Embeddings → Vector store → Retrieval → Generation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline_router)
app.include_router(ingestion_router)
app.include_router(processing_router)
app.include_router(chunking_router)
app.include_router(embeddings_router)
app.include_router(vectorstore_router)
app.include_router(retrieval_router)
app.include_router(generation_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
