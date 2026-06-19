import hashlib
import json
import math
import re
from dataclasses import dataclass

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import DocumentChunk


TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


class EmbeddingProviderError(RuntimeError):
    """Raised when an embedding provider cannot produce vectors."""


@dataclass
class EmbeddingBatch:
    vectors: list[list[float]]
    provider: str
    model: str


def vector_rag_enabled(db: Session | None = None) -> bool:
    settings = get_settings()
    provider = settings.rag_provider.lower().strip()
    if provider in {"supabase", "pgvector", "vector"}:
        return True
    if provider == "auto" and db is not None:
        return _is_postgres_session(db)
    return False


def active_embedding_model_name() -> str:
    settings = get_settings()
    provider = settings.embedding_provider.lower().strip()
    if provider == "gemini":
        return settings.gemini_embedding_model
    if provider == "local":
        return settings.local_embedding_model
    return provider


def embed_texts(texts: list[str]) -> EmbeddingBatch:
    settings = get_settings()
    provider = settings.embedding_provider.lower().strip()
    clean_texts = [text.strip() for text in texts if text and text.strip()]
    if not clean_texts:
        return EmbeddingBatch(vectors=[], provider=provider or "none", model=active_embedding_model_name())

    if provider == "gemini":
        return _embed_with_gemini(clean_texts)
    if provider == "local":
        return _embed_locally(clean_texts)

    raise EmbeddingProviderError(f"Unsupported EMBEDDING_PROVIDER value: {settings.embedding_provider}")


def embed_query(query: str) -> EmbeddingBatch:
    return embed_texts([query])


def embed_missing_document_chunks(db: Session, batch_size: int = 16) -> dict:
    if not vector_rag_enabled(db):
        return {"chunks_embedded": 0, "provider": None, "model": None}

    settings = get_settings()
    model_name = active_embedding_model_name()
    dimension = int(settings.rag_vector_dimension)
    chunks_embedded = 0
    provider_name: str | None = None

    while True:
        statement = (
            select(DocumentChunk)
            .where(
                or_(
                    DocumentChunk.embedding_json.is_(None),
                    DocumentChunk.embedding_model != model_name,
                    DocumentChunk.embedding_dimension != dimension,
                )
            )
            .order_by(DocumentChunk.source, DocumentChunk.chunk_index)
            .limit(batch_size)
        )
        chunks = db.scalars(statement).all()
        if not chunks:
            break

        batch = embed_texts([chunk.content for chunk in chunks])
        provider_name = batch.provider
        if len(batch.vectors) != len(chunks):
            raise EmbeddingProviderError("Embedding provider returned a different number of vectors than chunks.")

        for chunk, vector in zip(chunks, batch.vectors, strict=True):
            _validate_vector_dimension(vector, dimension)
            _store_chunk_embedding(db, chunk, vector, batch.model)
            chunks_embedded += 1
        db.commit()

    return {"chunks_embedded": chunks_embedded, "provider": provider_name, "model": model_name}


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def _embed_with_gemini(texts: list[str]) -> EmbeddingBatch:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise EmbeddingProviderError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini.")

    try:
        from google import genai
    except Exception as exc:  # pragma: no cover - depends on optional package.
        raise EmbeddingProviderError("google-genai is not installed. Install requirements.txt first.") from exc

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.embed_content(
                        model=settings.gemini_embedding_model, 
                        contents=texts,
                        config={"output_dimensionality": 768}
                )
    except Exception as exc:  # pragma: no cover - requires a real provider call.
        raise EmbeddingProviderError(f"Gemini embedding request failed: {exc}") from exc

    vectors = _extract_embedding_vectors(response)
    return EmbeddingBatch(vectors=vectors, provider="gemini", model=settings.gemini_embedding_model)


def _extract_embedding_vectors(response) -> list[list[float]]:
    embeddings = getattr(response, "embeddings", None)
    if embeddings is None:
        embedding = getattr(response, "embedding", None)
        embeddings = [embedding] if embedding is not None else None
    if embeddings is None and isinstance(response, dict):
        embeddings = response.get("embeddings") or response.get("embedding")
        if embeddings and isinstance(embeddings, dict):
            embeddings = [embeddings]
    if not embeddings:
        raise EmbeddingProviderError("Embedding response did not include embeddings.")

    vectors: list[list[float]] = []
    for embedding in embeddings:
        values = getattr(embedding, "values", None)
        if values is None and isinstance(embedding, dict):
            values = embedding.get("values")
        if values is None:
            raise EmbeddingProviderError("Embedding response item did not include values.")
        vectors.append([float(value) for value in values])
    return vectors


def _embed_locally(texts: list[str]) -> EmbeddingBatch:
    settings = get_settings()
    dimension = int(settings.rag_vector_dimension)
    return EmbeddingBatch(
        vectors=[_local_hash_embedding(text, dimension) for text in texts],
        provider="local",
        model=settings.local_embedding_model,
    )


def _local_hash_embedding(text: str, dimension: int) -> list[float]:
    vector = [0.0 for _ in range(dimension)]
    for token in TOKEN_RE.findall(text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _store_chunk_embedding(db: Session, chunk: DocumentChunk, vector: list[float], model_name: str) -> None:
    chunk.embedding_json = json.dumps(vector)
    chunk.embedding_model = model_name
    chunk.embedding_dimension = len(vector)
    db.add(chunk)

    if _is_postgres_session(db) and _pgvector_column_exists(db):
        db.execute(
            text(
                "UPDATE document_chunks "
                "SET embedding = CAST(:embedding AS vector) "
                "WHERE id = :chunk_id"
            ),
            {"embedding": vector_literal(vector), "chunk_id": chunk.id},
        )


def _validate_vector_dimension(vector: list[float], expected_dimension: int) -> None:
    if len(vector) != expected_dimension:
        raise EmbeddingProviderError(
            f"Embedding dimension mismatch: got {len(vector)}, expected {expected_dimension}. "
            "Set RAG_VECTOR_DIMENSION to match your embedding model before creating pgvector rows."
        )


def _is_postgres_session(db: Session) -> bool:
    return db.bind is not None and db.bind.dialect.name == "postgresql"


def _pgvector_column_exists(db: Session) -> bool:
    if not _is_postgres_session(db):
        return False
    result = db.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'document_chunks' AND column_name = 'embedding'"
        )
    ).first()
    return result is not None
