import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { askQuestion } from "./api";

function pathLabel(path) {
  if (!path?.length) return "Source";
  return path.join(" > ");
}

function dedupeCitations(citations) {
  const seen = new Set();
  const out = [];
  for (const citation of citations ?? []) {
    const key = pathLabel(citation.path) || citation.heading || citation.chunk_id;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(citation);
  }
  return out;
}

export default function ChatPanel() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function onSubmit(event) {
    event.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setLoading(true);

    try {
      const result = await askQuestion(query);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: result.answer,
          citations: dedupeCitations(result.citations),
          model: result.model,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: err instanceof Error ? err.message : String(err),
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="tab-panel chat-panel">
      <div className="chat-thread" aria-live="polite">
        {messages.length === 0 && !loading && (
          <p className="chat-empty">
            Ask a question about your indexed documents — for example,
            “How do I rollback a failed deployment?”
          </p>
        )}

        {messages.map((message, index) => (
          <article
            key={`${message.role}-${index}`}
            className={`bubble bubble-${message.role}${message.isError ? " bubble-error" : ""}`}
          >
            <p className="bubble-role">
              {message.role === "user" ? "You" : "Assistant"}
            </p>
            {message.isError || message.role === "user" ? (
              <p className="bubble-text">{message.text}</p>
            ) : (
              <div className="bubble-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.text}
                </ReactMarkdown>
              </div>
            )}
            {message.citations?.length > 0 && (
              <div className="citations">
                <p className="citations-label">Sources</p>
                <ul>
                  {message.citations.map((citation) => (
                    <li key={citation.chunk_id}>
                      {pathLabel(citation.path) || citation.heading}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </article>
        ))}

        {loading && (
          <article className="bubble bubble-assistant bubble-loading">
            <p className="bubble-role">Assistant</p>
            <div className="typing" aria-label="Thinking">
              <span />
              <span />
              <span />
            </div>
            <p className="muted">Retrieving context and generating answer…</p>
          </article>
        )}
        <div ref={bottomRef} />
      </div>

      <form className="chat-form" onSubmit={onSubmit}>
        <input
          type="text"
          value={input}
          disabled={loading}
          placeholder="Ask about your knowledge base…"
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="primary" type="submit" disabled={loading || !input.trim()}>
          {loading ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
