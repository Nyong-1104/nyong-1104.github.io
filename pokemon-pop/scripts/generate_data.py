# -*- coding: utf-8 -*-
"""Rebuild live snapshot + data.js from existing packs.json and catalog.json."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
KST = timezone(timedelta(hours=9))

sys.path.insert(0, str(SCRIPTS))
from pokepop_snapshot import build_live_snapshot, write_data_bundle  # noqa: E402


def main() -> int:
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    asof = datetime.now(KST).isoformat(timespec="seconds")
    live, stats = build_live_snapshot(catalog, packs, asof)
    write_data_bundle(DATA, packs, catalog, live)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
