"""Build a separate candidate YouTrack app without reading private configuration."""

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path(__file__).resolve().parent
OUTPUT = ROOT / ".cache/tracker-poc/youtrack-tmdb-live-isolated.zip"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as package:
        for name in ("manifest.json", "settings.json", "metadata.js"):
            entry = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            package.writestr(entry, (SOURCE / name).read_bytes())
    print(f"Archive: {OUTPUT}")
    print(f"SHA-256: {hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
