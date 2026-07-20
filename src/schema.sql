-- Tracks every chunk's current content hash (the source of truth for "did this change")
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id    TEXT PRIMARY KEY,   -- e.g. "policy_leave.md#0"
    doc_name    TEXT NOT NULL,
    content     TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cached answers, with a snapshot of which chunk versions produced them
CREATE TABLE IF NOT EXISTS answer_cache (
    query_hash   TEXT PRIMARY KEY,   -- hash of normalized query text
    query_text   TEXT NOT NULL,
    answer       TEXT NOT NULL,
    is_stale     INTEGER DEFAULT 0,  -- 0 = fresh, 1 = stale
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- The reverse index: which cached answers depended on which chunk version
CREATE TABLE IF NOT EXISTS answer_dependencies (
    query_hash        TEXT NOT NULL,
    chunk_id          TEXT NOT NULL,
    chunk_hash_at_gen TEXT NOT NULL,  -- hash of the chunk AT THE TIME this answer was generated
    PRIMARY KEY (query_hash, chunk_id),
    FOREIGN KEY (query_hash) REFERENCES answer_cache(query_hash),
    FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);

CREATE INDEX IF NOT EXISTS idx_dep_chunk ON answer_dependencies(chunk_id);