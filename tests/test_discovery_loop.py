from pinch_lab.run_discovery_loop import run_loop


def test_second_experiment_changes_because_of_first_result(tmp_path, monkeypatch):
    # Keep test artifacts out of the real results folder.
    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.RESULTS_DIR",
        tmp_path / "runs",
    )
    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.HISTORY_PATH",
        tmp_path / "experiments.json",
    )

    records = run_loop(steps=2)

    assert len(records) == 2
    first_dt = records[0]["experiment"]["proposed_value"]
    second_dt = records[1]["experiment"]["proposed_value"]
    assert first_dt != second_dt

    # Hypothesis is refined after the first analysis.
    assert records[0]["hypothesis"]["id"] == "HYP-001"
    assert records[1]["hypothesis"]["id"] == "HYP-002"
    assert records[0]["evidence_ids"]


    # Second experiment must come from analyst next_decision of the first.
    assert second_dt == records[0]["next_decision"]["experiment"]["delta_t_min"]
    assert records[0]["result"]["generated_by"] in {
        "SCIENCE_PINCH_ENGINE",
        "FAKE_EXPERIMENT",
    }
    assert records[0]["analysis"]["status"] in {"SUPPORTED", "REJECTED", "INCONCLUSIVE"}
