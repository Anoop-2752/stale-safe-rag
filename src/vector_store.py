import faiss
import numpy as np
import pickle
from pathlib import Path


class VectorStore:
    def __init__(self, dim: int):
        self.index = faiss.IndexFlatIP(dim)  # cosine similarity (since embeddings are normalized)
        self.chunk_ids: list[str] = []       # parallel array: index position -> chunk_id

    def add(self, embeddings: np.ndarray, chunk_ids: list[str]):
        self.index.add(embeddings)
        self.chunk_ids.extend(chunk_ids)

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> list[tuple[str, float]]:
        scores, indices = self.index.search(query_embedding, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.chunk_ids[idx], float(score)))
        return results

    def save(self, path: Path):
        faiss.write_index(self.index, str(path / "index.faiss"))
        with open(path / "chunk_ids.pkl", "wb") as f:
            pickle.dump(self.chunk_ids, f)

    def load(self, path: Path):
        self.index = faiss.read_index(str(path / "index.faiss"))
        with open(path / "chunk_ids.pkl", "rb") as f:
            self.chunk_ids = pickle.load(f)