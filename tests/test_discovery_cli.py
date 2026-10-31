"""First-use commands share the film-iq entry point without live I/O."""

import json

from discovery_fixtures import cohort

from film_iq.cli import main


def test_discover_cli_shows_pending_without_creating_database(tmp_path, capsys):
    path = tmp_path / "cohort.json"
    path.write_text(json.dumps(cohort()))
    assert main(["discover", "--cohort", str(path), "--format", "json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert (report["accepted"], report["suggested_unwatched"]) == (0, [])
    assert sorted(p.name for p in tmp_path.iterdir()) == ["cohort.json"]
