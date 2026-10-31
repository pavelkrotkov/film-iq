"""Catalog status uses the existing bounded-expiry validator."""

import json
from datetime import timedelta

from display_fixtures import NOW, catalog_path

from film_iq.cli import main


def test_expired_catalog_is_not_current(tmp_path, capsys):
    path = catalog_path(tmp_path)
    assert (
        main(
            [
                "status",
                "--catalog",
                str(path),
                "--now",
                (NOW + timedelta(days=6)).isoformat(),
                "--format",
                "json",
            ]
        )
        == 1
    )
    result = json.loads(capsys.readouterr().out)
    assert result["catalog"]["state"] == "expired"
    assert "records" not in result["catalog"] and "attribution" not in result["catalog"]
