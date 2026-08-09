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

Open http://127.0.0.1:5173 — Vite proxies `/pipeline` and `/ask` to the API.

Put your Gemini key in `.env` at the project root:

```bash
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3-flash-preview
```

