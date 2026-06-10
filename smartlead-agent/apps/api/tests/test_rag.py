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


@pytest.mark.anyio
async def test_uploaded_document_is_searchable_by_rag() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        upload = await client.post(
            "/documents/upload",
            json={
                "title": "custom-services.md",
                "content": "ZebraLocal offers emergency plumbing websites starting at $999 with same-week onboarding.",
            },
        )
        search = await client.post("/rag/search", json={"query": "ZebraLocal plumbing websites", "top_k": 4})

    assert upload.status_code == 200
    assert upload.json()["chunks_created"] > 0
    assert search.status_code == 200
    assert any("custom-services.md" in result["title"] for result in search.json()["results"])
    assert any("ZebraLocal" in result["content"] for result in search.json()["results"])


@pytest.mark.anyio
async def test_ingesting_demo_documents_preserves_uploaded_documents() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        upload = await client.post(
            "/documents/upload",
            json={
                "title": "retained-offer.md",
                "content": "RetainCo offers a custom retained package for $4,444.",
            },
        )
        ingest = await client.post("/documents/ingest-demo")
        documents = await client.get("/documents")
        search = await client.post("/rag/search", json={"query": "RetainCo retained package", "top_k": 4})

    assert upload.status_code == 200
    assert ingest.status_code == 200
    assert any(document["title"] == "retained-offer.md" for document in documents.json()["documents"])
    assert any(result["title"] == "retained-offer.md" for result in search.json()["results"])


@pytest.mark.anyio
async def test_specific_uploaded_pricing_document_beats_generic_pricing_doc() -> None:
    dental_content = (
        "# Dental Clinic Package\n\n"
        "BrightPath offers a dental clinic launch package for $3,456. "
        "It includes local SEO, website design, and appointment lead generation. "
        "The setup timeline is 10 business days."
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/documents/ingest-demo")
        await client.post("/documents/upload", json={"title": "dental-package.md", "content": dental_content})
        search = await client.post(
            "/rag/search",
            json={"query": "How much is the dental clinic launch package?", "top_k": 4},
        )
        chat = await client.post("/chat", json={"message": "How much is the dental clinic launch package?"})

    results = search.json()["results"]

    assert search.status_code == 200
    assert results[0]["title"] == "dental-package.md"
    assert "$3,456" in results[0]["content"]
    assert chat.status_code == 200
    assert "$3,456" in chat.json()["final_response"]


@pytest.mark.anyio
async def test_document_upload_rejects_unsupported_file_type() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/documents/upload",
            json={"title": "bad.pdf", "content": "This should not be accepted."},
        )

    assert response.status_code == 400


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
