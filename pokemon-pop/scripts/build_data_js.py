# -*- coding: utf-8 -*-
"""Bundle packs.json, catalog.json, and live/pop-price.json into data.js."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
from pokepop_snapshot import write_data_bundle  # noqa: E402


def main():
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    live = json.loads((DATA / "live" / "pop-price.json").read_text(encoding="utf-8"))
    write_data_bundle(DATA, packs, catalog, live)
    print("data.js rebuilt")


if __name__ == "__main__":
    main()
