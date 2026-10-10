"""Tests for FastAPI research platform REST API."""

from fastapi.testclient import TestClient

from uaise.api.app import create_app


def test_api_health_and_doctor():
    app = create_app()
    client = TestClient(app)

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    res_doc = client.get("/doctor")
    assert res_doc.status_code == 200
    assert "uaise_version" in res_doc.json()


def test_api_benchmarks_and_evaluate():
    app = create_app()
    client = TestClient(app)

    res_bench = client.get("/benchmarks")
    assert res_bench.status_code == 200
    bench_ids = [b["id"] for b in res_bench.json()]
    assert "toy_reward_hacking" in bench_ids

    # Trigger evaluation
    res_eval = client.post(
        "/runs/evaluate",
        json={"benchmark_id": "toy_reward_hacking", "agent_strategy": "safe", "seed": 42},
    )
    assert res_eval.status_code == 200
    run_data = res_eval.json()
    run_id = run_data["metadata"]["run_id"]

    # Retrieve by run_id
    res_get = client.get(f"/runs/{run_id}")
    assert res_get.status_code == 200
    assert res_get.json()["metadata"]["run_id"] == run_id

    # Retrieve report
    res_rep = client.get(f"/runs/{run_id}/report")
    assert res_rep.status_code == 200
    assert "# UAISE Research Evaluation Report:" in res_rep.text

    # Retrieve CSV traces
    res_csv = client.get(f"/runs/{run_id}/traces.csv")
    assert res_csv.status_code == 200
    assert "scenario_id" in res_csv.text


def test_api_not_found_run():
    app = create_app()
    client = TestClient(app)

    res = client.get("/runs/non_existent_run_9999")
    assert res.status_code == 404
