# -*- coding: utf-8 -*-
"""Add Special BOX Rokon's Crystal Season with Vulpix / Alolan Vulpix SM-P promos."""
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
PACK_ID = "rokon-crystal-season-box"

CURSOR_ART = Path(
    r"C:\Users\admin\.cursor\projects\c-Users-admin-Projects-nyong-1104-github-io\assets"
) / "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_box06-ee1bd3ca-896e-4d85-a02e-2aa57ae732e9.png"
PACK_IMAGE_NAME = "box-rokon-crystal-season.png"

IMG_146 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SMP/"
    "034353_P_ROKON.jpg"
)
IMG_147 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SMP/"
    "034354_P_ARORAROKON.jpg"
)

CARDS = [
    {
        "id": "sm-p-146",
        "packId": PACK_ID,
        "nameKo": "로콘",
        "nameEn": "Vulpix",
        "nameJa": "ロコン",
        "number": "146/SM-P",
        "rarity": "PROMO",
        "type": "fire",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_146,
        "images": {"jp": IMG_146, "kr": None, "en": None},
        "catalogKeys": {"jp": 34353, "kr": None, "en": None},
        "seed": {"basePrice": 250, "basePop": 30},
    },
    {
        "id": "sm-p-147",
        "packId": PACK_ID,
        "nameKo": "알로라 로콘",
        "nameEn": "Alolan Vulpix",
        "nameJa": "アローラ ロコン",
        "number": "147/SM-P",
        "rarity": "PROMO",
        "type": "water",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_147,
        "images": {"jp": IMG_147, "kr": None, "en": None},
        "catalogKeys": {"jp": 34354, "kr": None, "en": None},
        "seed": {"basePrice": 250, "basePop": 30},
    },
]

PACK = {
    "id": PACK_ID,
    "nameKo": "스페셜 BOX 로콘의 크리스탈 시즌",
    "nameEn": "Special BOX Rokon's Crystal Season",
    "nameJa": "スペシャルBOX Rokon's Crystal Season (ロコンのクリスタルシーズン)",
    "nameShort": "Crystal Season",
    "code": "PC-CRYSTAL",
    "releaseYear": 2017,
    "listGroup": "box",
    "listComplete": True,
    "expectedCards": 2,
    "languages": ["jp"],
    "blurb": "포켓몬센터 한정 스페셜 BOX · 로콘·알로라 로콘 홀로 프로모 2종.",
    "blurbEn": "Pokémon Center limited Special BOX · Vulpix & Alolan Vulpix holo promos.",
    "blurbJa": "ポケモンセンター限定スペシャルBOXのプロモ「ロコン」「アローラ ロコン」。",
    "packImage": f"./assets/{PACK_IMAGE_NAME}",
    "coverCardId": "sm-p-146",
    "brgSets": {
        "jp": {"setName": "POKEMON S&M JAPANESE PROMO", "year": 2017},
    },
    "cardIds": [c["id"] for c in CARDS],
}


def copy_box_art() -> Path:
    dest = ASSETS / PACK_IMAGE_NAME
    if dest.is_file() and dest.stat().st_size > 1000:
        return dest
    if not CURSOR_ART.is_file():
        raise FileNotFoundError(f"Box art not found: {dest} / {CURSOR_ART}")
    shutil.copy2(CURSOR_ART, dest)
    return dest


def main() -> int:
    art = copy_box_art()
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
                "artBytes": art.stat().st_size,
                **stats,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
