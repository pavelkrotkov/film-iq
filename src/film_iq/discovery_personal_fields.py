"""Only explicit scores and watched fields may enter a private report."""


def personal_fields(film: dict) -> dict:
    if type(film["watched"]) is not bool:
        raise ValueError("personal watched state must be boolean")
    ratings = {key: film[key] for key in ("personal_enjoyment", "personal_artistic_merit")}
    if not all(_valid_score(value) for value in ratings.values()):
        raise ValueError("personal scores must be null or integers 1–10")
    if film["merit_status"] not in {"known", "unknown", "invalid", "conflict"}:
        raise ValueError("unknown artistic-merit review state")
    if (film["merit_status"] == "known") != (ratings["personal_artistic_merit"] is not None):
        raise ValueError("artistic-merit score must agree with its review state")
    return {
        **ratings,
        "watched": film["watched"],
        "watched_dates": film["watched_dates"],
        "merit_status": film["merit_status"],
    }


def _valid_score(value):
    return value is None or (type(value) is int and 1 <= value <= 10)
