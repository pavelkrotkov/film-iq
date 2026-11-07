"""Check the YouTrack app archive includes the watchlist handler."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import build_youtrack


def build_widget(args, **_kwargs):
    output = next(arg.removeprefix("--outfile=") for arg in args if arg.startswith("--outfile="))
    Path(output).write_text("fictional widget")


def main():
    cache = build_youtrack.ROOT / ".cache/tracker-poc"
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fictional-youtrack-build-", dir=cache) as folder:
        output = Path(folder) / "app"
        with (
            patch.object(build_youtrack, "OUTPUT", output),
            patch.object(build_youtrack.subprocess, "run", side_effect=build_widget),
            patch.object(sys, "argv", ["build_youtrack.py"]),
        ):
            build_youtrack.main()
        with ZipFile(output.with_suffix(".zip")) as package:
            assert (
                package.read("movary-watchlist.js")
                == (build_youtrack.POC / "youtrack-app/movary-watchlist.js").read_bytes()
            )
            assert package.read("widgets/films/app.js") == b"fictional widget"
    print("YouTrack build packages the watchlist handler and widget")


if __name__ == "__main__":
    main()
