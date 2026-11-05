"""Offline fictional regression check for seeder lifecycle behavior."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, TypedDict
from unittest.mock import patch

import kaneo_seed


class Fixture(TypedDict):
    status: str
    fields: dict[str, str]


def main() -> None:
    existing = {
        "fixture-0001": {"status": "to-do"},
        "fixture-0003": {"status": "done"},
    }
    tasks: dict[str, Fixture] = {}
    for identity, item in existing.items():
        tasks[identity] = {
            "status": item["status"],
            "fields": {
                "POC Fixture ID": identity,
            },
        }
    writes = []

    def fake_call(_opener, _base, path, payload: dict[str, Any] | None = None, method=None):
        if path == "/custom-field/project/fictional-project/values":
            return [
                {"taskId": task, "fieldId": field, "value": value}
                for task, data in tasks.items()
                for field, value in data["fields"].items()
            ]
        if path == "/task/fictional-project" and method is None:
            assert payload is not None
            fields = {field["fieldId"]: field["value"] for field in payload["customFields"]}
            identity = fields["POC Fixture ID"]
            assert identity not in tasks
            tasks[identity] = {"status": payload["status"], "fields": fields}
            writes.append(("create", identity))
            return {"id": identity}
        raise AssertionError(f"Unexpected API mutation or route: {path}")

    with (
        patch.object(kaneo_seed.http.cookiejar, "MozillaCookieJar") as cookies,
        patch.object(kaneo_seed.urllib.request, "build_opener", return_value=object()),
        patch.object(kaneo_seed, "ensure_field", side_effect=lambda _o, _b, _p, name, *_: name),
        patch.object(kaneo_seed, "call", side_effect=fake_call),
        redirect_stdout(StringIO()),
    ):
        cookies.return_value.load.return_value = None
        kaneo_seed.seed("http://fixture.invalid", "fictional-project", Path("fictional-cookie"), 8)
        assert tasks["fixture-0007"]["status"] == "archived"
        assert tasks["fixture-0003"]["status"] == "done"
        assert tasks["fixture-0001"]["status"] == "to-do"
        first_writes = list(writes)
        kaneo_seed.seed("http://fixture.invalid", "fictional-project", Path("fictional-cookie"), 8)
        assert writes == first_writes
        assert tasks["fixture-0007"]["status"] == "archived"
        assert tasks["fixture-0003"]["status"] == "done"
        assert tasks["fixture-0001"]["status"] == "to-do"
    print("Fictional new archived fixture and unchanged legacy/manual states passed repeat seed")


if __name__ == "__main__":
    main()
