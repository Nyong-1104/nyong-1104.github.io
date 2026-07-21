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
from pokepop_snapshot import build_live_snapshot, write_data_bundle  # noqa: E402

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
    live, stats = build_live_snapshot(catalog, packs, asof)
    (DATA / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DATA / "live" / "pop-price.json").write_text(
        json.dumps(live, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
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
