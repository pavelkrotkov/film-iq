"""Small opt-in CC0 research acquisition, never a TMDB truth source.

Usage: uv run python -m film_iq.identity.wikidata_sample OBSERVATIONS OUTPUT
No retries: any HTTP/API failure is recorded as incomplete, including 429.
"""

import http.client
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ENDPOINT = "https://www.wikidata.org/w/api.php"
POLICY = (
    "English wbsearchentities title query; 50 results/page; follow search-continue, "
    "maximum 10 pages then incomplete. All returned entities with nondeprecated P4947 "
    "become candidates, retaining every ID. Labels/aliases en/fr/mul plus P1476 titles. "
    "Join all P57 directors in returned order. Unique P577 year only, else unknown. "
    "One second between requests; no retries. Not TMDB search or full catalog recall."
)


def get(parameters: dict) -> tuple[str, dict]:
    time.sleep(1)
    url = ENDPOINT + "?" + urllib.parse.urlencode({"format": "json", **parameters})
    request = urllib.request.Request(
        url, headers={"User-Agent": "film-iq/0.1 (CC0 identity research)"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if "error" in result:
        raise ValueError(result["error"])
    return url, result


def entities(ids: list[str]) -> dict:
    """Batch public entity requests and reject missing results.

    Missing entities cannot safely be treated as films without a catalog ID.
    Fail the retrieval instead of silently excluding unavailable evidence.
    """
    result = {}
    for start in range(0, len(ids), 50):
        _, page = get(
            {
                "action": "wbgetentities",
                "ids": "|".join(ids[start : start + 50]),
                "props": "labels|aliases|claims|info",
                "languages": "en|fr|mul",
            }
        )
        result.update(page["entities"])
    if set(ids) != result.keys() or any("missing" in entity for entity in result.values()):
        raise ValueError("Incomplete entity response")
    return result


def values(entity: dict, prop: str) -> list:
    statements = entity.get("claims", {}).get(prop, [])
    return [
        s["mainsnak"]["datavalue"]["value"]
        for s in statements
        if "datavalue" in s["mainsnak"] and s["rank"] != "deprecated"
    ]


def search(title: str, retrieval: dict) -> list[str]:
    offset = 0
    for _ in range(10):
        url, result = get(
            {
                "action": "wbsearchentities",
                "search": title,
                "language": "en",
                "type": "item",
                "limit": 50,
                "continue": offset,
            }
        )
        retrieval["pages"].append({"url": url, "response": result})
        if "search-continue" not in result:
            retrieval["search_complete"] = True
            break
        offset = result["search-continue"]
    return list(
        dict.fromkeys(
            item["id"] for page in retrieval["pages"] for item in page["response"]["search"]
        )
    )


def titles(entity: dict) -> list[str]:
    """Preserve supplied title forms; never insert the observed title as an alias."""
    result = [v["value"] for v in entity.get("labels", {}).values()]
    result += [v["value"] for group in entity.get("aliases", {}).values() for v in group]
    result += [v["text"] for v in values(entity, "P1476")]
    return list(dict.fromkeys(result))


def metadata(entity: dict, people: dict) -> dict:
    """Multiple release years remain unknown; no choice of a convenient date.

    The current resolver takes a single director string. Joining every supplied
    credit preserves the names but does not make source spellings agree.
    """
    credits = [
        people[v["id"]].get("labels", {}).get("en", {}).get("value") for v in values(entity, "P57")
    ]
    years = set(int(v["time"][1:5]) for v in values(entity, "P577") if v["time"].startswith("+"))
    imdb = values(entity, "P345")
    return {
        "titles": titles(entity),
        "director": ", ".join(credits) if credits and all(credits) else None,
        "year": next(iter(years)) if len(years) == 1 else None,
        "imdb_id": imdb[0] if len(imdb) == 1 else None,
    }


def candidates(movies: dict, people: dict) -> list[dict]:
    """Every returned nondeprecated P4947 statement becomes an unverified lead."""
    return [
        {"tmdb_id": int(identifier), **metadata(entity, people)}
        for entity in movies.values()
        for identifier in values(entity, "P4947")
    ]


def director_ids(movies: dict) -> list[str]:
    return list(dict.fromkeys(v["id"] for entity in movies.values() for v in values(entity, "P57")))


def collect(title: str, retrieval: dict) -> list[dict]:
    """Retain search pages, exclusions and exact entity revisions for inspection.

    No primary-source truth participates in candidate selection. Non-film search
    results are excluded only because they lack a TMDB movie-ID statement.
    """
    ids = search(title, retrieval)
    retrieval["returned_entities"] = ids
    found = entities(ids)
    movies = {key: entity for key, entity in found.items() if values(entity, "P4947")}
    retrieval["excluded_without_P4947"] = [key for key in ids if key not in movies]
    retrieval["excluded_evidence"] = {
        key: {
            "revision": found[key]["lastrevid"],
            "claims": {"P4947": found[key].get("claims", {}).get("P4947", [])},
        }
        for key in retrieval["excluded_without_P4947"]
    }
    people = entities(director_ids(movies))
    retrieval["candidate_evidence"] = {key: project(entity) for key, entity in movies.items()}
    retrieval["director_evidence"] = {key: project(entity) for key, entity in people.items()}
    return candidates(movies, people)


def acquire(case: dict) -> dict:
    """Keep attempted cases even when transport fails before JSON is available.

    Partial data never establishes absence; a failed retrieval keeps truth unknown.
    """
    retrieval = {
        "provider": "Wikidata CC0 leads, not TMDB search",
        "complete": False,
        "search_complete": False,
        "observed_at": datetime.now(UTC).isoformat(),
        "pages": [],
    }
    record = {
        "id": case["id"],
        "retrieval": retrieval,
        "candidates": [],
        "truth": {
            "tmdb_id": None,
            "status": "unknown",
            "reviewer": None,
            "evidence": [case["source"]["url"]],
            "reason": "Primary source supports work metadata; Wikidata P4947 has no independent TMDB mapping audit.",
        },
    }
    try:
        record["candidates"] = collect(case["observation"]["title"], retrieval)
        retrieval["complete"] = retrieval["search_complete"]
    except (
        urllib.error.URLError,
        http.client.HTTPException,
        TimeoutError,
        ValueError,
        KeyError,
    ) as error:
        retrieval["error"] = f"{type(error).__name__}: {error}"
    return record


def project(entity: dict) -> dict:
    return {
        "revision": entity["lastrevid"],
        "labels": entity.get("labels", {}),
        "aliases": entity.get("aliases", {}),
        "claims": {
            prop: entity.get("claims", {}).get(prop, [])
            for prop in ("P4947", "P57", "P577", "P345", "P1476")
        },
    }


def main() -> None:
    source, destination = map(Path, sys.argv[1:])
    sample = json.loads(source.read_text())
    snapshot = {
        "version": sample["version"],
        "rights": "Wikidata structured data CC0; https://www.wikidata.org/wiki/Wikidata:Licensing. No TMDB response or source-page copy.",
        "policy": POLICY,
        "cases": [],
    }
    for case in sample["cases"]:
        record = acquire(case)
        snapshot["cases"].append(record)
        destination.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
        print(case["id"], len(record["candidates"]), record["retrieval"]["complete"], flush=True)


if __name__ == "__main__":
    main()
