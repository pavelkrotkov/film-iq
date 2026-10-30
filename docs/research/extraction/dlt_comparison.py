"""Run an optional fictional-data SQLite versus dlt experiment."""

import os
import tempfile
from collections.abc import Iterable, Iterator
from importlib import import_module
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from docs.research.extraction.comparison_data import (
    CORRECTED,
    INITIAL,
    broken_rows,
    run_sqlite,
    snapshot,
)


def records(rows: Iterable[tuple[str, str]]) -> Iterator[dict[str, str]]:
    for identifier, title in rows:
        yield {"id": identifier, "title": title}


def make_pipeline(root: Path):
    dlt = import_module("dlt")
    # dlt 1.31 probes HOME for global settings; keep this experiment in the worktree.
    import_module("dlt.common.runtime.run_context").global_dir = lambda: str(root / "global")  # ty: ignore[unresolved-attribute]
    path = root / "dlt.sqlite3"
    return dlt.pipeline(
        pipeline_name="film_iq_b3",
        pipelines_dir=str(root / "pipelines"),
        dataset_name="main",
        destination=dlt.destinations.sqlalchemy(credentials=f"sqlite:///{path}"),
    )


def run_dlt(root: Path, initial=INITIAL, corrected=CORRECTED) -> None:
    path = root / "dlt.sqlite3"
    started = perf_counter()
    pipeline = make_pipeline(root)
    options = {"table_name": "observation", "write_disposition": "merge", "primary_key": "id"}
    pipeline.run(list(records(initial)), **options)
    pipeline = make_pipeline(root)
    pipeline.run(list(records(initial)), **options)
    assert snapshot(path) == sorted(initial)
    try:
        pipeline.run(records(broken_rows(corrected)), **options)
    except import_module("dlt.pipeline.exceptions").PipelineStepFailed as error:
        if "injected source failure" not in str(error):
            raise
    else:
        raise AssertionError("dlt did not report the injected source failure")
    assert snapshot(path) == sorted(initial)
    pipeline = make_pipeline(root)
    pipeline.run(list(records(corrected)), **options)
    assert snapshot(path) == sorted(corrected)
    print("dlt", "seconds", round(perf_counter() - started, 3))


def prepare(root: Path) -> None:
    for directory in ("tmp", "data", "project", "local", "cache"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    os.environ.update(
        TMPDIR=str(root / "tmp"),
        XDG_CACHE_HOME=str(root / "cache"),
        XDG_DATA_HOME=str(root / "data"),
        DLT_DATA_DIR=str(root / "data"),
        DLT_PROJECT_DIR=str(root / "project"),
        DLT_LOCAL_DIR=str(root / "local"),
        RUNTIME__DLTHUB_TELEMETRY="false",
    )
    tempfile.tempdir = str(root / "tmp")


def main() -> None:
    root = Path(__file__).resolve().parents[3] / ".cache" / "dlt-comparison" / uuid4().hex
    prepare(root)
    run_sqlite(root)
    run_dlt(root)


if __name__ == "__main__":
    main()
