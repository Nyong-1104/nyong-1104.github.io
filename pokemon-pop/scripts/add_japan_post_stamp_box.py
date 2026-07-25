# -*- coding: utf-8 -*-
"""Add Japan Post Stamp Box (見返り美人・月に雁) with two S-P promos."""
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

from brg_pop import restore_brg_pops  # noqa: E402
from ebay_prices import restore_ebay_prices  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402
from pokepop_snapshot import build_live_snapshot, write_data_bundle  # noqa: E402

KST = timezone(timedelta(hours=9))
PACK_ID = "japan-post-stamp-box"

CURSOR_ART = Path(
    r"C:\Users\admin\.cursor\projects\c-Users-admin-Projects-nyong-1104-github-io\assets"
) / "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_Japan_Post_Stamp_Box-10603967-1bb0-40bd-874f-37ef659f85b0.png"
PACK_IMAGE_NAME = "pack-japan-post-stamp-box.png"

IMG_226 = "https://www.pokemon-card.com/assets/images/card_images/large/S-P/039953_P_UTSUU.jpg"
IMG_227 = "https://www.pokemon-card.com/assets/images/card_images/large/S-P/039954_P_PIKACHUU.jpg"

CARDS = [
    {
        "id": "s-p-227",
        "packId": PACK_ID,
        "nameKo": "미카에리비진",
        "nameEn": "Beauty Looking Back",
        "nameJa": "見返り美人",
        "number": "227/S-P",
        "rarity": "PROMO",
        "type": "lightning",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_227,
        "images": {"jp": IMG_227, "kr": None, "en": None},
        "catalogKeys": {"jp": 39954, "kr": None, "en": None},
        "seed": {"basePrice": 200, "basePop": 30},
    },
    {
        "id": "s-p-226",
        "packId": PACK_ID,
        "nameKo": "츠키니간",
        "nameEn": "Moon and Geese",
        "nameJa": "月に雁",
        "number": "226/S-P",
        "rarity": "PROMO",
        "type": "water",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_226,
        "images": {"jp": IMG_226, "kr": None, "en": None},
        "catalogKeys": {"jp": 39953, "kr": None, "en": None},
        "seed": {"basePrice": 80, "basePop": 30},
    },
]

PACK = {
    "id": PACK_ID,
    "nameKo": "포켓몬 우표 BOX",
    "nameEn": "Pokémon Stamp BOX",
    "nameJa": "ポケモン切手BOX",
    "nameShort": "Stamp BOX",
    "code": "JP-STAMP",
    "releaseYear": 2021,
    "listGroup": "box",
    "listComplete": True,
    "expectedCards": 2,
    "languages": ["jp"],
    "blurb": "Japan Post Stamp Box · 미카에리비진·츠키니간 프로모 2종.",
    "blurbEn": "Japan Post Stamp Box · Beauty Looking Back & Moon and Geese promos.",
    "blurbJa": "ポケモン切手BOX〜見返り美人・月に雁セット〜のプロモ2種。",
    "packImage": f"./assets/{PACK_IMAGE_NAME}",
    "coverCardId": "s-p-227",
    "brgSets": {
        "jp": {"setName": "POKEMON SWSH JAPANESE PROMO", "year": 2021},
    },
    "cardIds": [c["id"] for c in CARDS],
}


def copy_box_art() -> Path:
    dest = ASSETS / PACK_IMAGE_NAME
    if dest.is_file():
        return dest
    if not CURSOR_ART.is_file():
        raise FileNotFoundError(f"Box art not found: {dest} / {CURSOR_ART}")
    shutil.copy2(CURSOR_ART, dest)
    return dest


def main() -> int:
    copy_box_art()
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))

    card_ids = {c["id"] for c in CARDS}
    packs = [p for p in packs if p["id"] != PACK_ID]
    packs.append(PACK)
    catalog = [c for c in catalog if c.get("id") not in card_ids and c.get("packId") != PACK_ID]
    catalog.extend(CARDS)

    asof_iso = datetime.now(KST).isoformat(timespec="seconds")
    live_path = DATA / "live" / "pop-price.json"
    previous = json.loads(live_path.read_text(encoding="utf-8")) if live_path.exists() else {}

    live, stats = build_live_snapshot(catalog, packs, asof_iso, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or "seed"
    live["generatedAt"] = asof_iso
    keep_ids = {c["id"] for c in catalog}
    live["cards"] = {k: v for k, v in (live.get("cards") or {}).items() if k in keep_ids}

    last_run = {"ranAt": asof_iso, "stats": stats}
    (DATA / "live" / "last-run.json").write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_data_bundle(DATA, packs, catalog, live, last_run)
    print(
        json.dumps(
            {
                "packId": PACK_ID,
                "cardIds": [c["id"] for c in CARDS],
                "packImage": PACK["packImage"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
