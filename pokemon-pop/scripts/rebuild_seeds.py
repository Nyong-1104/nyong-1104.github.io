# -*- coding: utf-8 -*-
"""Recompute catalog seeds + live POP/price snapshot from seed_for rules."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_catalog import seed_for  # noqa: E402
from ebay_prices import restore_ebay_prices  # noqa: E402
from brg_pop import restore_brg_pops  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402
from pokepop_snapshot import (  # noqa: E402
    build_live_snapshot,
    load_previous_live,
    write_data_bundle,
)

KST = timezone(timedelta(hours=9))


def main() -> int:
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    changed = 0
    for card in catalog:
        new_seed = seed_for(card.get("rarity") or "C", card.get("nameEn") or "", card.get("nameJa") or "")
        if card.get("seed") != new_seed:
            card["seed"] = new_seed
            changed += 1

    asof = datetime.now(KST).isoformat(timespec="seconds")
    previous = load_previous_live(DATA)
    live, stats = build_live_snapshot(catalog, packs, asof, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or live.get("source") or "seed"
    live["generatedAt"] = asof
    write_data_bundle(DATA, packs, catalog, live)
    sample = next((c for c in catalog if "V-UNION" in (c.get("nameEn") or "")), None)
    print(
        json.dumps(
            {"seedsUpdated": changed, **stats, "vunionSeed": sample.get("seed") if sample else None},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
