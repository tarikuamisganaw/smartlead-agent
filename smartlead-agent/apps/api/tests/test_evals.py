import pytest
from httpx import ASGITransport, AsyncClient

from app.evals.evaluator import LATEST_RESULTS_PATH, load_eval_cases, read_latest_eval_results, run_all_evals
from app.main import app


def test_eval_cases_load() -> None:
    cases = load_eval_cases()

    assert len(cases) >= 20
    assert all("id" in case for case in cases)
    assert any(case["id"].startswith("multiturn") for case in cases)


def test_run_evals_mock_mode() -> None:
    results = run_all_evals(persist_results=False)

    assert results["total_cases"] > 0
    assert "pass_rate" in results
    assert "intent_correct" in results["metrics"]
    assert "average_latency_ms" in results["metrics"]


@pytest.mark.anyio
async def test_eval_endpoints() -> None:
    if LATEST_RESULTS_PATH.exists():
        LATEST_RESULTS_PATH.unlink()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        cases = await client.get("/evals/cases")
        latest_before = await client.get("/evals/latest")
        run = await client.post("/evals/run")
        latest_after = await client.get("/evals/latest")

    assert cases.status_code == 200
    assert len(cases.json()["cases"]) >= 20
    assert latest_before.status_code == 200
    assert latest_before.json()["status"] == "missing"
    assert run.status_code == 200
    assert run.json()["total_cases"] >= 20
    assert latest_after.status_code == 200
    assert latest_after.json()["total_cases"] >= 20


def test_read_latest_eval_results_missing() -> None:
    if LATEST_RESULTS_PATH.exists():
        LATEST_RESULTS_PATH.unlink()

    latest = read_latest_eval_results()

    assert latest["status"] == "missing"
