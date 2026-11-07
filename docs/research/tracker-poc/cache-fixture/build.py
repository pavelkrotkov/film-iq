"""Build isolated fixture variants of the existing tracker UIs."""

import argparse
import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fictional_cache import seed

POC = Path(__file__).resolve().parents[1]
ROOT = POC.parents[2]
LOCAL = ROOT / ".cache/tracker-poc"
UI = POC / "ui"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", required=True, help="ID of a dedicated fictional Kaneo project"
    )
    project = parser.parse_args().project
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", project):
        raise ValueError("Invalid fictional project ID")
    cache = LOCAL / "fictional-cache"
    if not cache.exists():
        seed(cache, datetime.now(UTC))
        # These files contain only the two public fictional fixture records.
        cache.chmod(0o755)
        (cache / "cache").chmod(0o755)
        for path in (cache / "authority.json", *list((cache / "cache").iterdir())):
            path.chmod(0o644)
    target = UI / "dist/cache-fixture"
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(UI / "node_modules/.bin/esbuild"),
            "src.jsx",
            "--bundle",
            "--minify",
            f"--outfile={target / 'app.js'}",
            "--loader:.js=jsx",
            "--define:__FILMIQ_CACHE_FIXTURE__=true",
            f"--define:__FILMIQ_FIXTURE_PROJECT__={json.dumps(project)}",
        ],
        cwd=UI,
        check=True,
    )
    (target / "index.html").write_text(
        '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fictional cache fixture</title><link rel="stylesheet" href="../../style.css"></head><body><div id="root"></div><script src="app.js" defer></script></body></html>'
    )
    out = LOCAL / "youtrack-cache-fixture-app"
    widget = out / "widgets/films"
    widget.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((POC / "youtrack-app/manifest.json").read_text())
    manifest.update(
        name="filmiq-cache-fixture-ui",
        title="FilmIQ fictional cache fixture",
        description="Offline fictional records only.",
    )
    manifest["widgets"][0]["name"] = "FilmIQ fictional cache fixture"
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    for name in ("index.html", "youtrack.css"):
        shutil.copy2(POC / "youtrack-app/widgets/films" / name, widget / name)
    shutil.copy2(UI / "style.css", widget / "style.css")
    subprocess.run(
        [
            str(UI / "node_modules/.bin/esbuild"),
            "youtrack.jsx",
            "--bundle",
            "--minify",
            "--format=esm",
            f"--outfile={widget / 'app.js'}",
            "--define:__FILMIQ_CACHE_FIXTURE__=true",
        ],
        cwd=UI,
        check=True,
    )
    archive = LOCAL / "youtrack-cache-fixture-app.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as package:
        for path in (out / "manifest.json", *sorted(widget.iterdir())):
            package.write(path, path.relative_to(out))
    print("Fixture cache and two UI builds ready; no tracker or provider was contacted.")
    print(f"Kaneo project: {project}; package: {archive}")


if __name__ == "__main__":
    main()
