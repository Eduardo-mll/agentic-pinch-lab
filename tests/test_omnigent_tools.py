from pinch_lab.tools.omnigent_tools import (
    tool_gather_evidence,
    tool_run_discovery_loop,
    tool_run_experiment,
    tool_validate_evidence_ids,
)


def test_tool_gather_and_validate_evidence():
    pack = tool_gather_evidence(
        "Can lowering delta_t_min reduce external utility demand?"
    )
    assert pack["status"] == "OK"
    check = tool_validate_evidence_ids(pack["evidence_ids"])
    assert check["valid"] is True
    bad = tool_validate_evidence_ids(["EVID-999"])
    assert bad["valid"] is False


def test_tool_run_experiment_and_loop(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.RESULTS_DIR",
        tmp_path / "runs",
    )
    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.HISTORY_PATH",
        tmp_path / "experiments.json",
    )

    result = tool_run_experiment(7.5)
    assert result["status"] == "VALID"
    assert result["generated_by"] == "SCIENCE_PINCH_ENGINE"
    assert result["engine"]["fallback_used"] is False

    payload = tool_run_discovery_loop(steps=2)
    assert payload["status"] == "ok"
    assert payload["agentic_proof"]["second_changed"] is True
