import pytest

from pinch_lab.tools.run_experiment import run_computational_experiment
from pinch_lab.tools.science_bridge import science_available
from src.experiment_runner import load_baseline, run_experiment
from src.network_economics import evaluate_baseline_network_economics
from src.paths import BASELINE_PATH
from src.pinch_engine import run_pinch_analysis


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


def test_baseline_network_economics_ground_truth():
    streams, delta_t_min = load_baseline(BASELINE_PATH)
    pinch = run_pinch_analysis(streams, delta_t_min)
    econ = evaluate_baseline_network_economics(
        streams=streams,
        hot_pinch=float(pinch["hot_pinch_c"]),
        cold_pinch=float(pinch["cold_pinch_c"]),
        delta_t_min=delta_t_min,
    )

    by_name = {item["name"]: item for item in econ["exchangers"]}
    assert by_name["H1-C2"]["area_m2"] == pytest.approx(88.1868, abs=0.05)
    assert by_name["H2-C1"]["area_m2"] == pytest.approx(38.1787, abs=0.05)
    assert by_name["H1-C1"]["area_m2"] == pytest.approx(21.5092, abs=0.05)
    assert by_name["heater-C2"]["area_m2"] == pytest.approx(13.1427, abs=0.05)
    assert by_name["cooler-H1"]["area_m2"] == pytest.approx(2.8721, abs=0.1)
    assert by_name["cooler-H2"]["area_m2"] == pytest.approx(22.0156, abs=0.05)

    assert econ["economics"]["utility_cost_per_year"] == pytest.approx(
        11950.0, abs=0.01
    )
    assert econ["economics"]["equipment_cost_per_year"] == pytest.approx(
        92878.92, abs=1.0
    )
    assert econ["economics"]["total_cost_per_year"] == pytest.approx(
        104828.3995, abs=0.01
    )


def test_science_bridge_includes_area_and_cost():
    result = run_computational_experiment(10.0)
    assert result["network"] is not None
    assert result["economics"] is not None
    assert result["network"]["number_of_exchangers"] == 6
    assert result["network"]["total_area_m2"] > 0
    assert result["economics"]["total_cost_per_year"] == pytest.approx(
        104828.3995, abs=0.01
    )
    assert result["energy"]["heat_recovery_kw"] == 490


def test_run_experiment_results_include_economics():
    result = run_experiment(
        {
            "experiment_id": "E-002-TEST",
            "hypothesis": "energy vs cost",
            "parameters": {"delta_t_min": 10},
        },
        save_result=False,
    )
    assert result["valid"] is True
    assert result["results"]["economics"]["utility_cost_per_year"] == 11950.0
    assert result["results"]["network"]["number_of_exchangers"] == 6
