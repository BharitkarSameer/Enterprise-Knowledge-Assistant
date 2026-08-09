"""Source connectors. Register new file/API types here as they are added."""

from .markdown import parse_markdown

# extension → (file_type label, connector coroutine)
CONNECTORS = {
    ".md": ("markdown", parse_markdown),
    ".markdown": ("markdown", parse_markdown),
}

__all__ = ["CONNECTORS", "parse_markdown"]
