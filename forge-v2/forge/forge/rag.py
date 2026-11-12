"""Lightweight RAG over previously approved Forge projects.

Pure-Python TF-IDF cosine similarity — no external ML dependencies.
The corpus is the requirement + generated file contents of every
project whose status is "approved". Persisted to a JSON file so the
index survives restarts and can be rebuilt cheaply.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from forge.config import settings

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


class RAGIndex:
    """A tiny in-memory TF-IDF index with disk persistence."""

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or settings.rag_corpus_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # docs: { doc_id: {"text": str, "meta": dict} }
        self.docs: dict[str, dict[str, Any]] = {}
        self._df: Counter = Counter()
        self._load()

    # ---- persistence ----
    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.docs = data.get("docs", {})
                self._recompute_df()
            except (json.JSONDecodeError, OSError):
                self.docs = {}

    def _save(self) -> None:
        self.path.write_text(
            json.dumps({"docs": self.docs}, ensure_ascii=False),
            encoding="utf-8",
        )

    def _recompute_df(self) -> None:
        self._df = Counter()
        for doc in self.docs.values():
            for term in set(_tokenize(doc["text"])):
                self._df[term] += 1

    # ---- mutation ----
    def add(self, doc_id: str, text: str, meta: dict | None = None) -> None:
        self.docs[doc_id] = {"text": text, "meta": meta or {}}
        self._recompute_df()
        self._save()

    def remove(self, doc_id: str) -> None:
        self.docs.pop(doc_id, None)
        self._recompute_df()
        self._save()

    def clear(self) -> None:
        self.docs.clear()
        self._df.clear()
        self._save()

    def __len__(self) -> int:
        return len(self.docs)

    # ---- search ----
    def _tfidf_vector(self, text: str) -> dict[str, float]:
        tokens = _tokenize(text)
        if not tokens:
            return {}
        tf = Counter(tokens)
        n = len(self.docs)
        total = sum(tf.values())
        vec: dict[str, float] = {}
        for term, count in tf.items():
            df = self._df.get(term, 0)
            if df == 0:
                # term not in corpus: still count it with df=1 so idf is finite
                idf = math.log((n + 1) / 1) + 1 if n else 1.0
            else:
                idf = math.log((n + 1) / (df + 1)) + 1
            vec[term] = (count / total) * idf
        return vec

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(v * b.get(k, 0.0) for k, v in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def search(self, query: str, k: int | None = None) -> list[dict[str, Any]]:
        """Return top-k docs as [{'doc_id','score','snippet','meta'}]."""
        if not self.docs:
            return []
        k = k or settings.rag_top_k
        qvec = self._tfidf_vector(query)
        scored = []
        for doc_id, doc in self.docs.items():
            dvec = self._tfidf_vector(doc["text"])
            score = self._cosine(qvec, dvec)
            if score > 0:
                scored.append((doc_id, score, doc))
        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for doc_id, score, doc in scored[:k]:
            results.append(
                {
                    "doc_id": doc_id,
                    "score": round(score, 4),
                    "snippet": (doc["text"][:240] + "…") if len(doc["text"]) > 240 else doc["text"],
                    "meta": doc.get("meta", {}),
                }
            )
        return results


_index: RAGIndex | None = None


def get_index() -> RAGIndex:
    global _index
    if _index is None:
        _index = RAGIndex()
    return _index


def build_from_approved() -> int:
    """Rebuild the corpus from all approved projects in storage. Returns count."""
    from forge.storage import list_approved_projects

    idx = get_index()
    idx.clear()
    for p in list_approved_projects():
        text = p.get("requirement", "")
        code = p.get("result", {}).get("code", {})
        files_text = "\n".join(
            f.get("content", "") for f in code.get("files", [])
        )
        idx.add(
            p["id"],
            text + "\n" + files_text,
            meta={
                "project_name": p.get("project_name", ""),
                "requirement": text[:200],
            },
        )
    return len(idx)


def retrieve(query: str, k: int | None = None) -> list[dict[str, Any]]:
    if not settings.enable_rag:
        return []
    return get_index().search(query, k)
