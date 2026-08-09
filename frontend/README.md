# Frontend

React app for document indexing (ingest → Chroma) with live pipeline steps.

## Run

Terminal 1 (API, project root):

```bash
myenv\Scripts\activate
uvicorn main:app --reload
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — Vite proxies `/pipeline` to the API.
