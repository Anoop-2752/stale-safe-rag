import hashlib
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str
    doc_name: str
    content: str
    content_hash: str


def hash_content(text: str) -> str:
    """Stable content hash — whitespace-normalized so trivial formatting
    changes don't trigger false invalidation."""
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def chunk_document(filepath: Path) -> list[Chunk]:
    """Split a markdown file into paragraph-level chunks."""
    text = filepath.read_text(encoding="utf-8")
    doc_name = filepath.name

    # split on blank lines -> paragraphs; drop empties
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    for i, para in enumerate(paragraphs):
        chunk_id = f"{doc_name}#{i}"
        chunks.append(Chunk(
            chunk_id=chunk_id,
            doc_name=doc_name,
            content=para,
            content_hash=hash_content(para),
        ))
    return chunks


def chunk_all_docs(docs_dir: Path) -> list[Chunk]:
    all_chunks = []
    for filepath in sorted(docs_dir.glob("*.md")):
        all_chunks.extend(chunk_document(filepath))
    return all_chunks