# -*- coding: utf-8 -*-
"""Add Special BOX Pokémon Center Tohoku with exclusive Tohoku's Pikachu promo."""
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
PACK_ID = "pokemon-center-tohoku-box"

CURSOR_ART = Path(
    r"C:\Users\admin\.cursor\projects\c-Users-admin-Projects-nyong-1104-github-io\assets"
) / "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_Box02-228cfdef-62e9-4906-a581-da0b915c6516.png"
PACK_IMAGE_NAME = "box-pokemon-center-tohoku.png"

IMG_260 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/"
    "049617_P_TOUHOKUNOPIKACHIXYUU.jpg"
)

CARDS = [
    {
        "id": "sv-p-260",
        "packId": PACK_ID,
        "nameKo": "도호쿠의 피카츄",
        "nameEn": "Tohoku's Pikachu",
        "nameJa": "トウホクのピカチュウ",
        "number": "260/SV-P",
        "rarity": "PROMO",
        "type": "lightning",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_260,
        "images": {"jp": IMG_260, "kr": None, "en": None},
        "catalogKeys": {"jp": 49617, "kr": None, "en": None},
        "seed": {"basePrice": 180, "basePop": 30},
    },
]

PACK = {
    "id": PACK_ID,
    "nameKo": "스페셜 BOX 포켓몬센터 도호쿠",
    "nameEn": "Special BOX Pokémon Center Tohoku",
    "nameJa": "スペシャルBOX ポケモンセンター トウホク",
    "nameShort": "Tohoku BOX",
    "code": "PC-TOHOKU",
    "releaseYear": 2025,
    "listGroup": "box",
    "listComplete": True,
    "expectedCards": 1,
    "languages": ["jp"],
    "blurb": "포켓몬센터 도호쿠 스페셜 BOX · 도호쿠의 피카츄 프로모.",
    "blurbEn": "Pokémon Center Tohoku Special BOX · Tohoku's Pikachu promo.",
    "blurbJa": "スペシャルBOX ポケモンセンタートウホクのプロモ「トウホクのピカチュウ」。",
    "packImage": f"./assets/{PACK_IMAGE_NAME}",
    "coverCardId": "sv-p-260",
    "brgSets": {
        "jp": {"setName": "POKEMON S&V JAPANESE PROMO", "year": 2025},
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
