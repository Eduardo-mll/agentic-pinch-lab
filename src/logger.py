import json
from pathlib import Path


from src.paths import HISTORY_PATH as DEFAULT_HISTORY_PATH


def save_experiment(
    experiment_result: dict,
    path: Path = DEFAULT_HISTORY_PATH
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open(
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(
                experiment_result,
                ensure_ascii=False
            )
            + "\n"
        )


def load_history(
    path: Path = DEFAULT_HISTORY_PATH
) -> list[dict]:

    if not path.exists():
        return []

    history = []

    with path.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if line == "":
                continue

            history.append(
                json.loads(line)
            )

    return history