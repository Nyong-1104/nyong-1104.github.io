# -*- coding: utf-8 -*-
"""Add Team Pretend / Hiroshima / Fukuoka Special BOX packs with exclusive promos."""
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

IMG_013 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SMP/"
    "033288_P_SUKARUDANGOKKOPIKACHUU.jpg"
)
IMG_014 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SMP/"
    "033289_P_DANINGOKKOPIKACHUU.jpg"
)
IMG_261 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/"
    "049618_P_HIROSHIMANOPIKACHIXYUU.jpg"
)
IMG_289 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/"
    "049620_P_FUKUOKANOPIKACHIXYUU.jpg"
)

BOXES = [
    {
        "pack": {
            "id": "team-pretend-pikachu-box",
            "nameKo": "스페셜 BOX 단원고코 피카츄",
            "nameEn": "Special BOX Team Pretend Pikachu",
            "nameJa": "スペシャルBOX 団員ごっこピカチュウ",
            "nameShort": "Pretend BOX",
            "code": "PC-PRETEND",
            "releaseYear": 2016,
            "listGroup": "box",
            "listComplete": True,
            "expectedCards": 2,
            "languages": ["jp"],
            "blurb": "포켓몬센터 한정 스페셜 BOX · 단원고코·스컬단고코 피카츄 프로모 2종.",
            "blurbEn": "Pokémon Center limited Special BOX · Team Pretend & Team Skull Pretend Pikachu promos.",
            "blurbJa": "ポケモンセンター限定スペシャルBOXのプロモ「団員ごっこピカチュウ」「スカル団ごっこピカチュウ」。",
            "packImage": "./assets/box-team-pretend-pikachu.png",
            "coverCardId": "sm-p-014",
            "brgSets": {
                "jp": {"setName": "POKEMON S&M JAPANESE PROMO", "year": 2016},
            },
        },
        "artSrc": (
            "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_"
            "empty-window_images_box04-6566cdca-df13-4de1-9b58-2ca17261515a.png"
        ),
        "artDest": "box-team-pretend-pikachu.png",
        "cards": [
            {
                "id": "sm-p-014",
                "packId": "team-pretend-pikachu-box",
                "nameKo": "단원고코 피카츄",
                "nameEn": "Team Pretend Pikachu",
                "nameJa": "団員ごっこピカチュウ",
                "number": "014/SM-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_014,
                "images": {"jp": IMG_014, "kr": None, "en": None},
                "catalogKeys": {"jp": 33289, "kr": None, "en": None},
                "seed": {"basePrice": 300, "basePop": 30},
            },
            {
                "id": "sm-p-013",
                "packId": "team-pretend-pikachu-box",
                "nameKo": "스컬단고코 피카츄",
                "nameEn": "Team Skull Pretend Pikachu",
                "nameJa": "スカル団ごっこピカチュウ",
                "number": "013/SM-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_013,
                "images": {"jp": IMG_013, "kr": None, "en": None},
                "catalogKeys": {"jp": 33288, "kr": None, "en": None},
                "seed": {"basePrice": 200, "basePop": 30},
            },
        ],
    },
    {
        "pack": {
            "id": "pokemon-center-hiroshima-box",
            "nameKo": "스페셜 BOX 포켓몬센터 히로시마",
            "nameEn": "Special BOX Pokémon Center Hiroshima",
            "nameJa": "スペシャルBOX ポケモンセンター ヒロシマ",
            "nameShort": "Hiroshima BOX",
            "code": "PC-HIROSHIMA",
            "releaseYear": 2025,
            "listGroup": "box",
            "listComplete": True,
            "expectedCards": 1,
            "languages": ["jp"],
            "blurb": "포켓몬센터 히로시마 스페셜 BOX · 히로시마의 피카츄 프로모.",
            "blurbEn": "Pokémon Center Hiroshima Special BOX · Hiroshima's Pikachu promo.",
            "blurbJa": "スペシャルBOX ポケモンセンターヒロシマのプロモ「ヒロシマのピカチュウ」。",
            "packImage": "./assets/box-pokemon-center-hiroshima.png",
            "coverCardId": "sv-p-261",
            "brgSets": {
                "jp": {"setName": "POKEMON S&V JAPANESE PROMO", "year": 2025},
            },
        },
        "artSrc": (
            "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_"
            "empty-window_images_Box03-0a5b72a7-8c97-4ee4-a6af-3068feb9714d.png"
        ),
        "artDest": "box-pokemon-center-hiroshima.png",
        "cards": [
            {
                "id": "sv-p-261",
                "packId": "pokemon-center-hiroshima-box",
                "nameKo": "히로시마의 피카츄",
                "nameEn": "Hiroshima's Pikachu",
                "nameJa": "ヒロシマのピカチュウ",
                "number": "261/SV-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_261,
                "images": {"jp": IMG_261, "kr": None, "en": None},
                "catalogKeys": {"jp": 49618, "kr": None, "en": None},
                "seed": {"basePrice": 180, "basePop": 30},
            },
        ],
    },
    {
        "pack": {
            "id": "pokemon-center-fukuoka-box",
            "nameKo": "스페셜 BOX 포켓몬센터 후쿠오카",
            "nameEn": "Special BOX Pokémon Center Fukuoka",
            "nameJa": "スペシャルBOX ポケモンセンター フクオカ",
            "nameShort": "Fukuoka BOX",
            "code": "PC-FUKUOKA",
            "releaseYear": 2025,
            "listGroup": "box",
            "listComplete": True,
            "expectedCards": 1,
            "languages": ["jp"],
            "blurb": "포켓몬센터 후쿠오카 스페셜 BOX · 후쿠오카의 피카츄 프로모.",
            "blurbEn": "Pokémon Center Fukuoka Special BOX · Fukuoka's Pikachu promo.",
            "blurbJa": "スペシャルBOX ポケモンセンターフクオカのプロモ「フクオカのピカチュウ」。",
            "packImage": "./assets/box-pokemon-center-fukuoka.png",
            "coverCardId": "sv-p-289",
            "brgSets": {
                "jp": {"setName": "POKEMON S&V JAPANESE PROMO", "year": 2025},
            },
        },
        "artSrc": (
            "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_"
            "empty-window_images_Box05-39884c9c-8cb3-4be6-8c56-93065b1d0af1.png"
        ),
        "artDest": "box-pokemon-center-fukuoka.png",
        "cards": [
            {
                "id": "sv-p-289",
                "packId": "pokemon-center-fukuoka-box",
                "nameKo": "후쿠오카의 피카츄",
                "nameEn": "Fukuoka's Pikachu",
                "nameJa": "フクオカのピカチュウ",
                "number": "289/SV-P",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": None,
                "holoStyle": "holo",
                "image": IMG_289,
                "images": {"jp": IMG_289, "kr": None, "en": None},
                "catalogKeys": {"jp": 49620, "kr": None, "en": None},
                "seed": {"basePrice": 180, "basePop": 30},
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
        # stash pack object for write
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
