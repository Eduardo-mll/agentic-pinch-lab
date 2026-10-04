from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_discovery_run(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.RESULTS_DIR",
        tmp_path / "runs",
    )
    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.HISTORY_PATH",
        tmp_path / "experiments.json",
    )

    response = client.post("/discovery/run", json={"steps": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["agentic_proof"]["second_changed"] is True
    assert len(payload["experiments"]) == 2
