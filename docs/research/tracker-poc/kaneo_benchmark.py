"""Measure a complete local Kaneo board traversal and project field read."""

import argparse
import http.cookiejar
import time
import urllib.request
from pathlib import Path

from kaneo_smoke import call


def benchmark(base: str, project: str, cookie_file: Path):
    cookies = http.cookiejar.MozillaCookieJar(str(cookie_file))
    cookies.load(ignore_discard=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
    tasks = []
    page, pages, total, requests = 1, 1, None, 0
    started = time.monotonic()
    while page <= pages:
        path = f"/task/tasks/{project}?limit=100&page={page}"
        result = call(opener, base, path)
        requests += 1
        pagination = result["pagination"]
        pages = pagination["totalPages"]
        if total is not None and total != pagination["total"]:
            raise ValueError("board changed during measurement")
        total = pagination["total"]
        board = result["data"]
        tasks.extend(task["id"] for column in board["columns"] for task in column["tasks"])
        tasks.extend(task["id"] for task in board["archivedTasks"] + board["plannedTasks"])
        for related in range(2, pagination["relatedTotalPages"] + 1):
            call(opener, base, f"{path}&relatedPage={related}")
            requests += 1
        page += 1
    board_seconds = time.monotonic() - started
    if len(tasks) != total or len(set(tasks)) != total:
        raise ValueError("board traversal did not return every task exactly once")
    started = time.monotonic()
    values = call(opener, base, f"/custom-field/project/{project}/values")
    values_seconds = time.monotonic() - started
    print(
        f"{len(tasks)} tasks, {requests} board requests in {board_seconds:.3f}s; "
        f"{len(values)} field values in {values_seconds:.3f}s"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:15173")
    parser.add_argument("--project", required=True)
    parser.add_argument("--cookie-file", required=True, type=Path)
    args = parser.parse_args()
    benchmark(args.base.rstrip("/"), args.project, args.cookie_file)
