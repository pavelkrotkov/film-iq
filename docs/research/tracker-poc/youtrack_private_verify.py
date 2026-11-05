"""Read back local real-film IDs and source evidence without printing them."""

import json

from youtrack_client import YouTrackClient, YouTrackError
from youtrack_enrich import custom_value
from youtrack_private_import import SOURCE, validate


def main() -> None:
    films = validate(SOURCE)
    expected = {film["tmdb_id"]: film for film in films}
    client = YouTrackClient()
    issues = client.pages(
        "issues",
        query={
            "fields": "id,idReadable,customFields(name,value(name,text))",
            "query": "project: {FILMREAL} sort by: {issue id} asc",
        },
    )
    found = {}
    for issue in issues:
        identity = custom_value(issue, "FilmIQ TMDB ID")
        if type(identity) is not int or identity in found:
            raise YouTrackError("Film ID missing, invalid, or duplicated")
        found[identity] = issue
    if set(found) != set(expected):
        raise YouTrackError("YouTrack film IDs differ from the private input")
    with_links = 0
    for identity, film in expected.items():
        issue = found[identity]
        if custom_value(issue, "FilmIQ Source Year") != film.get("source_year"):
            raise YouTrackError("A source-listed year did not survive import")
        if custom_value(issue, "FilmIQ Release Year") is not None:
            raise YouTrackError("A source-listed year was treated as canonical")
        evidence = film.get("accepted_discovery_evidence") or {}
        stored = custom_value(issue, "FilmIQ Source Evidence")
        if evidence.get("links"):
            if not isinstance(stored, dict) or json.loads(stored.get("text", "")) != evidence:
                raise YouTrackError("Source evidence did not survive import")
            with_links += 1
        elif stored is not None:
            raise YouTrackError("Unexpected source evidence on an unlinked film")
    print(
        f"Verified {len(found)} unique YouTrack films; {with_links} have accepted source evidence"
    )


if __name__ == "__main__":
    main()
