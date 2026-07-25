# -*- coding: utf-8 -*-
"""Add missing Yu Nagaba Pikachu promo 208/S-P into the Nagaba pack."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pokepop_snapshot import (  # noqa: E402
    build_live_snapshot,
    load_previous_live,
    write_data_bundle,
)
from ebay_prices import restore_ebay_prices  # noqa: E402
from brg_pop import restore_brg_pops  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402

KST = timezone(timedelta(hours=9))
PACK_ID = "yu-nagaba-eevee-promo"
CARD_ID = "nagaba-208"

SRC_CANDIDATES = [
    Path(
        r"C:\Users\admin\.cursor\projects\c-Users-admin-Projects-nyong-1104-github-io\assets"
        r"\c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images"
        r"_________-cc4e33bc-0897-4b1c-b8bd-fd69cf58b512.png"
    ),
    ASSETS / "yu-nagaba-pikachu-208.png",
]

IMG_REL = "./assets/yu-nagaba-pikachu-208.png"


def ensure_image() -> None:
    dest = ASSETS / "yu-nagaba-pikachu-208.png"
    if dest.exists() and dest.stat().st_size > 1000:
        print("image ok", dest, dest.stat().st_size)
        return
    for src in SRC_CANDIDATES:
        if src.exists():
            shutil.copy2(src, dest)
            print("copied", src, "->", dest)
            return
    raise SystemExit("missing source image for Nagaba Pikachu")


def main() -> int:
    ensure_image()

    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))

    card = {
        "id": CARD_ID,
        "packId": PACK_ID,
        "nameKo": "피카츄",
        "nameEn": "Pikachu",
        "nameJa": "ピカチュウ",
        "number": "208/S-P",
        "rarity": "PROMO",
        "type": "lightning",
        "typeKo": "번개",
        "holoStyle": "holo",
        "image": IMG_REL,
        "images": {"jp": IMG_REL, "kr": None, "en": None},
        "catalogKeys": {"jp": None, "kr": None, "en": None},
        "seed": {"basePrice": 180, "basePop": 40},
        "tier": "B",
        "notes": "YU NAGABA × Pokémon Card Game promo (2021-07-22). Illus. YU NAGABA.",
    }

    catalog = [c for c in catalog if c.get("id") != CARD_ID]
    # Keep Nagaba cards together: insert before first existing nagaba-* if present.
    insert_at = next(
        (i for i, c in enumerate(catalog) if str(c.get("id", "")).startswith("nagaba-")),
        len(catalog),
    )
    catalog.insert(insert_at, card)

    pack = next(p for p in packs if p["id"] == PACK_ID)
    ids = [cid for cid in pack.get("cardIds") or [] if cid != CARD_ID]
    pack["cardIds"] = [CARD_ID] + ids
    pack["listComplete"] = True
    pack["expectedCards"] = 10
    pack["blurb"] = "나가바 유 콜라보 — 피카츄 + 이브이 일족 전 10종."
    pack["blurbEn"] = "Yu Nagaba collab — Pikachu + all 9 Eevee-line promos (10 total)."
    pack["blurbJa"] = "長場雄コラボ — ピカチュウ＋イーブイたち全10種。"

    asof = datetime.now(KST).isoformat(timespec="seconds")
    previous = load_previous_live(DATA)
    live, stats = build_live_snapshot(catalog, packs, asof, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or live.get("source") or "seed"
    live["generatedAt"] = asof

    last_run = {
        "ranAt": asof,
        "stats": {
            **stats,
            "addedNagabaPikachu": CARD_ID,
        },
    }
    (DATA / "live" / "last-run.json").write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_data_bundle(DATA, packs, catalog, live, last_run)
    print(json.dumps({"added": CARD_ID, "packCards": pack["cardIds"], **stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
