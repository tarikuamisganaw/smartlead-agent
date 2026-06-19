import math
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import DocumentChunk
from app.services.document_service import default_demo_data_dir, ingest_documents
from app.services.embedding_service import (
    EmbeddingProviderError,
    embed_missing_document_chunks,
    embed_query,
    vector_literal,
    vector_rag_enabled,
)

try:  # pragma: no cover - exercised only when sklearn is installed.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - fallback is covered in normal local runs without sklearn.
    TfidfVectorizer = None
    cosine_similarity = None


TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")
GENERIC_QUERY_TOKENS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "cost",
    "does",
    "for",
    "how",
    "intent",
    "is",
    "it",
    "much",
    "price",
    "pricing",
    "question",
    "the",
    "to",
    "what",
    "you",
}
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

        ranked = sorted(zip(scores, self.chunks, strict=True), key=lambda item: item[0], reverse=True)
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
    _ensure_chunks_exist(db)
    settings = get_settings()

    if vector_rag_enabled(db):
        try:
            results = _search_docs_pgvector(db, query, top_k=top_k)
            if results or not settings.rag_fallback_to_local:
                return results
        except Exception:
            db.rollback()
            if not settings.rag_fallback_to_local:
                raise

    return _search_docs_local(db, query, top_k=top_k)


def _search_docs_local(db: Session, query: str, top_k: int = 4) -> list[dict]:
    index = _get_index(db)
    return index.search(query, top_k=top_k)


def _search_docs_pgvector(db: Session, query: str, top_k: int = 4) -> list[dict]:
    if db.bind is None or db.bind.dialect.name != "postgresql":
        raise RuntimeError("pgvector RAG requires a Postgres/Supabase database connection.")

    try:
        embed_missing_document_chunks(db)
        query_embedding = embed_query(query).vectors[0]
    except EmbeddingProviderError:
        raise

    candidate_limit = max(top_k * 4, 12)
    statement = text(
        """
        SELECT
            id AS chunk_id,
            document_id,
            title,
            source,
            chunk_index,
            content,
            GREATEST(0, 1 - (embedding <=> CAST(:query_embedding AS vector))) AS score
        FROM document_chunks
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :candidate_limit
        """
    )
    rows = db.execute(
        statement,
        {
            "query_embedding": vector_literal(query_embedding),
            "candidate_limit": candidate_limit,
        },
    ).mappings().all()

    candidates = [
        (
            float(row["score"] or 0),
            RagChunk(
                id=row["chunk_id"],
                document_id=row["document_id"],
                source=row["source"],
                title=row["title"],
                chunk_index=row["chunk_index"],
                content=row["content"],
            ),
        )
        for row in rows
    ]
    ranked = sorted(
        ((score, chunk) for score, chunk in candidates),
        key=lambda item: item[0],
        reverse=True,
    )
    return [_chunk_to_result(chunk, score) for score, chunk in ranked[:top_k]]


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


def _ensure_chunks_exist(db: Session) -> None:
    has_chunks = db.scalar(select(DocumentChunk.id).limit(1))
    if has_chunks:
        return
    ingest_documents(db, default_demo_data_dir(), clear_existing=True)
    invalidate_rag_index()


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


def _keyword_boost(query: str, chunk: RagChunk) -> float:
    lowered_query = query.lower()
    haystack = f"{chunk.title} {chunk.source} {chunk.content}".lower()
    haystack_tokens = set(_tokenize(haystack))
    specific_query_tokens = _specific_query_tokens(query)
    boost = 0.0

    overlap = set(specific_query_tokens) & haystack_tokens
    if specific_query_tokens:
        boost += min(0.55, 0.12 * len(overlap))
        coverage = len(overlap) / len(set(specific_query_tokens))
        if coverage >= 0.75:
            boost += 0.25
        elif coverage >= 0.5:
            boost += 0.12

    boost += _phrase_overlap_boost(specific_query_tokens, haystack)

    if any(term in lowered_query for term in ("price", "pricing", "cost", "how much")) and (
        "pricing" in haystack or re.search(r"\$\s*\d", haystack)
    ):
        boost += 0.12
    if any(term in lowered_query for term in ("refund", "discount", "guarantee", "promise")) and "refund" in haystack:
        boost += 0.25
    if "case" in lowered_query and "case-studies" in haystack:
        boost += 0.25
    if "website" in lowered_query and any(term in haystack for term in ("website", "services", "pricing")):
        boost += 0.08
    if "seo" in lowered_query and "seo" in haystack:
        boost += 0.08

    return boost


def _specific_query_tokens(query: str) -> list[str]:
    return [token for token in _tokenize(query) if token not in GENERIC_QUERY_TOKENS and not token.endswith("_question")]


def _phrase_overlap_boost(tokens: list[str], haystack: str) -> float:
    if len(tokens) < 2:
        return 0.0

    boost = 0.0
    seen_phrases: set[str] = set()
    for size, weight in ((4, 0.22), (3, 0.16), (2, 0.08)):
        if len(tokens) < size:
            continue
        for index in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[index : index + size])
            if phrase in seen_phrases:
                continue
            seen_phrases.add(phrase)
            if phrase in haystack:
                boost += weight
    return min(boost, 0.45)
