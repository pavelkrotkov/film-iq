"""Only explicit scores and watched fields may enter a private report."""


def personal_fields(film: dict) -> dict:
    if type(film["watched"]) is not bool:
        raise ValueError("personal watched state must be boolean")
    ratings = {key: film[key] for key in ("personal_enjoyment", "personal_artistic_merit")}
    for value in ratings.values():
        if value is not None and (type(value) is not int or not 1 <= value <= 10):
            raise ValueError("personal scores must be null or integers 1–10")
    if film["merit_status"] not in {"known", "unknown", "invalid", "conflict"}:
        raise ValueError("unknown artistic-merit review state")
    return {
        **ratings,
        "watched": film["watched"],
        "watched_dates": film["watched_dates"],
        "merit_status": film["merit_status"],
    }
