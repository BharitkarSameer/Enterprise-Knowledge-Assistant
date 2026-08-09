import { useState } from "react";
import IngestPanel from "./IngestPanel";
import ChatPanel from "./ChatPanel";

export default function App() {
  const [tab, setTab] = useState("ingest");

  return (
    <div className="page">
      <header className="header">
        <p className="eyebrow">Enterprise Knowledge Assistant</p>
        <h1>{tab === "ingest" ? "Document indexing" : "Ask the knowledge base"}</h1>
        <p className="lede">
          {tab === "ingest"
            ? "Upload a markdown file and watch each pipeline stage complete live — from ingestion through Chroma storage."
            : "Chat with your indexed documents. Answers are grounded in retrieved chunks and include citations."}
        </p>
      </header>

      <nav className="tabs" aria-label="Main">
        <button
          type="button"
          className={`tab${tab === "ingest" ? " tab-active" : ""}`}
          onClick={() => setTab("ingest")}
        >
          Ingestion
        </button>
        <button
          type="button"
          className={`tab${tab === "ask" ? " tab-active" : ""}`}
          onClick={() => setTab("ask")}
        >
          Retrieval
        </button>
      </nav>

      {tab === "ingest" ? <IngestPanel /> : <ChatPanel />}
    </div>
  );
}
