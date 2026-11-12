"""RAG sur la politique de remboursement.
Backend principal : ChromaDB (embeddings). Repli : TF-IDF (scikit-learn).
Interface unique : search(query) -> [{source, text, score}], score dans [0, 1]."""
import os
from functools import lru_cache

from config import DATA


def _load_docs() -> list[tuple[str, str]]:
    return [(p.name, p.read_text(encoding="utf-8"))
            for p in sorted((DATA / "policy").glob("*.md"))]


FR_STOP = ["le","la","les","un","une","des","de","du","d","l","et","ou","en","au","aux","a",
           "est","sont","si","se","sa","son","ses","que","qui","pour","par","sur","dans","ce","cette",
           "ne","pas","je","tu","il","elle","nous","vous","ils","mon","ma","mes","y","ont","peut"]


class TfidfIndex:
    min_score = 0.10

    def __init__(self, docs):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.docs = docs
        self.vec = TfidfVectorizer(strip_accents="unicode", lowercase=True,
                                   stop_words=FR_STOP)
        self.matrix = self.vec.fit_transform([t for _, t in docs])

    def search(self, query: str, k: int = 3) -> list[dict]:
        from sklearn.metrics.pairwise import linear_kernel
        scores = linear_kernel(self.vec.transform([query]), self.matrix)[0]
        ranked = sorted(range(len(self.docs)), key=lambda i: -scores[i])[:k]
        return [{"source": self.docs[i][0], "text": self.docs[i][1],
                 "score": float(scores[i])} for i in ranked]


class ChromaIndex:
    min_score = 0.20

    def __init__(self, docs):
        import chromadb
        client = chromadb.EphemeralClient()
        self.col = client.get_or_create_collection(
            "policy", metadata={"hnsw:space": "cosine"})
        self.col.add(ids=[n for n, _ in docs], documents=[t for _, t in docs],
                     metadatas=[{"source": n} for n, _ in docs])

    def search(self, query: str, k: int = 3) -> list[dict]:
        res = self.col.query(query_texts=[query], n_results=k)
        return [{"source": m["source"], "text": d, "score": 1 - dist}
                for m, d, dist in zip(res["metadatas"][0], res["documents"][0],
                                      res["distances"][0])]


@lru_cache(maxsize=1)
def get_index():
    docs = _load_docs()
    if os.getenv("RAG_BACKEND", "chroma") == "chroma":
        try:
            return ChromaIndex(docs)
        except Exception as e:  # chromadb absent ou modèle non téléchargeable
            print(f"[RAG] Chroma indisponible ({e}); repli TF-IDF")
    return TfidfIndex(docs)


def search(query: str, k: int = 3) -> list[dict]:
    return get_index().search(query, k)


def min_score() -> float:
    return get_index().min_score
