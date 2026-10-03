from backend.pinch import run_pinch_analysis


def test_baseline_at_delta_t_min_10():
    result = run_pinch_analysis(delta_t_min=10)

    assert result.status == "VALID"
    assert result.hot_pinch_c == 80
    assert result.cold_pinch_c == 70
    assert result.heat_recovery_kw == 490
    assert result.heating_utility_kw == 100
    assert result.cooling_utility_kw == 95


def test_reject_out_of_range():
    result = run_pinch_analysis(delta_t_min=-20)
    assert result.status == "REJECTED"
    assert "OUT_OF_RANGE" in (result.message or "")
