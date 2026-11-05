"""Build an installable YouTrack app ZIP inside the ignored POC cache."""

import shutil
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[3]
POC = ROOT / "docs/research/tracker-poc"
OUTPUT = ROOT / ".cache/tracker-poc/youtrack-app"


def main() -> None:
    widget = OUTPUT / "widgets/films"
    widget.mkdir(parents=True, exist_ok=True)
    shutil.copy2(POC / "youtrack-app/manifest.json", OUTPUT / "manifest.json")
    shutil.copy2(POC / "youtrack-app/widgets/films/index.html", widget / "index.html")
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
    archive = OUTPUT.parent / "youtrack-app.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as package:
        for path in (OUTPUT / "manifest.json", *sorted(widget.iterdir())):
            package.write(path, path.relative_to(OUTPUT))
    print(f"Built {archive}")


if __name__ == "__main__":
    main()
