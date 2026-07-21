# -*- coding: utf-8 -*-
"""Add/refresh MG Festa Seoul Stamp Rally pack with Magikarp only."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from brg_pop import fetch_brg_for_packs, restore_brg_pops  # noqa: E402
from ebay_prices import restore_ebay_prices  # noqa: E402
from pokepop_snapshot import build_live_snapshot, write_data_bundle  # noqa: E402

KST = timezone(timedelta(hours=9))
PACK_ID = "mg-festa-seoul-stamp"
CARD_ID = "mg-festa-040"

PACK = {
    "id": PACK_ID,
    "nameKo": "포켓몬 메가페스타 POKEMON GO 서울 스탬프랠리",
    "nameEn": "MG Festa Pokémon GO Seoul Stamp Rally",
    "nameJa": "ポケモンメガフェスタ POKEMON GO ソウルスタンプラリー",
    "nameShort": "MG Festa Seoul",
    "code": "MG-PROMO",
    "releaseYear": 2026,
    "languages": ["kr"],
    "blurb": "메가페스타 × Pokémon GO 서울 스탬프랠리 프로모 — 잉어킹.",
    "blurbEn": "Mega Festa × Pokémon GO Seoul Stamp Rally promo — Magikarp.",
    "blurbJa": "メガフェスタ×Pokémon GOソウルスタンプラリープロモ — コイキング。",
    "packImage": "./assets/pack-mg-festa-seoul.png",
    "coverCardId": CARD_ID,
    "brgSets": {
        "kr": {"setName": "POKEMON MG KOREAN PROMO", "year": 2026},
    },
    "cardIds": [CARD_ID],
}

CARD = {
    "id": CARD_ID,
    "packId": PACK_ID,
    "nameKo": "잉어킹",
    "nameEn": "Magikarp",
    "nameJa": "コイキング",
    "number": "040",
    "rarity": "PROMO",
    "type": "water",
    "typeKo": None,
    "holoStyle": "holo",
    "image": "./assets/mg-festa-magikarp-040.png",
    "images": {
        "kr": "./assets/mg-festa-magikarp-040.png",
        "jp": None,
        "en": None,
    },
    "catalogKeys": {"jp": None, "kr": None, "en": None},
    "seed": {"basePrice": 80, "basePop": 19},
}


def main() -> int:
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))

    packs = [p for p in packs if p["id"] != PACK_ID]
    packs.append(PACK)
    catalog = [c for c in catalog if c.get("packId") != PACK_ID]
    catalog.append(CARD)

    asof_iso = datetime.now(KST).isoformat(timespec="seconds")
    live_path = DATA / "live" / "pop-price.json"
    previous = json.loads(live_path.read_text(encoding="utf-8")) if live_path.exists() else {}

    live, stats = build_live_snapshot(catalog, packs, asof_iso, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    brg_stats = fetch_brg_for_packs(
        catalog, packs, live, asof_iso, pack_id=PACK_ID, langs=["kr"], sleep_s=0.1
    )
    live["source"] = "seed+BRG"
    live["generatedAt"] = asof_iso
    keep_ids = {c["id"] for c in catalog}
    live["cards"] = {k: v for k, v in (live.get("cards") or {}).items() if k in keep_ids}

    last_run = {"ranAt": asof_iso, "stats": {**stats, "brg": brg_stats}}
    (DATA / "live" / "last-run.json").write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_data_bundle(DATA, packs, catalog, live, last_run)
    print(json.dumps({"packId": PACK_ID, "cardId": CARD_ID, "brg": brg_stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
