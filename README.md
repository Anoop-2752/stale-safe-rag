# stale-safe-rag



# Stale-Safe RAG

A small RAG system that solves a real production problem: **when a source document changes, how do you know which cached AI answers are now wrong — without regenerating everything?**

## The Problem

In a typical RAG (Retrieval-Augmented Generation) system, answers are often cached to save cost and latency. But when a source document is updated, any cached answer built from the old version becomes silently wrong. Most naive solutions either:
- Never invalidate (answers go stale forever), or
- Clear the entire cache on any change (wasteful, slow, expensive)

## The Solution

This project tracks **exactly which document chunks were used to generate each cached answer** (its "provenance"). Each chunk is fingerprinted with a content hash. When a document changes:

1. Only the specific chunks that actually changed are detected (via hash comparison)
2. A reverse index looks up exactly which cached answers depended on those chunks
3. Only those answers are marked stale and regenerated — everything else stays cached

Result: editing one paragraph in one document invalidates only the answers that relied on it — not the whole cache.

## Setup

**Requirements:** Python 3.11, a free [Groq API key](https://console.groq.com)

```bash
git clone <your-repo-url>
cd stale-safe-rag
conda create -n stalerag python=3.11 -y
conda activate stalerag
pip install -r requirements.txt
```

Create a `.env` file (copy from `.env.example`):

## Usage

```bash
# 1. Build the knowledge base (chunks docs, creates embeddings + index)
python scripts/ingest.py

# 2. Ask a question
python scripts/ask.py "How many annual leave days do employees get?"

# 3. Ask it again — should now come from cache
python scripts/ask.py "How many annual leave days do employees get?"

# 4. Edit any file in data/docs/, then run:
python scripts/refresh.py
# → prints exactly which cached answers are now stale

# 5. Ask the same question again — regenerates automatically
python scripts/ask.py "How many annual leave days do employees get?"
```

## Run tests

```bash
pytest tests/ -v
```

See `DOCUMENTATION.md` for a full breakdown of the folder structure and what each file does.