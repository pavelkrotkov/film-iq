"""Exercise neutral bearer import against fictional in-memory Kaneo responses."""

from copy import deepcopy
from typing import Any
from urllib.parse import parse_qs, urlsplit

from kaneo_watchlist_films import FIELD_NAMES, apply, neutral_body, plan
from movary_watchlist_projection import project
from youtrack_watchlist_films_check import observation


class Fake:
    def __init__(self, snapshot, status):
        projection = project(snapshot, status, [])
        self.sidecar: dict[str, Any] = {
            "version": "tracker-poc-movary-watchlist-users-v1",
            "project_id": "project1",
            "users": {
                "owner": {
                    key: projection[key] for key in ("version", "source", "observed_at", "entries")
                }
            },
        }
        self.fields = [
            {"id": f"field{i}", "name": name, "type": "text"} for i, name in enumerate(FIELD_NAMES)
        ]
        self.tasks = [
            {
                "id": f"task{i}",
                "projectId": "project1",
                "title": f"Unrelated fictional {i}",
                "status": "archived" if i == 101 else "to-do",
                "description": "Existing user edit",
            }
            for i in range(102)
        ]
        self.values = [{"taskId": "task0", "fieldId": "field0", "value": "102"}]
        self.posts = []
        self.lost = False
        self.change_after_first = False
        self.bad_page = False

    def request(self, path, payload=None):
        if path == "/user/me":
            return {"id": "owner"}
        if path == "/custom-field/project/project1":
            return deepcopy(self.fields)
        if path == "/custom-field/project/project1/values":
            return deepcopy(self.values)
        if path.startswith("/task/tasks/project1?"):
            page = int(parse_qs(urlsplit(path).query)["page"][0])
            total = len(self.tasks)
            if self.bad_page and page == 2:
                total += 1
            rows = self.tasks[(page - 1) * 100 : page * 100]
            return {
                "pagination": {"total": total, "totalPages": (total + 99) // 100},
                "data": {
                    "columns": [
                        {"tasks": deepcopy([r for r in rows if r["status"] != "archived"])}
                    ],
                    "archivedTasks": deepcopy([r for r in rows if r["status"] == "archived"]),
                    "plannedTasks": [],
                },
            }
        if path == "/task/project1":
            assert payload is not None
            assert all(
                term not in str(payload).lower()
                for term in ("movary", "watched", "watchlist", "personal")
            )
            ident = f"created{len(self.posts)}"
            self.posts.append(deepcopy(payload))
            self.tasks.append({"id": ident, "projectId": "project1", **deepcopy(payload)})
            self.values += [{"taskId": ident, **field} for field in payload["customFields"]]
            if self.change_after_first:
                self.sidecar["users"]["owner"]["observed_at"] = "2026-11-07T00:00:00+00:00"
            if self.lost:
                raise OSError("fictional lost response after creation")
            return {"id": ident}
        if path.startswith("/custom-field/task/"):
            return deepcopy([row for row in self.values if row["taskId"] == path.rsplit("/", 1)[1]])
        if path.startswith("/task/"):
            return deepcopy(next(row for row in self.tasks if row["id"] == path.rsplit("/", 1)[1]))
        raise AssertionError("Unexpected fictional request")


def rejects(fn):
    try:
        fn()
    except (ValueError, RuntimeError):
        return
    raise AssertionError("Expected refusal")


def main():
    snapshot, status = observation()
    fake = Fake(snapshot, status)

    def load(target=fake):
        return plan(
            target.request, "project1", target.sidecar, snapshot, status, {17, 102}, "a", "b"
        )

    preview = load()
    assert len(preview["pending"]) == 2 and not fake.posts
    assert "watchlist" not in str(neutral_body(preview["pending"][0], preview["fields"])).lower()
    changed = deepcopy(preview)
    changed["snapshot_sha256"] = "changed"
    rejects(lambda: apply(fake.request, changed, load))
    assert not fake.posts
    assert apply(fake.request, preview, load) == {"status": "applied", "created": 2}
    repeat = load()
    assert repeat["existing"] == 2 and repeat["pending"] == []
    assert apply(fake.request, repeat, load)["created"] == 0
    assert all(row["description"] == "Existing user edit" for row in fake.tasks[:102])

    collision = Fake(snapshot, status)
    collision.tasks[-1]["title"] = " FICTIONAL   film "
    planned = load(collision)
    assert planned["conflicts"] == 1
    rejects(lambda: apply(collision.request, planned, lambda: load(collision)))
    assert not collision.posts, "archived collision must block writes"

    denied = Fake(snapshot, status)
    assert (
        plan(denied.request, "project1", denied.sidecar, snapshot, status, {101}, "a", "b")[
            "conflicts"
        ]
        == 1
    )
    denied.sidecar["users"] = {"someone-else": next(iter(denied.sidecar["users"].values()))}
    rejects(lambda: load(denied))
    denied = Fake(snapshot, status)
    denied.bad_page = True
    rejects(lambda: load(denied))
    denied = Fake(snapshot, status)
    denied.values.append(deepcopy(denied.values[0]))
    rejects(lambda: load(denied))

    midrun = Fake(snapshot, status)
    planned = load(midrun)
    midrun.change_after_first = True
    rejects(lambda: apply(midrun.request, planned, lambda: load(midrun)))
    assert len(midrun.posts) == 1
    lost = Fake(snapshot, status)
    planned = load(lost)
    lost.lost = True
    rejects(lambda: apply(lost.request, planned, lambda: load(lost)))
    assert len(lost.posts) == 1 and len(load(lost)["pending"]) == 1
    print(
        "Fictional paginated Kaneo preview, owner, collisions, idempotence and uncertain write passed"
    )


if __name__ == "__main__":
    main()
