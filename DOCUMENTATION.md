
## Folder structure

```
stale-safe-rag/
├── data/docs/           # source markdown documents (the "knowledge base")
├── src/                 # core logic, importable and testable
├── scripts/              # CLI entry points that call into src/
├── db/                   # generated at runtime — SQLite DB + vector index (gitignored)
└── tests/                # automated tests
```

## `data/docs/`

The source-of-truth documents. Currently 4 fake company policy docs (leave, expenses, remote work, security). This is the folder you edit by hand to trigger invalidation — the whole project exists to answer "what happens when something in here changes?"

## `src/` — core logic

**`schema.sql`**
Defines the database structure. Three tables:
- `chunks` — every chunk's current content + content hash (the source of truth for "did this change")
- `answer_cache` — cached answers, with a staleness flag
- `answer_dependencies` — the reverse index: which cached answer used which chunk, and what that chunk's hash was *at the time* the answer was generated

**`chunker.py`**
Splits markdown docs into paragraph-level chunks and generates a stable content hash for each one. Whitespace is normalized before hashing so formatting changes don't falsely trigger invalidation.

**`embedder.py`**
Turns text into numeric vectors (embeddings) using a local sentence-transformers model, so meaning can be compared mathematically. Loads the model once and reuses it.

**`vector_store.py`**
A FAISS-based search index. Stores chunk embeddings and finds the most relevant chunks for a given question based on similarity.

**`generator.py`**
Calls the Groq API (LLaMA 3.3 70B) to generate an answer from a question + retrieved context chunks. Low temperature keeps answers consistent.

**`rag_pipeline.py`**
The main orchestrator. The `ask()` function: checks cache first → if fresh, returns instantly → if not, retrieves relevant chunks → generates an answer → saves the answer to cache **along with which chunks and chunk-hashes produced it** (this is where provenance tracking happens).

**`invalidate.py`**
The core "detective" logic. `find_changed_chunks()` re-reads all docs, re-hashes them, and compares against what's stored to find exactly which chunks changed. `mark_stale_answers()` uses the reverse index to find every cached answer that depended on those chunks and flags them stale — nothing else is touched.

## `scripts/` — CLI entry points

**`ingest.py`**
Run once at the start (and whenever docs are added). Chunks all documents, saves them + their hashes to the database, builds and saves the vector index.

**`ask.py`**
Run to ask a question from the terminal. Calls `rag_pipeline.ask()` and prints the answer along with whether it came from cache or was freshly generated.

**`refresh.py`**
Run after editing a document. Calls `invalidate.py`'s logic and prints a report: which chunks changed, and which cached answers are now stale.

## `db/` (generated, not committed)

- `cache.sqlite3` — the actual database (chunks, cached answers, dependencies)
- `index.faiss` / `chunk_ids.pkl` — the saved vector search index

## `tests/`

**`test_chunker.py`**
Verifies hashing is stable and consistent (same content → same hash, different content → different hash, whitespace differences don't count as real changes), and that documents split into paragraphs correctly.

**`test_invalidate.py`**
The most important test file — proves the core claim of the project using a small fake in-memory database: when one chunk changes, only the cached answers that actually depended on it get marked stale, and everything else stays untouched (even when multiple answers share a dependency on the same chunk).