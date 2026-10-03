from backend.pinch.calculations import heat_load_kw


def test_h1_heat_load():
    # Q = 3.5 * (180 - 60) = 420 kW
    assert heat_load_kw(3.5, 180, 60) == 420


def test_h2_heat_load():
    assert heat_load_kw(1.5, 140, 30) == 165
