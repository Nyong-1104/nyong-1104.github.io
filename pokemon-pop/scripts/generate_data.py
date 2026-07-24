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
from ebay_prices import restore_ebay_prices  # noqa: E402
from brg_pop import restore_brg_pops  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402
from pokepop_snapshot import (  # noqa: E402
    build_live_snapshot,
    load_previous_live,
    write_data_bundle,
)


def main() -> int:
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    asof = datetime.now(KST).isoformat(timespec="seconds")
    previous = load_previous_live(DATA)
    live, stats = build_live_snapshot(catalog, packs, asof, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or live.get("source") or "seed"
    live["generatedAt"] = asof
    write_data_bundle(DATA, packs, catalog, live)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
