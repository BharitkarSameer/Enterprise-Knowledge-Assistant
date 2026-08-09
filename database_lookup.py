"""
Inspect chunks stored in local Chroma.

Run with the project venv (chromadb is installed there):
    myenv\\Scripts\\python.exe database_lookup.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PERSIST_DIR = ROOT / "data" / "chroma"
COLLECTION = "knowledge_chunks"

try:
    import chromadb
except ModuleNotFoundError:
    print(
        "chromadb is not installed for this Python.\n"
        "Use the project venv:\n"
        f"  {ROOT / 'myenv' / 'Scripts' / 'python.exe'} database_lookup.py"
    )
    sys.exit(1)

if not PERSIST_DIR.exists():
    print(f"No Chroma data found at: {PERSIST_DIR}")
    print("Run implementation.py first to ingest and store chunks.")
    sys.exit(1)

client = chromadb.PersistentClient(path=str(PERSIST_DIR))
col = client.get_collection(COLLECTION)

print(f"persist_dir: {PERSIST_DIR}")
print(f"collection:  {COLLECTION}")
print(f"count:       {col.count()}")
print()

data = col.get(include=["documents", "metadatas"])
ids = data.get("ids") or []
documents = data.get("documents") or []
metadatas = data.get("metadatas") or []

for i, (cid, doc, meta) in enumerate(zip(ids, documents, metadatas), 1):
    meta = meta or {}
    heading = meta.get("heading", "")
    path = meta.get("path", "")
    preview = (doc or "")[:120].replace("\n", " ")
    print(f"{i}. {cid}")
    print(f"   heading: {heading}")
    print(f"   path:    {path}")
    print(f"   preview: {preview}")
    print()
