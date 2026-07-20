import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import sqlite3
from src.chunker import chunk_all_docs
from src.embedder import embed_texts
from src.vector_store import VectorStore

ROOT = Path(__file__).parent.parent
DOCS_DIR = ROOT / "data" / "docs"
DB_PATH = ROOT / "db" / "cache.sqlite3"
INDEX_DIR = ROOT / "db"

def main():
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(Path(ROOT / "src" / "schema.sql").read_text())

    chunks = chunk_all_docs(DOCS_DIR)
    print(f"Found {len(chunks)} chunks across docs")

    for c in chunks:
        conn.execute(
            "INSERT OR REPLACE INTO chunks (chunk_id, doc_name, content, content_hash) VALUES (?, ?, ?, ?)",
            (c.chunk_id, c.doc_name, c.content, c.content_hash),
        )
    conn.commit()

    embeddings = embed_texts([c.content for c in chunks])
    store = VectorStore(dim=embeddings.shape[1])
    store.add(embeddings, [c.chunk_id for c in chunks])
    store.save(INDEX_DIR)

    print("Ingest complete. Chunks stored in DB and vector index saved.")

if __name__ == "__main__":
    main()