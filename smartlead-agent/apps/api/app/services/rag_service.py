import math
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import DocumentChunk
from app.services.document_service import default_demo_data_dir, ingest_documents

try:  # pragma: no cover - exercised only when sklearn is installed.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - fallback is covered in normal local runs without sklearn.
    TfidfVectorizer = None
    cosine_similarity = None


TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")
_CACHED_INDEX: "LocalRagIndex | None" = None


@dataclass
class RagChunk:
    id: str
    document_id: str
    source: str
    title: str
    chunk_index: int
    content: str


@dataclass
class LocalRagIndex:
    chunks: list[RagChunk]
    vectorizer: Any | None = None
    matrix: Any | None = None
    idf: dict[str, float] | None = None
    doc_vectors: list[dict[str, float]] | None = None

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        if not self.chunks:
            return []

        if self.vectorizer is not None and self.matrix is not None:
            scores = self._sklearn_scores(query)
        else:
            scores = self._fallback_scores(query)

        ranked = sorted(
            ((score + _keyword_boost(query, chunk), chunk) for score, chunk in zip(scores, self.chunks, strict=True)),
            key=lambda item: item[0],
            reverse=True,
        )
        results = []
        for score, chunk in ranked[:top_k]:
            if score <= 0:
                continue
            results.append(_chunk_to_result(chunk, score))
        return results

    def _sklearn_scores(self, query: str) -> list[float]:
        query_vector = self.vectorizer.transform([query])
        return cosine_similarity(query_vector, self.matrix).flatten().tolist()

    def _fallback_scores(self, query: str) -> list[float]:
        query_tokens = _tokenize(query)
        if not query_tokens or not self.doc_vectors or not self.idf:
            return [0.0 for _ in self.chunks]

        query_vector = _term_vector(query_tokens, self.idf)
        return [_cosine(query_vector, vector) for vector in self.doc_vectors]


def build_index_from_db(db: Session) -> LocalRagIndex:
    statement = select(DocumentChunk).order_by(DocumentChunk.source, DocumentChunk.chunk_index)
    chunks = [_snapshot_chunk(chunk) for chunk in db.scalars(statement).all()]
    texts = [chunk.content for chunk in chunks]

    if not chunks:
        return LocalRagIndex(chunks=[])

    if TfidfVectorizer is not None:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
        return LocalRagIndex(chunks=chunks, vectorizer=vectorizer, matrix=matrix)

    idf = _build_idf(texts)
    doc_vectors = [_term_vector(_tokenize(text), idf) for text in texts]
    return LocalRagIndex(chunks=chunks, idf=idf, doc_vectors=doc_vectors)


def search_docs(db: Session, query: str, top_k: int = 4) -> list[dict]:
    index = _get_index(db)
    if not index.chunks:
        ingest_documents(db, default_demo_data_dir(), clear_existing=True)
        invalidate_rag_index()
        index = _get_index(db)
    return index.search(query, top_k=top_k)


def invalidate_rag_index() -> None:
    global _CACHED_INDEX
    _CACHED_INDEX = None


def _get_index(db: Session) -> LocalRagIndex:
    settings = get_settings()
    if not settings.rag_cache_enabled:
        return build_index_from_db(db)

    global _CACHED_INDEX
    if _CACHED_INDEX is None:
        _CACHED_INDEX = build_index_from_db(db)
    return _CACHED_INDEX


def _snapshot_chunk(chunk: DocumentChunk) -> RagChunk:
    return RagChunk(
        id=chunk.id,
        document_id=chunk.document_id,
        source=chunk.source,
        title=chunk.title,
        chunk_index=chunk.chunk_index,
        content=chunk.content,
    )


def _chunk_to_result(chunk: RagChunk, score: float) -> dict:
    return {
        "chunk_id": chunk.id,
        "document_id": chunk.document_id,
        "title": chunk.title,
        "source": chunk.source,
        "content": chunk.content,
        "score": round(float(score), 4),
    }


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _build_idf(texts: list[str]) -> dict[str, float]:
    documents = [set(_tokenize(text)) for text in texts]
    total = len(documents)
    vocabulary = sorted(set().union(*documents))
    return {
        token: math.log((1 + total) / (1 + sum(1 for document in documents if token in document))) + 1
        for token in vocabulary
    }


def _term_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for token in tokens:
        if token in idf:
            counts[token] = counts.get(token, 0) + 1
    if not counts:
        return {}
    total = sum(counts.values())
    return {token: (count / total) * idf[token] for token, count in counts.items()}


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    overlap = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in overlap)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _keyword_boost(query: str, chunk: DocumentChunk) -> float:
    lowered_query = query.lower()
    haystack = f"{chunk.title} {chunk.source} {chunk.content}".lower()
    boost = 0.0

    if any(term in lowered_query for term in ("price", "pricing", "cost", "how much")) and "pricing" in haystack:
        boost += 0.6
    if any(term in lowered_query for term in ("refund", "discount", "guarantee", "promise")) and "refund" in haystack:
        boost += 0.6
    if "case" in lowered_query and "case-studies" in haystack:
        boost += 0.6
    if "website" in lowered_query and any(term in haystack for term in ("website", "services", "pricing")):
        boost += 0.25
    if "seo" in lowered_query and "seo" in haystack:
        boost += 0.2

    return boost
