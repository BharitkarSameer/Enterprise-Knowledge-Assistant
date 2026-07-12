

# High Level Architecture

```text
                Data Sources
────────────────────────────────────
Confluence Pages
PDF Documents
Word Documents
Markdown Files
SOPs
Runbooks
Wiki Pages
────────────────────────────────────
                ↓
          Ingestion Layer
                ↓
        Processing Pipeline
                ↓
         Embedding Pipeline
                ↓
            Vector Store
                ↓
      Retrieval + Reranking
                ↓
           LLM Generation
                ↓
          React Frontend
```

---

# Component 1 — Data Ingestion Layer

This is probably the most important module.

## Inputs

### Phase 1 MVP

* PDFs
* TXT
* DOCX
* Markdown

### Phase 2

* Confluence API
* HTML pages
* URLs

### Phase 3

* Jira
* SharePoint
* Internal Wikis

---

## Output

```json
{
    "source": "confluence",
    "title": "Deployment Guide",
    "content": "...",
    "author": "DevOps Team",
    "last_modified": "2026-07-15",
    "url": "...",
    "tags": ["deployment", "prod"]
}
```

---

# Component 2 — Document Processing

## Responsibilities

### Cleaning

Remove:

* headers
* footers
* navigation menus
* page numbers
* duplicate content

---

### Chunking

Example:

```text
Chunk 1
Deployment prerequisites

Chunk 2
Rollback procedure

Chunk 3
Escalation contacts
```

Metadata:

```json
{
    "chunk_id": 15,
    "document": "Deployment Guide",
    "section": "Rollback Procedure",
    "source": "Confluence"
}
```

---

# Component 3 — Embedding Service

Input:

```text
How do I rollback a failed deployment?
```

Output:

```text
[0.182, 0.723, 0.113, ...]
```

Same for chunks.

---

## Candidate Models

Keep interface generic:

```python
embedding_provider.embed(text)
```

This allows:

* OpenAI embeddings
* Ollama embeddings
* Sentence Transformers

without changing the rest of the code.

---

# Component 4 — Vector Database

Stores:

```text
embedding
chunk
metadata
```

Example:

```json
{
  "embedding": [...],
  "document": "Deployment Guide",
  "section": "Rollback",
  "url": "confluence/page/123"
}
```

Potential choices:

* Chroma
* Qdrant
* FAISS

I would start with Chroma.

---

# Component 5 — Retrieval Engine

Query:

> How do I deploy service X?

Steps:

```text
Question
↓
Embedding
↓
Similarity Search
↓
Top K Chunks
↓
Optional reranking
↓
Context Package
```

---

## Future Feature

Hybrid Retrieval:

```text
BM25 score
+
Vector similarity
```

This usually performs much better in enterprise search.

---

# Component 6 — Generation Layer

Input:

```text
Question
+
Retrieved Context
```

Output:

```text
Answer
+
Citations
+
Confidence Score
```

Example:

```text
The rollback procedure requires...

Sources:
Deployment Guide
Section: Rollback
Updated: June 2026
```

---

# Component 7 — React Frontend

## Pages

### Dashboard

Shows:

* Indexed documents
* Confluence spaces
* Recent uploads
* Statistics

---

### Chat Page

```text
Ask a question...
```

Results:

```text
Answer

Sources:
Deployment Guide
Runbook
Incident SOP
```

---

### Source Viewer

Click source:

```text
Open Confluence Page
Jump to Section
Highlight chunk
```

---

# Component 8 — Administration Panel

This is where the project starts looking enterprise-grade.

Features:

* Re-index source
* Delete source
* View ingestion status
* View failures

---

# Suggested Folder Structure

## Backend

```text
backend/
│
├── api/
├── ingestion/
├── processing/
├── embeddings/
├── retrieval/
├── generation/
├── vectorstore/
├── models/
└── services/
```

---

## Frontend

```text
frontend/
│
├── pages/
├── components/
├── services/
├── hooks/
└── context/
```

---

# MVP Scope

Build only:

```text
PDF Upload
↓
Chunk
↓
Embed
↓
Store
↓
Ask Question
↓
Answer + Citation
```

Then add:

```text
Confluence API
```

This ordering is important because:

* RAG pipeline is reusable.
* Only ingestion changes.
* Confluence becomes just another connector.

---

Honestly, the moment you support Confluence pages instead of just PDFs, this stops being a student AI project and starts looking like a lightweight version of products companies actually buy.
