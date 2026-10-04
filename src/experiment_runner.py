import json
import time
from pathlib import Path

from src.models import Stream

from src.pinch_engine import (
    run_pinch_analysis
)

from src.logger import (
    save_experiment
)

from src.network_economics import (
    evaluate_baseline_network_economics
)

from src.paths import BASELINE_PATH


def load_baseline(
    path: Path = BASELINE_PATH
) -> tuple[list[Stream], float]:

    with path.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    streams = [
        Stream(
            id=item["id"],
            type=item["type"],
            supply_temp=float(
                item["supply_temp"]
            ),
            target_temp=float(
                item["target_temp"]
            ),
            fcp=float(
                item["fcp"]
            ),
            h=float(
                item["h"]
            )
        )
        for item in data["streams"]
    ]

    delta_t_min = float(
        data["delta_t_min"]
    )

    return (
        streams,
        delta_t_min
    )


def run_experiment(
    experiment: dict,
    save_result: bool = True
) -> dict:

    start_time = (
        time.perf_counter()
    )

    experiment_id = (
        experiment.get(
            "experiment_id",
            "UNKNOWN"
        )
    )

    try:

        streams, baseline_dtmin = (
            load_baseline()
        )

        parameters = experiment.get(
            "parameters",
            {}
        )

        delta_t_min = float(
            parameters.get(
                "delta_t_min",
                baseline_dtmin
            )
        )

        pinch_result = (
            run_pinch_analysis(
                streams=streams,
                delta_t_min=delta_t_min
            )
        )

        warnings: list[str] = []
        network_economics = None

        try:
            network_economics = (
                evaluate_baseline_network_economics(
                    streams=streams,
                    hot_pinch=float(
                        pinch_result["hot_pinch_c"]
                    ),
                    cold_pinch=float(
                        pinch_result["cold_pinch_c"]
                    ),
                    delta_t_min=delta_t_min,
                )
            )
        except Exception as economics_error:
            warnings.append(
                "Network economics unavailable: "
                f"{economics_error}"
            )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        result = {
            "experiment_id":
                experiment_id,

            "status":
                "completed",

            "valid":
                True,

            "hypothesis":
                experiment.get(
                    "hypothesis"
                ),

            "parameters": {
                "delta_t_min":
                    delta_t_min
            },

            "results": {
                "energy":
                    pinch_result,

                "network":
                    None
                    if network_economics is None
                    else {
                        "total_area_m2":
                            network_economics[
                                "total_area_m2"
                            ],
                        "number_of_exchangers":
                            network_economics[
                                "number_of_exchangers"
                            ],
                        "process_heat_kw":
                            network_economics[
                                "process_heat_kw"
                            ],
                        "topology":
                            network_economics.get(
                                "topology"
                            ),
                        "exchangers":
                            network_economics[
                                "exchangers"
                            ],
                    },

                "economics":
                    None
                    if network_economics is None
                    else network_economics[
                        "economics"
                    ],
            },

            "execution_time_seconds":
                elapsed,

            "warnings":
                warnings
        }

    except Exception as error:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        result = {
            "experiment_id":
                experiment_id,

            "status":
                "failed",

            "valid":
                False,

            "hypothesis":
                experiment.get(
                    "hypothesis"
                ),

            "parameters":
                experiment.get(
                    "parameters",
                    {}
                ),

            "error":
                str(error),

            "execution_time_seconds":
                elapsed
        }

    if save_result:
        save_experiment(
            result
        )

    return result
