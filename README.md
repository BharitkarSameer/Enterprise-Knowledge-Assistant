# Enterprise Knowledge Assistant

RAG pipeline for enterprise documents (Markdown first; PDF, DOCX, Confluence later).

## Structure

```text
main.py                 # FastAPI entry point
pipeline/               # Live SSE indexing orchestrator
ingestion/              # File → metadata + payload
processing/             # Sections + typed blocks
chunking/               # 1 section → 1 chunk
embeddings/             # Sentence Transformers
vectorstore/            # Chroma (store only)
retrieval/              # Coming next
generation/             # Coming next
frontend/               # React indexing UI
shared/                 # Common schemas
```

## Setup

```bash
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt

cd frontend
npm install
```

## Run

Terminal 1 — API (project root):

```bash
myenv\Scripts\activate
uvicorn main:app --reload
```

Terminal 2 — UI:

```bash
cd frontend
npm run dev
```

- UI: http://127.0.0.1:5173  
- API docs: http://127.0.0.1:8000/docs  
- Live indexing stream: `POST /pipeline/ingest` (SSE)

CLI without UI:

```bash
python implementation.py
```

## Current status

| Layer       | Status                                      |
|-------------|---------------------------------------------|
| Pipeline    | SSE live steps working                      |
| Ingestion   | Markdown upload working                     |
| Processing  | Markdown sections/blocks working            |
| Chunking    | Section → chunk working                     |
| Embeddings  | MiniLM working                              |
| Vectorstore | Chroma upsert working                       |
| Retrieval   | Stub                                        |
| Generation  | Stub                                        |
| Frontend    | Indexing UI with live step progress         |
