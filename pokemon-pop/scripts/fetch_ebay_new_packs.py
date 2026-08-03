# -*- coding: utf-8 -*-
"""Fetch eBay prices only for recently uploaded packs (missing slots only)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
sys.path.insert(0, str(SCRIPTS))

from brg_pop import restore_brg_pops  # noqa: E402
from bwr_cards import ensure_bwr_cards  # noqa: E402
from ebay_prices import (  # noqa: E402
    fetch_ebay_batch,
    has_credentials,
    live_source_label,
    restore_ebay_prices,
)
from fetch_live import load_dotenv  # noqa: E402
from gemrate_pop import mark_live_source, restore_psa_pops  # noqa: E402
from pokepop_snapshot import (  # noqa: E402
    assign_tiers_to_catalog,
    build_live_snapshot,
    write_data_bundle,
)

KST = timezone(timedelta(hours=9))

# Packs added in the recent upload batch (boosters + promo/box).
NEW_PACKS = [
    "pokekyun",
    "s12a-vstar-universe",
    "sm12a-tag-all-stars",
    "s1a-vmax-rising",
    "sm5p-ultra-force",
    "25th-anniversary-golden-box",
    "munch-scream-promo",
    "mario-luigi-pikachu-box",
    "rokon-crystal-season-box",
    "rayquaza-poncho-pikachu-box",
    "magikarp-gyarados-pretend-pikachu-box",
    "mega-charizard-y-poncho-pikachu-box",
    "team-pretend-pikachu-box",
    "pokemon-center-hiroshima-box",
    "pokemon-center-fukuoka-box",
    "pokemon-center-tohoku-box",
    "japan-post-stamp-box",
    "yu-nagaba-eevee-promo",
    "s8a-p-25th-anniversary",
    "victini-bwr-promo",
    "mg-festa-seoul-stamp",
]


def miss_count(live: dict, packs: list[dict], catalog: list[dict], pack_id: str) -> int:
    pack = next(p for p in packs if p["id"] == pack_id)
    langs = pack.get("languages") or ["jp"]
    n = 0
    for card in catalog:
        if card.get("packId") != pack_id:
            continue
        for lang in langs:
            variant = (live.get("cards") or {}).get(card["id"], {}).get(lang) or {}
            price = variant.get("price") or {}
            if not (price.get("source") == "eBay" and price.get("grades")):
                n += 1
    return n


def main() -> int:
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT.parent / ".env")
    if not has_credentials():
        raise SystemExit("Set EBAY_CLIENT_ID / EBAY_CLIENT_SECRET")

    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    catalog = ensure_bwr_cards(catalog, packs)
    assign_tiers_to_catalog(catalog)

    asof = datetime.now(KST).isoformat(timespec="seconds")
    previous = json.loads((DATA / "live" / "pop-price.json").read_text(encoding="utf-8"))
    live, stats = build_live_snapshot(catalog, packs, asof, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)

    pack_ids = {p["id"] for p in packs}
    targets = []
    for pid in NEW_PACKS:
        if pid not in pack_ids:
            print(f"skip missing pack {pid}", flush=True)
            continue
        n = miss_count(live, packs, catalog, pid)
        if n:
            targets.append((n, pid))
    targets.sort(reverse=True)
    print(
        json.dumps(
            {"targets": [{"packId": pid, "miss": n} for n, pid in targets], "jobs": sum(n for n, _ in targets)},
            ensure_ascii=False,
        ),
        flush=True,
    )

    totals = {"ok": 0, "empty": 0, "failed": 0, "planned": 0}
    for i, (nmiss, pid) in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] {pid} miss={nmiss}", flush=True)
        st = fetch_ebay_batch(
            catalog,
            packs,
            live,
            asof,
            limit=20000,
            pack_id=pid,
            max_age_days=36500,  # missing/non-eBay only
            force=False,
            sleep_s=0.22,
        )
        totals["ok"] += int(st.get("jobsOk") or 0)
        totals["empty"] += int(st.get("jobsEmpty") or 0)
        totals["failed"] += int(st.get("jobsFailed") or 0)
        totals["planned"] += int(st.get("jobsPlanned") or 0)
        print(
            f"  -> planned={st.get('jobsPlanned')} ok={st.get('jobsOk')} "
            f"empty={st.get('jobsEmpty')} failed={st.get('jobsFailed')}",
            flush=True,
        )

        mark_live_source(live)
        src = live_source_label(live)
        if "BRG" not in src:
            src += "+BRG"
        if "PSA" not in src:
            src += "+PSA"
        live["source"] = src
        live["generatedAt"] = datetime.now(KST).isoformat(timespec="seconds")
        last = {
            "ranAt": live["generatedAt"],
            "stats": {
                **stats,
                "ebayNewPacks": {"totals": dict(totals), "lastPack": pid},
                "liveSource": src,
            },
        }
        write_data_bundle(DATA, packs, catalog, live, last)

    left = sum(
        miss_count(live, packs, catalog, pid)
        for pid in NEW_PACKS
        if pid in pack_ids
    )
    print(
        json.dumps(
            {"DONE": True, "totals": totals, "stillMissingInNewPacks": left},
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
