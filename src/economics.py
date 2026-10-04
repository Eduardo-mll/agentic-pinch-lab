import math


def calculate_u(
    h_hot: float,
    h_cold: float
) -> float:

    if h_hot <= 0:
        raise ValueError(
            "h_hot must be positive."
        )

    if h_cold <= 0:
        raise ValueError(
            "h_cold must be positive."
        )

    return 1.0 / (
        (1.0 / h_hot)
        + (1.0 / h_cold)
    )


def calculate_lmtd(
    delta_t_1: float,
    delta_t_2: float
) -> float:

    if delta_t_1 <= 0:
        raise ValueError(
            "delta_t_1 must be positive."
        )

    if delta_t_2 <= 0:
        raise ValueError(
            "delta_t_2 must be positive."
        )

    if math.isclose(
        delta_t_1,
        delta_t_2,
        abs_tol=1e-12
    ):
        return delta_t_1

    return (
        delta_t_1
        - delta_t_2
    ) / math.log(
        delta_t_1
        / delta_t_2
    )


def calculate_area(
    heat_duty_kw: float,
    u_kw_m2_c: float,
    lmtd_c: float
) -> float:

    if heat_duty_kw < 0:
        raise ValueError(
            "Heat duty cannot be negative."
        )

    if u_kw_m2_c <= 0:
        raise ValueError(
            "U must be positive."
        )

    if lmtd_c <= 0:
        raise ValueError(
            "LMTD must be positive."
        )

    return (
        heat_duty_kw
        / (
            u_kw_m2_c
            * lmtd_c
        )
    )


def calculate_exchanger_cost(
    area_m2: float,
    equipment_type: str
) -> float:

    if area_m2 < 0:
        raise ValueError(
            "Area cannot be negative."
        )

    if equipment_type in {
        "process",
        "cooler"
    }:
        coefficient = 30.0

    elif equipment_type == "heater":
        coefficient = 60.0

    else:
        raise ValueError(
            "equipment_type must be "
            "'process', 'cooler' or 'heater'."
        )

    return (
        15000.0
        + coefficient
        * (area_m2 ** 0.8)
    )


def calculate_utility_cost(
    cooling_kw: float,
    heating_kw: float,
    cooling_rate: float = 10.0,
    heating_rate: float = 110.0
) -> dict:

    if cooling_kw < 0:
        raise ValueError(
            "Cooling load cannot be negative."
        )

    if heating_kw < 0:
        raise ValueError(
            "Heating load cannot be negative."
        )

    cooling_cost = (
        cooling_kw
        * cooling_rate
    )

    heating_cost = (
        heating_kw
        * heating_rate
    )

    return {
        "cooling_cost_per_year":
            cooling_cost,

        "heating_cost_per_year":
            heating_cost,

        "total_utility_cost_per_year":
            cooling_cost
            + heating_cost
    }


def calculate_total_network_cost(
    equipment_costs: list[float],
    cooling_kw: float,
    heating_kw: float
) -> dict:

    exchanger_cost = sum(
        equipment_costs
    )

    utility_costs = (
        calculate_utility_cost(
            cooling_kw=cooling_kw,
            heating_kw=heating_kw
        )
    )

    total_cost = (
        exchanger_cost
        + utility_costs[
            "total_utility_cost_per_year"
        ]
    )

    return {
        "equipment_cost_per_year":
            exchanger_cost,

        "utility_cost_per_year":
            utility_costs[
                "total_utility_cost_per_year"
            ],

        "total_cost_per_year":
            total_cost
    }