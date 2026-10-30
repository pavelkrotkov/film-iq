"""Typed-unit baselines and descriptive coverage for the fixed real cohort."""

from docs.research.scoring.real_evaluation import summarize

WEIGHTS = {
    "list_component": 0.45,
    "critic_component": 0.30,
    "award_component": 0.15,
    "audience_component": 0.10,
}
METRICS = ("rt_positivity_pct", "rt_average_10", "metascore_100")


def weighted(row: dict, weights: dict[str, float]) -> float | None:
    if any(row[key] is None for key in weights):
        return None
    return sum(row[key] * weight for key, weight in weights.items()) / sum(weights.values())


def scaled(value: float | None, scale: float) -> float | None:
    return value / scale if value is not None else None


def observation(ballot: dict, reception: dict, count_cap: int) -> dict:
    row = summarize(ballot) | reception
    row["named_award"] = int(ballot["named_award_win"])
    row["list_component"] = scaled(row["training_count"], count_cap)
    row["critic_component"] = scaled(row["metascore_100"], 100)
    row["award_component"] = row["named_award"]
    row["audience_component"] = scaled(reception["audience_numeric_10"], 10)
    row["full_weighted"] = weighted(row, WEIGHTS)
    row["audience_omitted"] = weighted(row, {key: WEIGHTS[key] for key in tuple(WEIGHTS)[:3]})
    row["list_critic_only"] = weighted(row, {key: WEIGHTS[key] for key in tuple(WEIGHTS)[:2]})
    return row


def coverage(rows: list[dict]) -> dict:
    return {
        "films": len(rows),
        "known_list": sum(row["training_count"] is not None for row in rows),
        "known_reception": sum(row["metascore_100"] is not None for row in rows),
        "known_full_weighted": sum(row["full_weighted"] is not None for row in rows),
    }


def groups(rows: list[dict], key: str) -> dict:
    labels: dict[str, list[dict]] = {}
    for row in rows:
        for label in row[key]:
            labels.setdefault(label, []).append(row)
    return {label: coverage(members) for label, members in sorted(labels.items())}
