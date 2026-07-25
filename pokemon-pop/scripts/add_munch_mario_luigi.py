# -*- coding: utf-8 -*-
"""Add Munch The Scream promo pack + Mario & Luigi Pikachu Special BOX."""
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

MUNCH_PACK_ID = "munch-scream-promo"
MARIO_PACK_ID = "mario-luigi-pikachu-box"

MUNCH_ART_SRC = (
    "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_"
    "empty-window_images_______-7756e152-f8ab-453f-80a7-f3db61aec9fa.png"
)
MUNCH_ART_DEST = "pack-munch-scream.png"

MARIO_ART_SRC = (
    "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_"
    "empty-window_images____BOX-679571f1-da82-433c-a85a-8f0d57810335.png"
)
MARIO_ART_DEST = "box-mario-luigi-pikachu.png"

IMG_286 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SMP/"
    "035892_P_KODAKKU.jpg"
)
IMG_287 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SMP/"
    "035893_P_IBUI.jpg"
)
IMG_288 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SMP/"
    "035894_P_PIKACHUU.jpg"
)
IMG_289 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SMP/"
    "035895_P_MIMIKKYU.jpg"
)
IMG_290 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SMP/"
    "035896_P_MOKURO.jpg"
)

IMG_293 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "032348_P_MARIOPIKACHUU.jpg"
)
IMG_294 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "032349_P_MARIOPIKACHUU.jpg"
)
IMG_295 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "032350_P_RUIJIPIKACHUU.jpg"
)
IMG_296 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/XYP/"
    "032351_P_RUIJIPIKACHUU.jpg"
)

MUNCH_CARDS = [
    {
        "id": "sm-p-286",
        "packId": MUNCH_PACK_ID,
        "nameKo": "고라파덕",
        "nameEn": "Psyduck",
        "nameJa": "コダック",
        "number": "286/SM-P",
        "rarity": "PROMO",
        "type": "water",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_286,
        "images": {"jp": IMG_286, "kr": None, "en": None},
        "catalogKeys": {"jp": 35892, "kr": None, "en": None},
        "seed": {"basePrice": 120, "basePop": 40},
    },
    {
        "id": "sm-p-287",
        "packId": MUNCH_PACK_ID,
        "nameKo": "이브이",
        "nameEn": "Eevee",
        "nameJa": "イーブイ",
        "number": "287/SM-P",
        "rarity": "PROMO",
        "type": "colorless",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_287,
        "images": {"jp": IMG_287, "kr": None, "en": None},
        "catalogKeys": {"jp": 35893, "kr": None, "en": None},
        "seed": {"basePrice": 150, "basePop": 40},
    },
    {
        "id": "sm-p-288",
        "packId": MUNCH_PACK_ID,
        "nameKo": "피카츄",
        "nameEn": "Pikachu",
        "nameJa": "ピカチュウ",
        "number": "288/SM-P",
        "rarity": "PROMO",
        "type": "lightning",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_288,
        "images": {"jp": IMG_288, "kr": None, "en": None},
        "catalogKeys": {"jp": 35894, "kr": None, "en": None},
        "seed": {"basePrice": 400, "basePop": 35},
    },
    {
        "id": "sm-p-289",
        "packId": MUNCH_PACK_ID,
        "nameKo": "따라큐",
        "nameEn": "Mimikyu",
        "nameJa": "ミミッキュ",
        "number": "289/SM-P",
        "rarity": "PROMO",
        "type": "psychic",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_289,
        "images": {"jp": IMG_289, "kr": None, "en": None},
        "catalogKeys": {"jp": 35895, "kr": None, "en": None},
        "seed": {"basePrice": 180, "basePop": 40},
    },
    {
        "id": "sm-p-290",
        "packId": MUNCH_PACK_ID,
        "nameKo": "나몰빼미",
        "nameEn": "Rowlet",
        "nameJa": "モクロー",
        "number": "290/SM-P",
        "rarity": "PROMO",
        "type": "grass",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_290,
        "images": {"jp": IMG_290, "kr": None, "en": None},
        "catalogKeys": {"jp": 35896, "kr": None, "en": None},
        "seed": {"basePrice": 120, "basePop": 40},
    },
]

MUNCH_PACK = {
    "id": MUNCH_PACK_ID,
    "nameKo": "뭉크의 절규 프로모카드팩",
    "nameEn": "Munch The Scream Promo Pack",
    "nameJa": "ムンクの叫び プロモカードパック",
    "nameShort": "뭉크",
    "code": "MUNCH-P",
    "releaseYear": 2018,
    "listGroup": "promo",
    "listComplete": True,
    "expectedCards": 5,
    "languages": ["jp"],
    "blurb": "ムンク展 × 포켓몬카드 · 절규 모티브 프로모 전 5종 (고라파덕·이브이·피카츄·따라큐·나몰빼미).",
    "blurbEn": "Munch exhibition × Pokémon Card · all 5 The Scream promos (Psyduck, Eevee, Pikachu, Mimikyu, Rowlet).",
    "blurbJa": "ムンク展×ポケモンカードゲーム — 「叫び」モチーフプロモ全5種。",
    "packImage": f"./assets/{MUNCH_ART_DEST}",
    "coverCardId": "sm-p-288",
    "brgSets": {
        "jp": {"setName": "POKEMON S&M JAPANESE PROMO", "year": 2018},
    },
    "cardIds": [c["id"] for c in MUNCH_CARDS],
}

MARIO_CARDS = [
    {
        "id": "xy-p-294",
        "packId": MARIO_PACK_ID,
        "nameKo": "마리오 피카츄 (프리미엄 키라)",
        "nameEn": "Mario Pikachu (Premium Kira)",
        "nameJa": "マリオピカチュウ（プレミアムキラ）",
        "number": "294/XY-P",
        "rarity": "PROMO",
        "type": "lightning",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_294,
        "images": {"jp": IMG_294, "kr": None, "en": None},
        "catalogKeys": {"jp": 32349, "kr": None, "en": None},
        "seed": {"basePrice": 2500, "basePop": 25},
    },
    {
        "id": "xy-p-293",
        "packId": MARIO_PACK_ID,
        "nameKo": "마리오 피카츄",
        "nameEn": "Mario Pikachu",
        "nameJa": "マリオピカチュウ",
        "number": "293/XY-P",
        "rarity": "PROMO",
        "type": "lightning",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_293,
        "images": {"jp": IMG_293, "kr": None, "en": None},
        "catalogKeys": {"jp": 32348, "kr": None, "en": None},
        "seed": {"basePrice": 1200, "basePop": 30},
    },
    {
        "id": "xy-p-296",
        "packId": MARIO_PACK_ID,
        "nameKo": "루이지 피카츄 (프리미엄 키라)",
        "nameEn": "Luigi Pikachu (Premium Kira)",
        "nameJa": "ルイージピカチュウ（プレミアムキラ）",
        "number": "296/XY-P",
        "rarity": "PROMO",
        "type": "lightning",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_296,
        "images": {"jp": IMG_296, "kr": None, "en": None},
        "catalogKeys": {"jp": 32351, "kr": None, "en": None},
        "seed": {"basePrice": 2500, "basePop": 25},
    },
    {
        "id": "xy-p-295",
        "packId": MARIO_PACK_ID,
        "nameKo": "루이지 피카츄",
        "nameEn": "Luigi Pikachu",
        "nameJa": "ルイージピカチュウ",
        "number": "295/XY-P",
        "rarity": "PROMO",
        "type": "lightning",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_295,
        "images": {"jp": IMG_295, "kr": None, "en": None},
        "catalogKeys": {"jp": 32350, "kr": None, "en": None},
        "seed": {"basePrice": 1200, "basePop": 30},
    },
]

MARIO_PACK = {
    "id": MARIO_PACK_ID,
    "nameKo": "스페셜 BOX 마리오 & 루이지 피카츄",
    "nameEn": "Mario & Luigi Pikachu Special BOX",
    "nameJa": "スペシャルBOX マリオ＆ルイージピカチュウ",
    "nameShort": "Mario & Luigi",
    "code": "PC-MARIO-LUIGI",
    "releaseYear": 2016,
    "listGroup": "box",
    "listComplete": True,
    "expectedCards": 4,
    "languages": ["jp"],
    "blurb": "마리오·루이지 피카츄 스페셜 BOX 합본 · 프리미엄/오리지널 키라 프로모 전 4종.",
    "blurbEn": "Combined Mario & Luigi Pikachu Special BOX · all 4 premium/original kira promos.",
    "blurbJa": "マリオ／ルイージピカチュウスペシャルBOXのプレミアムキラ・オリジナルキラ全4種。",
    "packImage": f"./assets/{MARIO_ART_DEST}",
    "coverCardId": "xy-p-294",
    "brgSets": {
        "jp": {"setName": "POKEMON XY JAPANESE PROMO", "year": 2016},
    },
    "cardIds": [c["id"] for c in MARIO_CARDS],
}


def copy_art(src_name: str, dest_name: str) -> Path:
    dest = ASSETS / dest_name
    if dest.is_file() and dest.stat().st_size > 1000:
        return dest
    src = CURSOR_ASSETS / src_name
    if not src.is_file():
        raise FileNotFoundError(f"Art not found: {dest} / {src}")
    shutil.copy2(src, dest)
    return dest


def upsert(packs: list[dict], catalog: list[dict], pack: dict, cards: list[dict]) -> None:
    pack_id = pack["id"]
    card_ids = {c["id"] for c in cards}
    packs[:] = [p for p in packs if p["id"] != pack_id]
    packs.append(pack)
    catalog[:] = [
        c
        for c in catalog
        if c.get("id") not in card_ids and c.get("packId") != pack_id
    ]
    catalog.extend(cards)


def main() -> int:
    munch_art = copy_art(MUNCH_ART_SRC, MUNCH_ART_DEST)
    mario_art = copy_art(MARIO_ART_SRC, MARIO_ART_DEST)

    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))

    upsert(packs, catalog, MUNCH_PACK, MUNCH_CARDS)
    upsert(packs, catalog, MARIO_PACK, MARIO_CARDS)

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
                "munch": {
                    "packId": MUNCH_PACK_ID,
                    "cardIds": [c["id"] for c in MUNCH_CARDS],
                    "packImage": MUNCH_PACK["packImage"],
                    "artBytes": munch_art.stat().st_size,
                },
                "marioLuigi": {
                    "packId": MARIO_PACK_ID,
                    "cardIds": [c["id"] for c in MARIO_CARDS],
                    "packImage": MARIO_PACK["packImage"],
                    "artBytes": mario_art.stat().st_size,
                },
                **stats,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
