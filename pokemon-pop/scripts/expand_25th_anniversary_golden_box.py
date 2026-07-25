# -*- coding: utf-8 -*-
"""Expand 25th Anniversary Golden Box with full S8a-G deck card list."""
from __future__ import annotations

import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_catalog import (  # noqa: E402
    build_ja_dex_index,
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
PACK_ID = "25th-anniversary-golden-box"
UA = {"User-Agent": "PokePopCatalogBuilder/1.0"}
RAW = "https://raw.githubusercontent.com/type-null/PTCG-database/main/data_jp/S8a-G"
API = "https://api.github.com/repos/type-null/PTCG-database/contents/data_jp/S8a-G"

# JP → (KO, EN) for trainers / energy not covered by dex lookup
NAME_OVERRIDES: dict[str, tuple[str, str]] = {
    "モンスターボール": ("몬스터볼", "Monster Ball"),
    "きずぐすり": ("상처약", "Potion"),
    "スーパーボール": ("슈퍼볼", "Great Ball"),
    "ポケモンいれかえ": ("포켓몬 교체", "Switch"),
    "ポケモンキャッチャー": ("포켓몬 캐처", "Pokémon Catcher"),
    "博士の研究（マグノリア博士）": (
        "박사의 연구（마그놀리아 박사）",
        "Professor's Research (Professor Magnolia)",
    ),
    "ビート": ("비트", "Bede"),
    "ポケモンごっこ": ("포켓몬 흉내", "Poké Kid"),
    "ホップ": ("호프", "Hop"),
    "基本雷エネルギー": ("기본 번개 에너지", "Basic Lightning Energy"),
}

# Preserve higher seed prices for the gold exclusives
GOLD_SEEDS = {
    "s8a-g-001": {"basePrice": 500, "basePop": 25},
    "s8a-g-002": {"basePrice": 120, "basePop": 30},
}


def http_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sort_key(card: dict):
    raw = str(card.get("number") or "").split("/")[0].strip()
    try:
        return (0, int(raw))
    except ValueError:
        return (1, raw)


def fetch_s8a_g() -> list[dict]:
    cache_dir = DATA / "_tmp" / "jp_cards" / "S8a-G"
    cache_dir.mkdir(parents=True, exist_ok=True)
    items = http_json(API)
    ids = [int(x["name"].replace(".json", "")) for x in items if x["name"].endswith(".json")]

    cards: list[dict] = []

    def load_one(jid: int) -> dict:
        local = cache_dir / f"{jid}.json"
        if local.exists():
            return json.loads(local.read_text(encoding="utf-8"))
        data = http_json(f"{RAW}/{jid}.json")
        local.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    with ThreadPoolExecutor(max_workers=24) as ex:
        futs = [ex.submit(load_one, jid) for jid in ids]
        for fut in as_completed(futs):
            cards.append(fut.result())
    cards.sort(key=sort_key)
    return cards


def card_id_num(card: dict) -> str:
    raw = str(card.get("number") or "").split("/")[0].strip()
    if raw.isdigit():
        return raw.zfill(3)
    return raw.lower()


def number_display_safe(card: dict) -> str:
    raw = str(card.get("number") or "").strip()
    if "/" in raw:
        return raw
    left = raw.split("/")[0].strip()
    total = card.get("set_total")
    if isinstance(total, int) and total > 0:
        return f"{left.zfill(3)}/{str(total).zfill(3)}"
    if isinstance(total, str) and total.isdigit() and int(total) > 0:
        return f"{left.zfill(3)}/{total.zfill(3)}"
    if left.isdigit():
        return f"{left.zfill(3)}/015"
    return left


def build_cards(ko_names, en_names, ja_index) -> list[dict]:
    pack_ctx = {"id": PACK_ID, "idPrefix": "s8a-g", "sourceFolder": "S8a-G"}
    out: list[dict] = []
    for raw in fetch_s8a_g():
        # Temporarily normalize numeric numbers so to_catalog_card ids stay padded;
        # LIG needs a custom path because set_total is -1 and number is non-numeric.
        num_key = card_id_num(raw)
        if num_key == "lig":
            img = raw.get("img") or ""
            card = {
                "id": "s8a-g-lig",
                "packId": PACK_ID,
                "nameKo": NAME_OVERRIDES["基本雷エネルギー"][0],
                "nameEn": NAME_OVERRIDES["基本雷エネルギー"][1],
                "nameJa": raw.get("name") or "基本雷エネルギー",
                "number": "LIG",
                "rarity": "PROMO",
                "type": "lightning",
                "typeKo": "번개",
                "holoStyle": "holo",
                "image": img,
                "images": {"jp": img, "kr": None, "en": None},
                "catalogKeys": {"jp": raw.get("jp_id"), "kr": None, "en": None},
                "seed": {"basePrice": 8, "basePop": 80},
            }
        else:
            # Ensure padded number for id generation
            patched = dict(raw)
            patched["number"] = str(raw.get("number") or "").split("/")[0].zfill(3)
            if not patched.get("set_total") or patched.get("set_total") in (-1, "-1"):
                patched["set_total"] = "015"
            card = to_catalog_card(patched, pack_ctx, ko_names, en_names, ja_index)
            card["number"] = number_display_safe(raw)
            card["rarity"] = "PROMO"
            card["holoStyle"] = "holo"
            jp_name = card.get("nameJa") or ""
            if jp_name in NAME_OVERRIDES:
                card["nameKo"], card["nameEn"] = NAME_OVERRIDES[jp_name]
            # Energy-like / trainer type fix when PTCG omits types
            if "エネルギー" in jp_name:
                card["type"] = "lightning"
                card["typeKo"] = "번개"
            if card["id"] in GOLD_SEEDS:
                card["seed"] = dict(GOLD_SEEDS[card["id"]])
            elif card["id"] in {"s8a-g-005", "s8a-g-006"}:
                # Playable Pikachu V / VMAX in the constructed deck
                card["seed"] = {
                    "basePrice": 25 if card["id"].endswith("005") else 40,
                    "basePop": 50,
                }
        out.append(card)
    return out


def main() -> int:
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))

    print("Loading species lists…")
    ko_names = load_species_names("ko")
    en_names = load_species_names("en")
    ja_names = load_species_names("ja")
    ja_index = build_ja_dex_index(ja_names)

    print("Fetching S8a-G…")
    cards = build_cards(ko_names, en_names, ja_index)
    # Preserve prior tier/seed overlays for existing gold cards if present
    prev_by_id = {c["id"]: c for c in catalog if c.get("packId") == PACK_ID}
    for c in cards:
        prev = prev_by_id.get(c["id"])
        if prev:
            if prev.get("tier"):
                c["tier"] = prev["tier"]
            if prev.get("seed") and c["id"] in GOLD_SEEDS:
                c["seed"] = prev["seed"]

    card_ids = [c["id"] for c in cards]
    packs = [p for p in packs if p.get("id") != PACK_ID]
    catalog = [c for c in catalog if c.get("packId") != PACK_ID]

    pack = {
        "id": PACK_ID,
        "nameKo": "25주년 애니버서리 골든 박스",
        "nameEn": "25th Anniversary Golden Box",
        "nameJa": "25th ANNIVERSARY GOLDEN BOX",
        "nameShort": "Golden BOX",
        "code": "S8a-G",
        "releaseYear": 2021,
        "listGroup": "box",
        "listComplete": True,
        "expectedCards": len(cards),
        "languages": ["jp"],
        "blurb": "25주년 골든 박스 · 금색 피카츄V·몬스터볼 + 고정 홀로 피카츄 덱(S8a-G) 전 카드.",
        "blurbEn": "25th Anniversary Golden Box · gold Pikachu V & Monster Ball plus the fixed holo Pikachu deck (S8a-G).",
        "blurbJa": "25th ANNIVERSARY GOLDEN BOXの金色「ピカチュウV」「モンスターボール」と特製ピカチュウデッキ全カード。",
        "packImage": "./assets/box-25th-anniversary-golden.png",
        "coverCardId": "s8a-g-001",
        "brgSets": {
            "jp": {"setName": "POKEMON SWSH JAPANESE S8AG", "year": 2021},
        },
        "cardIds": card_ids,
    }
    packs.append(pack)
    catalog.extend(cards)

    asof = datetime.now(KST).isoformat(timespec="seconds")
    previous = load_previous_live(DATA)
    live, stats = build_live_snapshot(catalog, packs, asof, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or live.get("source") or "seed"
    live["generatedAt"] = asof
    keep_ids = {c["id"] for c in catalog}
    live["cards"] = {k: v for k, v in (live.get("cards") or {}).items() if k in keep_ids}

    last_run = {
        "ranAt": asof,
        "stats": {
            **stats,
            "expandedPack": PACK_ID,
            "cardCount": len(cards),
            "cardIds": card_ids,
        },
    }
    (DATA / "live" / "last-run.json").write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_data_bundle(DATA, packs, catalog, live, last_run)

    summary = [
        {
            "id": c["id"],
            "number": c["number"],
            "nameKo": c["nameKo"],
            "nameEn": c["nameEn"],
            "nameJa": c["nameJa"],
        }
        for c in cards
    ]
    out = DATA / "_tmp" / "golden_box_expand_result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"packId": PACK_ID, "count": len(cards), "cards": summary, **stats},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out} count={len(cards)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
