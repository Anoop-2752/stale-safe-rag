import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import sqlite3
import pytest
from src.invalidate import mark_stale_answers

ROOT = Path(__file__).parent.parent


@pytest.fixture
def test_db(tmp_path):
    """Create a small, fake DB with 2 chunks and 2 cached answers,
    so we can test invalidation logic without touching the real project DB."""
    db_path = tmp_path / "test.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.executescript((ROOT / "src" / "schema.sql").read_text())

    # two chunks, from two different docs
    conn.execute(
        "INSERT INTO chunks (chunk_id, doc_name, content, content_hash) VALUES (?, ?, ?, ?)",
        ("doc1#0", "doc1.md", "leave content", "hashA"),
    )
    conn.execute(
        "INSERT INTO chunks (chunk_id, doc_name, content, content_hash) VALUES (?, ?, ?, ?)",
        ("doc2#0", "doc2.md", "expense content", "hashB"),
    )

    # two cached answers, each depending on a different chunk
    conn.execute(
        "INSERT INTO answer_cache (query_hash, query_text, answer, is_stale) VALUES (?, ?, ?, ?)",
        ("q1", "leave question", "answer1", 0),
    )
    conn.execute(
        "INSERT INTO answer_cache (query_hash, query_text, answer, is_stale) VALUES (?, ?, ?, ?)",
        ("q2", "expense question", "answer2", 0),
    )

    # provenance: q1 depends on doc1#0, q2 depends on doc2#0
    conn.execute(
        "INSERT INTO answer_dependencies (query_hash, chunk_id, chunk_hash_at_gen) VALUES (?, ?, ?)",
        ("q1", "doc1#0", "hashA"),
    )
    conn.execute(
        "INSERT INTO answer_dependencies (query_hash, chunk_id, chunk_hash_at_gen) VALUES (?, ?, ?)",
        ("q2", "doc2#0", "hashB"),
    )

    conn.commit()
    return conn


def test_only_dependent_answer_gets_marked_stale(test_db):
    # simulate doc1#0 changing (its hash no longer matches)
    stale = mark_stale_answers(test_db, changed_chunk_ids=["doc1#0"])

    assert stale == ["q1"]  # only q1 depended on doc1#0

    row = test_db.execute(
        "SELECT is_stale FROM answer_cache WHERE query_hash = 'q1'"
    ).fetchone()
    assert row[0] == 1  # marked stale

    row2 = test_db.execute(
        "SELECT is_stale FROM answer_cache WHERE query_hash = 'q2'"
    ).fetchone()
    assert row2[0] == 0  # untouched


def test_no_changed_chunks_means_no_stale_answers(test_db):
    stale = mark_stale_answers(test_db, changed_chunk_ids=[])
    assert stale == []


def test_multiple_answers_can_share_one_chunk(test_db):
    # add a second answer that ALSO depends on doc1#0
    test_db.execute(
        "INSERT INTO answer_cache (query_hash, query_text, answer, is_stale) VALUES (?, ?, ?, ?)",
        ("q3", "another leave question", "answer3", 0),
    )
    test_db.execute(
        "INSERT INTO answer_dependencies (query_hash, chunk_id, chunk_hash_at_gen) VALUES (?, ?, ?)",
        ("q3", "doc1#0", "hashA"),
    )
    test_db.commit()

    stale = mark_stale_answers(test_db, changed_chunk_ids=["doc1#0"])

    assert set(stale) == {"q1", "q3"}  # both answers depending on doc1#0 go stale

    row = test_db.execute(
        "SELECT is_stale FROM answer_cache WHERE query_hash = 'q2'"
    ).fetchone()
    assert row[0] == 0  # q2 still untouched