from pinch_lab.tools.run_experiment import run_computational_experiment
from pinch_lab.tools.science_bridge import science_available


def test_science_package_is_available():
    assert science_available() is True


def test_science_baseline_near_known_targets():
    result = run_computational_experiment(10.0)
    assert result["status"] == "VALID"
    assert result["generated_by"] == "SCIENCE_PINCH_ENGINE"
    assert result["heat_recovery_kw"] == 490
    assert result["heating_utility_kw"] == 100
    assert result["cooling_utility_kw"] == 95
    assert result["hot_pinch_c"] == 80
    assert result["cold_pinch_c"] == 70


def test_science_rejects_out_of_range():
    result = run_computational_experiment(-5)
    assert result["status"] == "REJECTED"


def test_science_failure_does_not_use_fake_numbers(monkeypatch):
    def explode(delta_t_min: float):
        raise RuntimeError(f"boom at {delta_t_min}")

    monkeypatch.setattr(
        "pinch_lab.tools.run_experiment.run_science_experiment",
        explode,
    )
    result = run_computational_experiment(10.0)
    assert result["status"] == "FAILED"
    assert result["generated_by"] == "SCIENCE_PINCH_ENGINE"
    assert result["heat_recovery_kw"] is None
    assert result["engine"]["mode"] == "scientific"
    assert result["engine"]["fallback_used"] is False
    assert "boom" in result["message"]


def test_simulation_mode_is_explicit():
    result = run_computational_experiment(10.0, mode="simulation")
    assert result["generated_by"] == "FAKE_EXPERIMENT"
    assert result["engine"]["mode"] == "simulation"
    assert result["engine"]["fallback_used"] is False
