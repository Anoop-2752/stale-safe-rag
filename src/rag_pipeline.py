import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import sqlite3
import hashlib
from src.embedder import embed_texts
from src.vector_store import VectorStore
from src.generator import generate_answer

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "db" / "cache.sqlite3"


def hash_query(query: str) -> str:
    normalized = " ".join(query.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def ask(query: str, top_k: int = 3) -> dict:
    conn = sqlite3.connect(DB_PATH)
    query_hash = hash_query(query)

    # 1. Check cache first
    row = conn.execute(
        "SELECT answer, is_stale FROM answer_cache WHERE query_hash = ?", (query_hash,)
    ).fetchone()

    if row and row[1] == 0:
        conn.close()
        return {"answer": row[0], "source": "cache", "stale": False}

    # 2. Retrieve relevant chunks
    store = VectorStore(dim=384)  # all-MiniLM-L6-v2 output size
    store.load(ROOT / "db")

    query_embedding = embed_texts([query])
    results = store.search(query_embedding, top_k=top_k)
    chunk_ids = [chunk_id for chunk_id, _ in results]

    chunk_rows = conn.execute(
        f"SELECT chunk_id, content, content_hash FROM chunks WHERE chunk_id IN ({','.join('?' * len(chunk_ids))})",
        chunk_ids,
    ).fetchall()
    chunk_map = {r[0]: {"content": r[1], "hash": r[2]} for r in chunk_rows}

    # 3. Generate answer
    context_texts = [chunk_map[cid]["content"] for cid in chunk_ids if cid in chunk_map]
    answer = generate_answer(query, context_texts)

    # 4. Store in cache + record provenance (this is the key step)
    conn.execute(
        "INSERT OR REPLACE INTO answer_cache (query_hash, query_text, answer, is_stale) VALUES (?, ?, ?, 0)",
        (query_hash, query, answer),
    )
    conn.execute("DELETE FROM answer_dependencies WHERE query_hash = ?", (query_hash,))
    for cid in chunk_ids:
        if cid in chunk_map:
            conn.execute(
                "INSERT INTO answer_dependencies (query_hash, chunk_id, chunk_hash_at_gen) VALUES (?, ?, ?)",
                (query_hash, cid, chunk_map[cid]["hash"]),
            )
    conn.commit()
    conn.close()

    return {"answer": answer, "source": "generated", "chunks_used": chunk_ids, "stale": False}