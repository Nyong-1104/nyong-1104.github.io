# -*- coding: utf-8 -*-
"""Apply explicit BWR whitelist to catalog/packs and rebuild data.js."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
KST = timezone(timedelta(hours=9))

sys.path.insert(0, str(SCRIPTS))
from brg_pop import restore_brg_pops  # noqa: E402
from bwr_cards import ensure_bwr_cards  # noqa: E402
from ebay_prices import live_source_label, restore_ebay_prices  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402
from pokepop_snapshot import (  # noqa: E402
    assign_tiers_to_catalog,
    build_live_snapshot,
    write_data_bundle,
)


def main() -> int:
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    catalog = ensure_bwr_cards(catalog, packs)
    tiers = assign_tiers_to_catalog(catalog)

    asof = datetime.now(KST).isoformat(timespec="seconds")
    previous = {}
    live_path = DATA / "live" / "pop-price.json"
    if live_path.exists():
        previous = json.loads(live_path.read_text(encoding="utf-8"))

    live, stats = build_live_snapshot(catalog, packs, asof, previous)
    stats["tiers"] = tiers
    stats["brgPopsRestored"] = restore_brg_pops(live, previous)
    stats["ebayPricesRestored"] = restore_ebay_prices(live, previous)
    stats["gemratePsaRestored"] = restore_psa_pops(live, previous)
    live["source"] = live_source_label(live)
    if stats["brgPopsRestored"] and "BRG" not in str(live.get("source")):
        live["source"] = "seed+BRG" if live["source"] == "seed" else f"{live['source']}+BRG"
    if stats["gemratePsaRestored"] and "gemrate" not in str(live.get("source")).lower():
        live["source"] = f"{live['source']}+gemrate"
    live["generatedAt"] = asof
    last_run = {"ranAt": asof, "stats": stats}
    (DATA / "live" / "last-run.json").write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_data_bundle(DATA, packs, catalog, live, last_run)

    bwr = [c for c in catalog if c.get("rarity") == "BWR"]
    print(json.dumps({"tiers": tiers, "bwr": [(c["id"], c["nameKo"], c["number"]) for c in bwr]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
