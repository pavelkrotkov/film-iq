"""Render original reception units, population and observed sample count."""


def metric_text(value: dict) -> str:
    units = {
        "percent": "%",
        "score_100": "/100",
        "score_10": "/10",
        "score_5": "/5",
        "count": " count",
        "grade": " grade",
        None: " (unit unknown)",
    }
    amount = "unknown" if value["value"] is None else f"{value['value']}{units[value['unit']]}"
    samples = "unknown" if value["sample_count"] is None else str(value["sample_count"])
    return (
        f"{value['measure']} ({value['population']}, {value['metric']}): {amount}; "
        f"sample count {samples}; measured {value['observed_on'] or 'unknown'}"
    )
