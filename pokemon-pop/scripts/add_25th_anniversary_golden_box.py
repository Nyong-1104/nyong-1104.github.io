# -*- coding: utf-8 -*-
"""Add 25th Anniversary Golden Box with exclusive gold Pikachu V / Monster Ball."""
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
PACK_ID = "25th-anniversary-golden-box"

CURSOR_ART = Path(
    r"C:\Users\admin\.cursor\projects\c-Users-admin-Projects-nyong-1104-github-io\assets"
) / "c__Users_admin_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_25th_box-ca799b18-fceb-4bb6-88a6-44bb848c6c1f.png"
PACK_IMAGE_NAME = "box-25th-anniversary-golden.png"

IMG_001 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/S8a-G/"
    "041664_P_PIKACHIXYUUV.jpg"
)
IMG_002 = (
    "https://www.pokemon-card.com/assets/images/card_images/large/S8a-G/"
    "041665_T_MONSUTABORU.jpg"
)

CARDS = [
    {
        "id": "s8a-g-001",
        "packId": PACK_ID,
        "nameKo": "피카츄V",
        "nameEn": "Pikachu V",
        "nameJa": "ピカチュウV",
        "number": "001/015",
        "rarity": "PROMO",
        "type": "lightning",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_001,
        "images": {"jp": IMG_001, "kr": None, "en": None},
        "catalogKeys": {"jp": 41664, "kr": None, "en": None},
        "seed": {"basePrice": 500, "basePop": 25},
    },
    {
        "id": "s8a-g-002",
        "packId": PACK_ID,
        "nameKo": "몬스터볼",
        "nameEn": "Monster Ball",
        "nameJa": "モンスターボール",
        "number": "002/015",
        "rarity": "PROMO",
        "type": "trainer",
        "typeKo": None,
        "holoStyle": "holo",
        "image": IMG_002,
        "images": {"jp": IMG_002, "kr": None, "en": None},
        "catalogKeys": {"jp": 41665, "kr": None, "en": None},
        "seed": {"basePrice": 120, "basePop": 30},
    },
]

PACK = {
    "id": PACK_ID,
    "nameKo": "25주년 애니버서리 골든 박스",
    "nameEn": "25th Anniversary Golden Box",
    "nameJa": "25th ANNIVERSARY GOLDEN BOX",
    "nameShort": "Golden BOX",
    "code": "S8a-G",
    "releaseYear": 2021,
    "listGroup": "box",
    "listComplete": True,
    "expectedCards": 2,
    "languages": ["jp"],
    "blurb": "25주년 골든 박스 · 금색 피카츄V·몬스터볼 전용 카드 2종.",
    "blurbEn": "25th Anniversary Golden Box · exclusive gold Pikachu V & Monster Ball.",
    "blurbJa": "25th ANNIVERSARY GOLDEN BOXの金色「ピカチュウV」「モンスターボール」。",
    "packImage": f"./assets/{PACK_IMAGE_NAME}",
    "coverCardId": "s8a-g-001",
    "brgSets": {
        "jp": {"setName": "POKEMON SWSH JAPANESE S8AG", "year": 2021},
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
                "cardNames": [c["nameEn"] for c in CARDS],
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
