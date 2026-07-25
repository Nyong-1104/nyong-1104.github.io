# -*- coding: utf-8 -*-
"""Add VSTAR Universe, Tag All Stars, VMAX Rising, Ultra Force, Storm Emerald packs."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_catalog import (  # noqa: E402
    attach_multilang_images,
    build_ja_dex_index,
    fetch_jp_cards,
    load_species_names,
    to_catalog_card,
)
from brg_pop import restore_brg_pops  # noqa: E402
from ebay_prices import restore_ebay_prices  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402
from pokepop_snapshot import (  # noqa: E402
    build_live_snapshot,
    load_previous_live,
    write_data_bundle,
)

KST = timezone(timedelta(hours=9))
CURSOR_ASSETS = Path(
    r"C:\Users\admin\.cursor\projects\c-Users-admin-Projects-nyong-1104-github-io\assets"
)

# (dest_asset, source_glob_substring)
IMAGE_MAP = [
    (
        "pack-s12a.png",
        "_____VSTAR______JP-fd29f7a2-a74b-4c61-a452-b7ea3b660244.png",
    ),
    (
        "pack-sm12a.png",
        "_____TAG_TEAM_GX__________JP-e22fae90-e8a6-4ea9-950a-814dce764583.png",
    ),
    (
        "pack-s1a.png",
        "_____VMAX_____JP-a83a4b78-aa89-42fa-989c-f4b36ef53086.png",
    ),
    (
        "pack-sm5p.png",
        "___________JP-882fed7d-0062-490b-a2ce-50c2806800ed.png",
    ),
    (
        "pack-m6.png",
        "____________JP-755d74a9-5e86-4e6a-953b-054e6b0b83a3.png",
    ),
]

NEW_PACKS = [
    {
        "id": "s12a-vstar-universe",
        "nameKo": "VSTAR 유니버스",
        "nameEn": "VSTAR Universe",
        "nameJa": "VSTARユニバース",
        "code": "S12a",
        "releaseYear": 2022,
        "languages": ["jp", "kr"],
        "blurb": "소드&실드 하이클래스 팩. V·VMAX·VSTAR가 확정 수록됩니다.",
        "blurbEn": "Sword & Shield high-class pack with a guaranteed V / VMAX / VSTAR.",
        "blurbJa": "ソード&シールドのハイクラスパック。V・VMAX・VSTARのいずれかが確定です。",
        "packImage": "./assets/pack-s12a.png",
        "sourceFolder": "S12a",
        "idPrefix": "s12a",
        "listComplete": True,
        "listGroup": "booster",
    },
    {
        "id": "sm12a-tag-all-stars",
        "nameKo": "GX 태그 올스타즈",
        "nameEn": "GX Tag All Stars",
        "nameJa": "GX タッグオールスターズ",
        "code": "SM12a",
        "releaseYear": 2019,
        "languages": ["jp", "kr"],
        "blurb": "썬&문 하이클래스 팩. TAG TEAM GX가 중심인 올스타 세트입니다.",
        "blurbEn": "Sun & Moon high-class pack starring TAG TEAM GX cards.",
        "blurbJa": "サン&ムーンのハイクラスパック。TAG TEAM GXが中心のオールスターセットです。",
        "packImage": "./assets/pack-sm12a.png",
        "sourceFolder": "SM12a",
        "idPrefix": "sm12a",
        "listComplete": True,
        "listGroup": "booster",
    },
    {
        "id": "s1a-vmax-rising",
        "nameKo": "VMAX 라이징",
        "nameEn": "VMAX Rising",
        "nameJa": "VMAXライジング",
        "code": "S1a",
        "releaseYear": 2019,
        "languages": ["jp", "kr"],
        "blurb": "소드&실드 초기 강화 확장팩. 거다이맥스와 VMAX가 등장합니다.",
        "blurbEn": "Early Sword & Shield subset introducing VMAX and Gigantamax stars.",
        "blurbJa": "ソード&シールド初期の強化拡張パック。ダイマックスとVMAXが登場します。",
        "packImage": "./assets/pack-s1a.png",
        "sourceFolder": "S1a",
        "idPrefix": "s1a",
        "listComplete": True,
        "listGroup": "booster",
    },
    {
        "id": "sm5p-ultra-force",
        "nameKo": "울트라 포스",
        "nameEn": "Ultra Force",
        "nameJa": "ウルトラフォース",
        "code": "SM5+",
        "releaseYear": 2018,
        "languages": ["jp", "kr"],
        "blurb": "울트라비스트와 네크로즈마가 중심인 썬&문 강화 확장팩입니다.",
        "blurbEn": "Sun & Moon subset focused on Ultra Beasts and Necrozma.",
        "blurbJa": "ウルトラビーストとネクロズマが中心のサン&ムーン強化拡張パックです。",
        "packImage": "./assets/pack-sm5p.png",
        "sourceFolder": "SM5p",
        "idPrefix": "sm5p",
        "listComplete": True,
        "listGroup": "booster",
    },
    {
        "id": "m6-storm-emerald",
        "nameKo": "스톰 에메랄드",
        "nameEn": "Storm Emerald",
        "nameJa": "ストームエメラルド",
        "code": "M6",
        "releaseYear": 2026,
        "languages": ["jp", "kr"],
        "blurb": "메가레쿠쟈가 상징하는 MEGA 확장팩. 카드 목록은 출시 후 추가 예정입니다.",
        "blurbEn": "MEGA expansion featuring Mega Rayquaza. Card list coming after release.",
        "blurbJa": "メガレックウザが象徴のMEGA拡張パック。カードリストは発売後に追加予定です。",
        "packImage": "./assets/pack-m6.png",
        "sourceFolder": None,
        "idPrefix": "m6",
        "listComplete": False,
        "listGroup": "booster",
        "stubOnly": True,
    },
]


def copy_pack_images() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for dest_name, src_name in IMAGE_MAP:
        src = CURSOR_ASSETS / src_name
        dest = ASSETS / dest_name
        if not src.exists():
            # fallback: fuzzy match
            hits = list(CURSOR_ASSETS.glob(f"*{src_name.split('-')[-1]}"))
            if not hits:
                raise SystemExit(f"missing pack art: {src_name}")
            src = hits[0]
        shutil.copy2(src, dest)
        # optional: leave art as-is (full pack photos, don't punch black)
        print(f"copied {src.name} -> {dest.name} ({dest.stat().st_size} bytes)")


def build_cards(meta: dict, ko_names, en_names, ja_index) -> list[dict]:
    if meta.get("stubOnly") or not meta.get("sourceFolder"):
        return []
    pack_ctx = {
        "id": meta["id"],
        "idPrefix": meta["idPrefix"],
        "sourceFolder": meta["sourceFolder"],
    }
    jp_cards = fetch_jp_cards(meta["sourceFolder"])
    return [to_catalog_card(c, pack_ctx, ko_names, en_names, ja_index) for c in jp_cards]


def main() -> int:
    copy_pack_images()

    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))

    print("Loading species lists…")
    ko_names = load_species_names("ko")
    en_names = load_species_names("en")
    ja_names = load_species_names("ja")
    ja_index = build_ja_dex_index(ja_names)

    new_ids = {m["id"] for m in NEW_PACKS}
    packs = [p for p in packs if p.get("id") not in new_ids]
    catalog = [c for c in catalog if c.get("packId") not in new_ids]

    summary = []
    for meta in NEW_PACKS:
        print(f"Building {meta['id']}…")
        cards = build_cards(meta, ko_names, en_names, ja_index)
        attach_multilang_images(cards)
        for c in cards:
            images = c.setdefault("images", {})
            images["jp"] = images.get("jp") or c.get("image")
            # don't invent KR/EN for older sets without maps
            if "kr" not in images:
                images["kr"] = None
            if "en" not in images:
                images["en"] = None

        pack_row = {
            "id": meta["id"],
            "nameKo": meta["nameKo"],
            "nameEn": meta["nameEn"],
            "nameJa": meta["nameJa"],
            "code": meta["code"],
            "releaseYear": meta["releaseYear"],
            "listGroup": meta.get("listGroup", "booster"),
            "listComplete": bool(meta.get("listComplete")) and bool(cards),
            "languages": meta["languages"],
            "blurb": meta["blurb"],
            "blurbEn": meta["blurbEn"],
            "blurbJa": meta["blurbJa"],
            "packImage": meta["packImage"],
            "coverCardId": cards[0]["id"] if cards else None,
            "cardIds": [c["id"] for c in cards],
        }
        if meta.get("stubOnly"):
            pack_row["listComplete"] = False
        packs.append(pack_row)
        catalog.extend(cards)
        summary.append({"id": meta["id"], "cards": len(cards)})
        print(f"  → {len(cards)} cards")

    asof = datetime.now(KST).isoformat(timespec="seconds")
    previous = load_previous_live(DATA)
    live, stats = build_live_snapshot(catalog, packs, asof, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or live.get("source") or "seed"
    live["generatedAt"] = asof

    last_run = {"ranAt": asof, "stats": {**stats, "addedPacks": summary}}
    (DATA / "live" / "last-run.json").write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_data_bundle(DATA, packs, catalog, live, last_run)
    print(json.dumps({"addedPacks": summary, **stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
