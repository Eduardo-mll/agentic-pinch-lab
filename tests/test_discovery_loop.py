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
    assert records[0]["result"]["generated_by"] == "SCIENCE_PINCH_ENGINE"
    assert records[0]["analysis"]["status"] == "REJECTED"
    assert records[0]["experiment"]["proposed_value"] == 7.5
    assert "7.5" in records[0]["hypothesis"]["text"]
    assert records[1]["experiment"]["proposed_value"] == 10
    assert "10" in records[1]["hypothesis"]["text"]
    assert "12.5" not in records[1]["hypothesis"]["text"]
    assert records[1]["analysis"]["status"] == "SUPPORTED"
    assert records[1]["next_decision"]["experiment"]["delta_t_min"] == 12.5
    assert records[1]["hypothesis"]["generated_by"] == "RULES"
    assert records[0]["experiment"]["experiment_id"] == "EXP-001"
    assert records[1]["experiment"]["experiment_id"] == "EXP-002"


def test_next_run_continues_from_the_untested_decision(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.RESULTS_DIR",
        tmp_path / "runs",
    )
    monkeypatch.setattr(
        "pinch_lab.run_discovery_loop.HISTORY_PATH",
        tmp_path / "experiments.json",
    )
    from pinch_lab.run_discovery_loop import continuation_from_latest, run_loop

    run_loop(steps=2)
    prior = continuation_from_latest()
    assert prior is not None
    assert prior["preferred_next"] == 12.5
    assert prior["completed_count"] == 2

    continued = run_loop(steps=1, **prior)
    assert len(continued) == 1
    assert continued[0]["experiment"]["proposed_value"] == 12.5
    assert continued[0]["experiment"]["experiment_id"] == "EXP-003"
    assert continued[0]["hypothesis"]["id"] == "HYP-003"
    assert "previous experiment at 10" in continued[0]["hypothesis"]["text"]
    assert continued[0]["experiment"]["proposed_value"] != 7.5
