from fastapi.testclient import TestClient
import json

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


def test_lab_status_exposes_approval_and_measurement():
    response = client.get("/lab/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["human_approval"]["delta_t_min_min_c"] == 5
    assert payload["human_approval"]["delta_t_min_max_c"] == 30
    assert "fcp" in payload["human_approval"]["locked"]
    measurement = payload["measurement"]
    assert measurement is not None
    assert measurement["speedup"] is None
    assert measurement["cycle_seconds"] > 0
    assert measurement["second_delta_t_min_changed"] is True


def test_clear_saved_runs_removes_only_run_files(tmp_path):
    from backend.api.routes import clear_saved_runs

    runs = tmp_path / "results" / "runs"
    runs.mkdir(parents=True)
    (runs / "RUN-ABC.json").write_text("{}", encoding="utf-8")
    (runs / "keep.txt").write_text("stay", encoding="utf-8")
    history = tmp_path / "results" / "experiments.json"
    history.write_text('{"experiments":[{"run_id":"RUN-ABC"}]}', encoding="utf-8")
    (tmp_path / "results" / "science_history.jsonl").write_text("{}\n", encoding="utf-8")

    payload = clear_saved_runs(tmp_path, history)
    assert payload["removed_runs"] == 1
    assert not (runs / "RUN-ABC.json").exists()
    assert (runs / "keep.txt").read_text(encoding="utf-8") == "stay"
    assert json.loads(history.read_text(encoding="utf-8"))["experiments"] == []
    assert not (tmp_path / "results" / "science_history.jsonl").exists()


def test_discovery_records_reads_saved_files_only():
    response = client.get("/discovery/records")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert isinstance(payload["experiments"], list)
