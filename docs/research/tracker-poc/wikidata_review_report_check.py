"""Offline fictional check for the private Wikidata evidence renderer."""

from copy import deepcopy
from typing import Any

from wikidata_review_report import build, link, snak_value


def main() -> None:
    date = {
        "snaktype": "value",
        "datavalue": {
            "type": "time",
            "value": {
                "time": "+2000-01-01T00:00:00Z",
                "precision": 11,
                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                "timezone": 0,
                "before": 0,
                "after": 0,
            },
        },
    }
    item = {
        "snaktype": "value",
        "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q42"}},
    }
    claim = {
        "mainsnak": date,
        "rank": "normal",
        "qualifiers": {"P291": [item]},
        "references": [{"snaks": {"P248": [item]}}],
    }
    preview = "\n".join(f"| Fictional film | {100 + i} |" for i in range(8))
    films = [{"title": f"Fictional [{i}]", "tmdb_id": 100 + i} for i in range(8)]
    entities = {
        f"Q{i + 1}": {
            "crosswalk_tmdb_id": str(100 + i),
            "lastrevid": i + 1000,
            "claims": {
                "P577": [claim, {**claim, "rank": "deprecated"}],
                "P57": [{"rank": "normal", "mainsnak": item}],
            },
        }
        for i in range(8)
    }
    source: dict[str, Any] = {
        "source": "Wikidata wbgetentities",
        "license": "CC0",
        "endpoint": "https://www.wikidata.org/w/api.php",
        "retrieved_at": "2026-11-06T00:00:00+00:00",
        "entities": entities,
    }
    report, counts = build(preview, source, {"films": films})
    assert counts == {"films": 8, "date_claims": 8, "director_claims": 8, "genre_claims": 0}
    assert "unverified leads" in report and "canonical release year" in report
    assert "Fictional \\[0\\]" in report
    assert "precision 11" in report and "before 0; after 0" in report
    assert "Qualifiers:" in report and "Reference:" in report
    assert "https://www.wikidata.org/wiki/Q42" in report
    assert "Unknown (genre item claims missing or malformed)" in report
    assert "invalid link" in link("javascript:alert(1)", "fake")
    assert "Unknown" in snak_value({"snaktype": "somevalue"})
    broken = deepcopy(source)
    broken["entities"]["Q1"]["crosswalk_tmdb_id"] = "999999"
    try:
        build(preview, broken, {"films": films})
    except ValueError:
        pass
    else:
        raise AssertionError("Out-of-scope identity was accepted")
    print("Fictional private review rendering, context, unknowns and scope checks passed")


if __name__ == "__main__":
    main()
