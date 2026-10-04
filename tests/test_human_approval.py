from src.experiment_runner import run_experiment
from src.human_gate import approval_error


def test_locked_stream_change_needs_human_approval():
    message = approval_error({"delta_t_min": 10, "fcp": 9})
    assert message is not None
    assert message.startswith("NEEDS_HUMAN_APPROVAL")

    result = run_experiment(
        {
            "experiment_id": "GATE-001",
            "parameters": {"delta_t_min": 10, "supply_temp": 200},
        },
        save_result=False,
    )
    assert result["valid"] is False
    assert "NEEDS_HUMAN_APPROVAL" in result["error"]
    assert "results" not in result


def test_approved_flag_still_does_not_change_streams():
    result = run_experiment(
        {
            "experiment_id": "GATE-002",
            "parameters": {
                "delta_t_min": 10,
                "h": 1.0,
                "human_approved": True,
            },
        },
        save_result=False,
    )
    assert result["valid"] is False
    assert "cannot change" in result["error"]


def test_delta_t_min_inside_range_still_runs():
    result = run_experiment(
        {
            "experiment_id": "GATE-003",
            "parameters": {"delta_t_min": 10},
        },
        save_result=False,
    )
    assert result["valid"] is True
    assert result["results"]["energy"]["maximum_heat_recovery_kw"] == 490
