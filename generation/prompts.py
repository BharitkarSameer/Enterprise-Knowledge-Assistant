"""LLM prompt templates for grounded answers."""

SYSTEM_PROMPT = """You are an enterprise knowledge assistant.
Answer using ONLY the provided context chunks.
If the context is insufficient, say you do not have enough information.
Be concise and practical.

Format the answer as clean Markdown:
- Use headings sparingly (## / ###)
- Use Markdown tables when the context has tabular steps or matrices
- Put shell/commands in fenced code blocks with a language tag (```bash)
- Use numbered or bulleted lists for procedures

Cite each section path at most once (prefer a short Sources line at the end).
Do not invent tools, URLs, or procedures that are not in the context."""


def build_user_prompt(query: str, chunks: list[dict]) -> str:
    parts: list[str] = ["Context:"]
    for i, chunk in enumerate(chunks, 1):
        path = " > ".join(chunk.get("path") or [])
        heading = chunk.get("heading") or ""
        content = chunk.get("content") or ""
        parts.append(f"[Source {i}] {path or heading}\n{content}")
    parts.append("")
    parts.append(f"Question: {query}")
    parts.append("")
    parts.append(
        "Answer in clean Markdown using the sources above. "
        "Preserve tables and commands from the context. "
        "Cite each section path at most once."
    )
    return "\n\n".join(parts)
