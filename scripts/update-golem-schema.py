#!/usr/bin/env python3
"""Dev-only: (re-)vendor the frozen GOLEM ontology and its provenance.

Fetches a single pinned blob from the upstream repository and writes the three
resource files the runtime ships (``golem.ttl``, ``version.json``, ``VERSION``).
The runtime itself never reaches the network (research D9); this generator is
the only thing that does, and only when a maintainer chooses to re-pin.

Usage:
    uv run python scripts/update-golem-schema.py
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

REPOSITORY = "https://github.com/GOLEM-lab/golem-ontology"
COMMIT = "f666128a9a29f39c9f23c96ae1c48023cc8e7898"
FILE = "golem/golem_v1-1.ttl"
VERSION_IRI = "https://w3id.org/golem/ontology/v1.1"
VERSION_INFO = "1.1"
VERSION_LABEL = "golem-1.1"
RETRIEVED = "2026-05-30"

RAW_URL = f"https://raw.githubusercontent.com/GOLEM-lab/golem-ontology/{COMMIT}/{FILE}"

DEST = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "bookwright"
    / "resources"
    / "schemas"
    / VERSION_LABEL
)


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(RAW_URL) as response:
        ttl_bytes = response.read()
    (DEST / "golem.ttl").write_bytes(ttl_bytes)

    provenance = {
        "repository": REPOSITORY,
        "commit": COMMIT,
        "file": FILE,
        "version_iri": VERSION_IRI,
        "version_info": VERSION_INFO,
        "retrieved": RETRIEVED,
    }
    (DEST / "version.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    (DEST / "VERSION").write_text(VERSION_LABEL + "\n", encoding="utf-8")

    print(f"Vendored {len(ttl_bytes)} bytes of {FILE} @ {COMMIT[:12]} into {DEST}")


if __name__ == "__main__":
    main()
