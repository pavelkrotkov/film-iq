"""Build an installable YouTrack app ZIP inside the ignored POC cache."""

import argparse
import shutil
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[3]
POC = ROOT / "docs/research/tracker-poc"
OUTPUT = ROOT / ".cache/tracker-poc/youtrack-app"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate",
        action="store_true",
        help="build a separate candidate without replacing the existing approval ZIP",
    )
    args = parser.parse_args()
    output = OUTPUT.with_name("youtrack-app-candidate") if args.candidate else OUTPUT
    widget = output / "widgets/films"
    widget.mkdir(parents=True, exist_ok=True)
    app = POC / "youtrack-app"
    app_files = (
        "manifest.json",
        "entity-extensions.json",
        "preferences.js",
        "movary.js",
        "poc_lifecycle_guard.js",
        "poc_scheduled_marker.js",
    )
    for name in app_files:
        shutil.copy2(app / name, output / name)
    shutil.copy2(POC / "youtrack-app/widgets/films/index.html", widget / "index.html")
    shutil.copy2(POC / "youtrack-app/widgets/films/youtrack.css", widget / "youtrack.css")
    shutil.copy2(POC / "ui/style.css", widget / "style.css")
    subprocess.run(
        [
            str(POC / "ui/node_modules/.bin/esbuild"),
            "youtrack.jsx",
            "--bundle",
            "--minify",
            "--format=esm",
            f"--outfile={widget / 'app.js'}",
        ],
        cwd=POC / "ui",
        check=True,
    )
    archive = output.parent / (
        "youtrack-app-candidate.zip" if args.candidate else "youtrack-app.zip"
    )
    with ZipFile(archive, "w", ZIP_DEFLATED) as package:
        for path in (*(output / name for name in app_files), *sorted(widget.iterdir())):
            package.write(path, path.relative_to(output))
    print(f"Built {archive}")


if __name__ == "__main__":
    main()
