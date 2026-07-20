import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import sqlite3
from src.chunker import chunk_all_docs

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "db" / "cache.sqlite3"
DOCS_DIR = ROOT / "data" / "docs"


def find_changed_chunks(conn: sqlite3.Connection) -> list[str]:
    """Compare current doc content against what's stored in the DB.
    Returns chunk_ids whose content_hash has changed (or are new)."""
    current_chunks = chunk_all_docs(DOCS_DIR)
    changed = []

    for c in current_chunks:
        row = conn.execute(
            "SELECT content_hash FROM chunks WHERE chunk_id = ?", (c.chunk_id,)
        ).fetchone()

        if row is None or row[0] != c.content_hash:
            changed.append(c.chunk_id)
            # update the chunks table to the new content + hash
            conn.execute(
                "INSERT OR REPLACE INTO chunks (chunk_id, doc_name, content, content_hash) VALUES (?, ?, ?, ?)",
                (c.chunk_id, c.doc_name, c.content, c.content_hash),
            )

    conn.commit()
    return changed


def mark_stale_answers(conn: sqlite3.Connection, changed_chunk_ids: list[str]) -> list[str]:
    """Using the reverse index, find every cached answer that depended
    on any of the changed chunks, and mark it stale."""
    if not changed_chunk_ids:
        return []

    placeholders = ",".join("?" * len(changed_chunk_ids))
    rows = conn.execute(
        f"SELECT DISTINCT query_hash FROM answer_dependencies WHERE chunk_id IN ({placeholders})",
        changed_chunk_ids,
    ).fetchall()

    stale_query_hashes = [r[0] for r in rows]

    for qh in stale_query_hashes:
        conn.execute("UPDATE answer_cache SET is_stale = 1 WHERE query_hash = ?", (qh,))
    conn.commit()

    return stale_query_hashes


def run_invalidation() -> dict:
    conn = sqlite3.connect(DB_PATH)

    changed_chunks = find_changed_chunks(conn)
    stale_answers = mark_stale_answers(conn, changed_chunks)

    # get readable query text for the report
    stale_details = []
    if stale_answers:
        placeholders = ",".join("?" * len(stale_answers))
        rows = conn.execute(
            f"SELECT query_hash, query_text FROM answer_cache WHERE query_hash IN ({placeholders})",
            stale_answers,
        ).fetchall()
        stale_details = [{"query_hash": r[0], "query_text": r[1]} for r in rows]

    conn.close()

    return {
        "changed_chunks": changed_chunks,
        "stale_answer_count": len(stale_answers),
        "stale_answers": stale_details,
    }