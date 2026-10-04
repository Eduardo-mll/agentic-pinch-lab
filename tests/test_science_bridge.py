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
