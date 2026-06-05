import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.document_service import chunk_text, default_demo_data_dir, ingest_documents
from app.database import SessionLocal


@pytest.mark.anyio
async def test_document_ingestion() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/documents/ingest-demo")

    body = response.json()

    assert response.status_code == 200
    assert body["documents_ingested"] >= 6
    assert body["chunks_created"] > 0


@pytest.mark.anyio
async def test_rag_pricing_search() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/documents/ingest-demo")
        response = await client.post("/rag/search", json={"query": "How much does SEO cost?", "top_k": 4})

    body = response.json()

    assert response.status_code == 200
    assert any("pricing.md" in result["title"] for result in body["results"])
    assert any("$1,500" in result["content"] or "SEO Starter" in result["content"] for result in body["results"])


def test_chunk_text_creates_readable_chunks() -> None:
    chunks = chunk_text("First paragraph.\n\nSecond paragraph. " * 80, chunk_size=180, overlap=20)

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)


def test_ingestion_service_directly() -> None:
    db = SessionLocal()
    try:
        result = ingest_documents(db, default_demo_data_dir(), clear_existing=True)
    finally:
        db.close()

    assert result["documents_ingested"] >= 6
    assert result["chunks_created"] > 0
