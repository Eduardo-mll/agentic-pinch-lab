from pinch_lab.agents.evidence import gather_evidence
from pinch_lab.agents.hypothesis import formulate_hypothesis
from pinch_lab.tools.evidence_store import validate_evidence_ids


def test_gather_evidence_returns_approved_ids():
    pack = gather_evidence(
        "Can lowering delta_t_min reduce external utility demand?"
    )
    assert pack["status"] == "OK"
    assert len(pack["evidence_ids"]) >= 1
    assert "EVID-001" in pack["evidence_ids"] or "EVID-002" in pack["evidence_ids"]


def test_invented_evidence_id_is_rejected():
    check = validate_evidence_ids(["EVID-999"])
    assert check["valid"] is False
    assert check["status"] == "INVALID_EVIDENCE_REFERENCE"
    assert "EVID-999" in check["missing_ids"]


def test_hypothesis_requires_evidence():
    hyp = formulate_hypothesis(
        question="test question",
        evidence_ids=[],
        evidence_status="INSUFFICIENT_EVIDENCE",
    )
    assert hyp["status"] == "INSUFFICIENT_EVIDENCE"
    assert hyp["id"] == "HYP-000"


def test_discovery_loop_includes_evidence(tmp_path, monkeypatch):
    from pinch_lab.run_discovery_loop import run_loop

    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.RESULTS_DIR",
        tmp_path / "runs",
    )
    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.HISTORY_PATH",
        tmp_path / "experiments.json",
    )

    records = run_loop(steps=2)
    assert records[0]["evidence_ids"]
    assert records[0]["evidence"]["status"] == "OK"
    assert records[0]["hypothesis"]["id"] == "HYP-001"
