# -*- coding: utf-8 -*-
"""Add Rayquaza / Magikarp-Gyarados / Mega Charizard Y Special BOX packs."""
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
CURSOR_ASSETS = Path(
    r"C:\Users\admin\.cursor\projects\c-Users-admin-Projects-nyong-1104-github-io\assets"
)

IMG_150 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "031162_P_KOIKINGUGOKKOPIKACHUU.jpg"
)
IMG_151 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "031163_P_GYARADOSUGOKKOPIKACHUU.jpg"
)
IMG_206 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "031642_P_PIKACHUU.jpg"
)
IMG_208 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "031641_P_PONCHOWOKITAPIKACHUU.jpg"
)
IMG_230 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "032191_P_PONCHOWOKITAPIKACHUU.jpg"
)
IMG_231 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "032192_P_PONCHOWOKITAPIKACHUU.jpg"
)

BOXES = [
    {
        "pack": {
            "id": "rayquaza-poncho-pikachu-box",
            "nameKo": "스페셜 BOX 레쿠자 판초를 입은 피카츄",
            "nameEn": "Special BOX Pikachu in Rayquaza Poncho",
            "nameJa": "スペシャルBOX レックウザポンチョを着たピカチュウ",
            "nameShort": "Rayquaza Poncho",
            "code": "PC-RAY-PONCHO",
            "releaseYear": 2016,
            "listGroup": "box",
            "listComplete": True,
            "expectedCards": 2,
            "languages": ["jp"],
            "blurb": "포켓몬센터 한정 XY BREAK 스페셜 BOX · 레쿠자·검은 레쿠자 판초 피카츄 프리미엄 키라 2종.",
            "blurbEn": "Pokémon Center limited XY BREAK Special BOX · Rayquaza & Shiny Rayquaza Poncho Pikachu premium kira promos.",
            "blurbJa": "ポケモンセンター限定スペシャルBOXのプレミアムキラ「ポンチョを着たピカチュウ（レックウザ／黒いレックウザ）」。",
            "packImage": "./assets/box-rayquaza-poncho-pikachu.png",
            "coverCardId": "xy-p-230",
            "brgSets": {
                "jp": {"setName": "POKEMON XY JAPANESE PROMO", "year": 2016},
            },
        },
        "artSrc": (
            "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_"
            "empty-window_images_box07-869ef696-6f8e-41d8-885b-70b25f802ed2.png"
        ),
        "artDest": "box-rayquaza-poncho-pikachu.png",
        "cards": [
            {
                "id": "xy-p-230",
                "packId": "rayquaza-poncho-pikachu-box",
                "nameKo": "레쿠자 판초를 입은 피카츄",
                "nameEn": "Pikachu in Rayquaza Poncho",
                "nameJa": "ポンチョを着たピカチュウ（レックウザ）",
                "number": "230/XY-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_230,
                "images": {"jp": IMG_230, "kr": None, "en": None},
                "catalogKeys": {"jp": 32191, "kr": None, "en": None},
                "seed": {"basePrice": 800, "basePop": 40},
            },
            {
                "id": "xy-p-231",
                "packId": "rayquaza-poncho-pikachu-box",
                "nameKo": "검은 레쿠자 판초를 입은 피카츄",
                "nameEn": "Pikachu in Shiny Rayquaza Poncho",
                "nameJa": "ポンチョを着たピカチュウ（黒いレックウザ）",
                "number": "231/XY-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_231,
                "images": {"jp": IMG_231, "kr": None, "en": None},
                "catalogKeys": {"jp": 32192, "kr": None, "en": None},
                "seed": {"basePrice": 800, "basePop": 40},
            },
        ],
    },
    {
        "pack": {
            "id": "magikarp-gyarados-pretend-pikachu-box",
            "nameKo": "스페셜 BOX 잉어킹고코 & 갸라도스고코 피카츄",
            "nameEn": "Special BOX Magikarp & Gyarados Pretend Pikachu",
            "nameJa": "スペシャルBOX コイキングごっこ & ギャラドスごっこ ピカチュウ",
            "nameShort": "Magikarp BOX",
            "code": "PC-MAGI-PRETEND",
            "releaseYear": 2015,
            "listGroup": "box",
            "listComplete": True,
            "expectedCards": 2,
            "languages": ["jp"],
            "blurb": "포켓몬센터 히로시마 오픈 기념 XY 스페셜 BOX · 잉어킹고코·갸라도스고코 피카츄 프로모 2종.",
            "blurbEn": "Pokémon Center Hiroshima opening XY Special BOX · Magikarp & Gyarados Pretend Pikachu promos.",
            "blurbJa": "ポケモンセンターヒロシマオープン記念スペシャルBOXのプロモ「コイキングごっこピカチュウ」「ギャラドスごっこピカチュウ」。",
            "packImage": "./assets/box-magikarp-gyarados-pretend-pikachu.png",
            "coverCardId": "xy-p-150",
            "brgSets": {
                "jp": {"setName": "POKEMON XY JAPANESE PROMO", "year": 2015},
            },
        },
        "artSrc": (
            "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_"
            "empty-window_images_box08-9e17ed8b-8144-4bef-9c04-e200ac12659c.png"
        ),
        "artDest": "box-magikarp-gyarados-pretend-pikachu.png",
        "cards": [
            {
                "id": "xy-p-150",
                "packId": "magikarp-gyarados-pretend-pikachu-box",
                "nameKo": "잉어킹고코 피카츄",
                "nameEn": "Magikarp Pretend Pikachu",
                "nameJa": "コイキングごっこピカチュウ",
                "number": "150/XY-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_150,
                "images": {"jp": IMG_150, "kr": None, "en": None},
                "catalogKeys": {"jp": 31162, "kr": None, "en": None},
                "seed": {"basePrice": 500, "basePop": 40},
            },
            {
                "id": "xy-p-151",
                "packId": "magikarp-gyarados-pretend-pikachu-box",
                "nameKo": "갸라도스고코 피카츄",
                "nameEn": "Gyarados Pretend Pikachu",
                "nameJa": "ギャラドスごっこピカチュウ",
                "number": "151/XY-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_151,
                "images": {"jp": IMG_151, "kr": None, "en": None},
                "catalogKeys": {"jp": 31163, "kr": None, "en": None},
                "seed": {"basePrice": 500, "basePop": 40},
            },
        ],
    },
    {
        "pack": {
            "id": "mega-charizard-y-poncho-pikachu-box",
            "nameKo": "스페셜 BOX 메가리자돈Y 판초를 입은 피카츄",
            "nameEn": "Special BOX Pikachu in Mega Charizard Y Poncho",
            "nameJa": "スペシャルBOX メガリザードンYのポンチョを着たピカチュウ",
            "nameShort": "Charizard Y Poncho",
            "code": "PC-ZARDY-PONCHO",
            "releaseYear": 2016,
            "listGroup": "box",
            "listComplete": True,
            "expectedCards": 2,
            "languages": ["jp"],
            "blurb": "XY BREAK 스페셜 BOX · 메가리자돈Y 판초 피카츄 프리미엄 키라 + 스페셜 키라 피카츄.",
            "blurbEn": "XY BREAK Special BOX · Mega Charizard Y Poncho Pikachu premium kira + special kira Pikachu.",
            "blurbJa": "スペシャルBOXのプレミアムキラ「ポンチョを着たピカチュウ（メガリザードンY）」とスペシャルキラ「ピカチュウ」。",
            "packImage": "./assets/box-mega-charizard-y-poncho-pikachu.png",
            "coverCardId": "xy-p-208",
            "brgSets": {
                "jp": {"setName": "POKEMON XY JAPANESE PROMO", "year": 2016},
            },
        },
        "artSrc": (
            "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_"
            "empty-window_images_box09-1cf9c9c4-39f7-4681-ba3f-0a21023ebedb.png"
        ),
        "artDest": "box-mega-charizard-y-poncho-pikachu.png",
        "cards": [
            {
                "id": "xy-p-208",
                "packId": "mega-charizard-y-poncho-pikachu-box",
                "nameKo": "메가리자돈Y 판초를 입은 피카츄",
                "nameEn": "Pikachu in Mega Charizard Y Poncho",
                "nameJa": "ポンチョを着たピカチュウ（メガリザードンY）",
                "number": "208/XY-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_208,
                "images": {"jp": IMG_208, "kr": None, "en": None},
                "catalogKeys": {"jp": 31641, "kr": None, "en": None},
                "seed": {"basePrice": 900, "basePop": 40},
            },
            {
                "id": "xy-p-206",
                "packId": "mega-charizard-y-poncho-pikachu-box",
                "nameKo": "피카츄",
                "nameEn": "Pikachu",
                "nameJa": "ピカチュウ",
                "number": "206/XY-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_206,
                "images": {"jp": IMG_206, "kr": None, "en": None},
                "catalogKeys": {"jp": 31642, "kr": None, "en": None},
                "seed": {"basePrice": 200, "basePop": 50},
            },
        ],
    },
]


def copy_box_art(src_name: str, dest_name: str) -> Path:
    dest = ASSETS / dest_name
    if dest.is_file() and dest.stat().st_size > 1000:
        return dest
    src = CURSOR_ASSETS / src_name
    if not src.is_file():
        raise FileNotFoundError(f"Box art not found: {dest} / {src}")
    shutil.copy2(src, dest)
    return dest


def main() -> int:
    summary = []
    all_cards: list[dict] = []
    pack_ids: set[str] = set()
    card_ids: set[str] = set()

    for box in BOXES:
        art = copy_box_art(box["artSrc"], box["artDest"])
        pack = dict(box["pack"])
        cards = [dict(c) for c in box["cards"]]
        pack["cardIds"] = [c["id"] for c in cards]
        all_cards.extend(cards)
        pack_ids.add(pack["id"])
        card_ids.update(c["id"] for c in cards)
        summary.append(
            {
                "packId": pack["id"],
                "cardIds": pack["cardIds"],
                "packImage": pack["packImage"],
                "artBytes": art.stat().st_size,
            }
        )
        box["_pack"] = pack

    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))

    packs = [p for p in packs if p["id"] not in pack_ids]
    packs.extend(box["_pack"] for box in BOXES)
    catalog = [
        c
        for c in catalog
        if c.get("id") not in card_ids and c.get("packId") not in pack_ids
    ]
    catalog.extend(all_cards)

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
    print(json.dumps({"boxes": summary, **stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
