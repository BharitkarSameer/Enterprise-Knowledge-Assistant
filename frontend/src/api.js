export const PIPELINE_STEPS = [
  "ingestion",
  "processing",
  "chunking",
  "embeddings",
  "vectorstore",
];

export const STEP_LABELS = {
  ingestion: "Ingestion",
  processing: "Processing",
  chunking: "Chunking",
  embeddings: "Embeddings",
  vectorstore: "Vector store",
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export async function runIngestPipeline(file, onEvent) {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_BASE}/pipeline/ingest`, {
    method: "POST",
    body,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Pipeline request failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part
        .split("\n")
        .map((l) => l.trim())
        .find((l) => l.startsWith("data:"));
      if (!line) continue;
      const json = line.replace(/^data:\s*/, "");
      onEvent(JSON.parse(json));
    }
  }
}

export async function askQuestion(query) {
  const response = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      top_k: 2,
      candidate_k: 6,
      use_reranker: true,
    }),
  });

  if (!response.ok) {
    let detail = `Ask failed (${response.status})`;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return response.json();
}
