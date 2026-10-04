from pinch_lab.agents.analyst import analyze_result


def _result(delta_t_min: float, total_cost: float, heating: float = 90.0) -> dict:
    return {
        "status": "VALID",
        "delta_t_min": delta_t_min,
        "heating_utility_kw": heating,
        "heat_recovery_kw": 500.0,
        "economics": {
            "equipment_cost_per_year": total_cost - 10000,
            "utility_cost_per_year": 10000,
            "total_cost_per_year": total_cost,
        },
    }


def test_higher_cost_reverses_a_lower_delta_t_min():
    analysis = analyze_result(
        hypothesis={"text": "lower dtmin"},
        experiment={"proposed_value": 7.5, "expected_effect": "reduce_external_utility"},
        result=_result(7.5, 118000.0, heating=87.5),
    )
    assert analysis["decision_basis"] == "total_cost"
    assert analysis["status"] == "REJECTED"
    assert analysis["next_decision"]["experiment"]["delta_t_min"] > 7.5


def test_lower_cost_continues_the_same_direction():
    previous = _result(10.0, 110000.0, heating=100.0)
    analysis = analyze_result(
        hypothesis={"text": "lower dtmin"},
        experiment={"proposed_value": 7.5, "expected_effect": "reduce_external_utility"},
        result=_result(7.5, 100000.0, heating=87.5),
        previous_result=previous,
    )
    assert analysis["status"] == "SUPPORTED"
    assert analysis["next_decision"]["experiment"]["delta_t_min"] < 7.5
    assert analysis["direction"] == "decrease_delta_t_min"
