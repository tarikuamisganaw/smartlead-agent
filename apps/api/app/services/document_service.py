import json
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.services.embedding_service import EmbeddingProviderError, embed_missing_document_chunks, vector_rag_enabled


ALLOWED_UPLOAD_EXTENSIONS = {".md", ".txt"}


def default_demo_data_dir() -> str:
    project_root = Path(__file__).resolve().parents[4]
    return str(project_root / "data" / "demo_business")


def load_demo_documents(data_dir: str) -> list[dict]:
    base_path = Path(data_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"Demo document directory not found: {data_dir}")

    documents = []
    for path in sorted(base_path.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        documents.append(
            {
                "title": path.name,
                "source": str(path),
                "content": content,
            }
        )
    return documents


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    cleaned = "\n".join(line.rstrip() for line in text.strip().splitlines()).strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    overlap = min(overlap, chunk_size // 2)

    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end]

        if end < len(cleaned):
            paragraph_break = chunk.rfind("\n\n")
            sentence_break = chunk.rfind(". ")
            break_at = max(paragraph_break, sentence_break)
            if break_at > chunk_size * 0.45:
                end = start + break_at + (2 if paragraph_break == break_at else 1)
                chunk = cleaned[start:end]

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)

    return chunks


def ingest_documents(db: Session, data_dir: str, clear_existing: bool = True) -> dict:
    documents = load_demo_documents(data_dir)

    try:
        if clear_existing:
            demo_document_ids = list(
                db.scalars(select(Document.id).where(Document.source.not_like("uploaded:%"))).all()
            )
            if demo_document_ids:
                db.execute(delete(DocumentChunk).where(DocumentChunk.document_id.in_(demo_document_ids)))
                db.execute(delete(Document).where(Document.id.in_(demo_document_ids)))
            db.commit()

        chunks_created = 0
        for document_data in documents:
            document = Document(**document_data)
            db.add(document)
            db.flush()

            chunks = chunk_text(document.content)
            for index, chunk in enumerate(chunks):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        source=document.source,
                        title=document.title,
                        chunk_index=index,
                        content=chunk,
                        metadata_json=json.dumps({"title": document.title, "source": document.source}),
                    )
                )
                chunks_created += 1

        db.commit()
        embedding_result = _embed_new_chunks_if_enabled(db)
        return {
            "documents_ingested": len(documents),
            "chunks_created": chunks_created,
            **embedding_result,
        }
    except Exception:
        db.rollback()
        raise


def create_document_from_content(
    db: Session,
    *,
    title: str,
    content: str,
    source: str | None = None,
    organization_id: str | None = None,
) -> dict:
    clean_title = title.strip()
    clean_content = content.strip()
    extension = Path(clean_title).suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError("Only .md and .txt documents can be uploaded.")
    if not clean_content:
        raise ValueError("Uploaded document content cannot be empty.")

    try:
        document = Document(
            organization_id=organization_id,
            title=clean_title,
            source=source or f"uploaded:{clean_title}",
            content=clean_content,
        )
        db.add(document)
        db.flush()

        chunks = chunk_text(document.content)
        for index, chunk in enumerate(chunks):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    organization_id=organization_id,
                    source=document.source,
                    title=document.title,
                    chunk_index=index,
                    content=chunk,
                    metadata_json=json.dumps(
                        {
                            "title": document.title,
                            "source": document.source,
                            "uploaded": True,
                        }
                    ),
                )
            )

        db.commit()
        embedding_result = _embed_new_chunks_if_enabled(db)
        db.refresh(document)
        return {
            "document_id": document.id,
            "title": document.title,
            "source": document.source,
            "chunks_created": len(chunks),
            **embedding_result,
        }
    except Exception:
        db.rollback()
        raise


def list_documents_with_chunk_counts(db: Session) -> list[dict]:
    statement = (
        select(Document, func.count(DocumentChunk.id).label("chunk_count"))
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.title)
    )
    rows = db.execute(statement).all()
    return [
        {
            "id": document.id,
            "title": document.title,
            "source": document.source,
            "created_at": document.created_at.isoformat(),
            "chunk_count": chunk_count,
        }
        for document, chunk_count in rows
    ]


def _embed_new_chunks_if_enabled(db: Session) -> dict:
    if not vector_rag_enabled(db):
        return {"embedding_status": "not_enabled"}

    try:
        result = embed_missing_document_chunks(db)
        return {"embedding_status": "embedded", **result}
    except EmbeddingProviderError as exc:
        db.rollback()
        return {"embedding_status": "failed", "embedding_error": str(exc)}
    except Exception as exc:
        db.rollback()
        return {"embedding_status": "failed", "embedding_error": str(exc)}
