# -*- coding: utf-8 -*-
"""Merge official-site secret rares (incl. MUR) into catalog/packs/live.

PTCG-database only has base numbers for M1L/M1S (001-063). Secret rares
(064+) live on pokemon-card.com — import from data/_tmp/mur_scan.json
(and optional extras).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
KST = timezone(timedelta(hours=9))

sys.path.insert(0, str(SCRIPTS))
from fix_korean_names import EXTRA_MAP  # noqa: E402
from pokepop_snapshot import (  # noqa: E402
    assign_tiers_to_catalog,
    build_live_snapshot,
    ensure_card_tier,
    write_data_bundle,
)
from brg_pop import restore_brg_pops  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402
from ebay_prices import restore_ebay_prices  # noqa: E402

SET_TO_PACK = {
    "M1L": ("m1l-mega-brave", "m1l"),
    "M1S": ("m1s-mega-symphonia", "m1s"),
    "M2": ("m2-inferno-x", "m2"),
    "M2a": ("m2a-mega-dream-ex", "m2a"),
    "M3": ("m3-nihil-zero", "m3"),
    "M4": ("m4-ninja-spinner", "m4"),
    "M5": ("m5-abyss-eye", "m5"),
}

RARITY_MAP = {
    "rare_c_c": "C",
    "c_c": "C",
    "rare_u_c": "U",
    "u_c": "U",
    "rare_r_c": "R",
    "r_c": "R",
    "rare_rr": "RR",
    "rr": "RR",
    "rare_sr_c": "SR",
    "sr_c": "SR",
    "sr": "SR",
    "rare_ar": "AR",
    "ar": "AR",
    "rare_sar": "SAR",
    "sar": "SAR",
    "rare_ur_c": "UR",
    "ur_c": "UR",
    "ur": "UR",
    "rare_hr": "HR",
    "hr": "HR",
    "rare_mur": "MUR",
    "mur": "MUR",
    "MUR": "MUR",
}

SEED_BY_RARITY = {
    "MUR": (320, 80),
    "SAR": (220, 900),
    "SR": (95, 420),
    "AR": (35, 2400),
    "UR": (90, 280),
    "RR": (45, 520),
}

TYPE_FROM_NAME = {
    "ルカリオ": ("fighting", "격투"),
    "サーナイト": ("psychic", "초"),
    "リザードン": ("fire", "불"),
    "カイリュー": ("dragon", "드래곤"),
    "ゲッコウガ": ("water", "물"),
    "ジガルデ": ("dragon", "드래곤"),
    "ダークライ": ("darkness", "악"),
}


def map_rarity(raw: str | None) -> str:
    if not raw:
        return "C"
    if raw in RARITY_MAP:
        return RARITY_MAP[raw]
    up = raw.upper()
    if up in RARITY_MAP:
        return RARITY_MAP[up]
    cleaned = up.replace("RARE_", "")
    return RARITY_MAP.get(cleaned, cleaned[:6] or "C")


def holo_for(rarity: str) -> str:
    if rarity in {"MUR", "SAR", "SIR", "BWR"}:
        return "sar"
    if rarity == "AR":
        return "reverse"
    if rarity in {"SR", "HR", "UR", "RR"}:
        return "holo"
    return "reverse"


def guess_type(name_ja: str) -> tuple[str, str]:
    for key, typ in TYPE_FROM_NAME.items():
        if key in name_ja:
            return typ
    return "colorless", "무색"


def localize(name_ja: str) -> tuple[str, str]:
    raw = (name_ja or "").strip()
    if raw in EXTRA_MAP:
        ko, en = EXTRA_MAP[raw]
        return ko, en
    # strip mega prefix for lookup
    base = raw
    mega = False
    if base.startswith("メガ"):
        mega = True
        base = base[2:]
    # try without ex
    key = base
    suffix_ko = ""
    suffix_en = ""
    if key.endswith("ex"):
        key = key[:-2]
        suffix_ko = " ex"
        suffix_en = " ex"
    if raw in EXTRA_MAP:
        ko, en = EXTRA_MAP[raw]
        return ko, en
    if key in EXTRA_MAP:
        ko, en = EXTRA_MAP[key]
    elif f"メガ{key}ex" in EXTRA_MAP:
        return EXTRA_MAP[f"メガ{key}ex"]
    else:
        # fallback: use JP as display
        ko, en = key, key
    if mega:
        ko = f"메가 {ko}"
        en = f"Mega {en}"
    return ko + suffix_ko, en + suffix_en


def to_card(row: dict, pack_id: str, id_prefix: str) -> dict | None:
    num_full = row.get("number") or ""
    coll = str(row.get("collector") or num_full.split("/")[0]).zfill(3)
    rarity = map_rarity(row.get("rarity"))
    name_ja = row.get("name") or ""
    name_ko, name_en = localize(name_ja)
    typ, typ_ko = guess_type(name_ja)
    seed_price, seed_pop = SEED_BY_RARITY.get(rarity, (40, 200))
    card = {
        "id": f"{id_prefix}-{coll}",
        "packId": pack_id,
        "nameKo": name_ko,
        "nameEn": name_en,
        "nameJa": name_ja,
        "number": num_full,
        "rarity": rarity,
        "type": typ,
        "typeKo": typ_ko,
        "holoStyle": holo_for(rarity),
        "image": row.get("img"),
        "images": {
            "jp": row.get("img"),
            "kr": None,
            "en": row.get("img"),
        },
        "catalogKeys": {"jp": row.get("jp_id"), "kr": None, "en": None},
        "seed": {"basePrice": seed_price, "basePop": seed_pop},
    }
    ensure_card_tier(card)
    return card


def load_scans() -> list[dict]:
    rows: list[dict] = []
    tmp = DATA / "_tmp"
    for name in ("mur_scan.json", "mur_extra.json"):
        path = tmp / name
        if path.is_file():
            rows.extend(json.loads(path.read_text(encoding="utf-8")))
    # de-dupe by jp_id
    by_id = {}
    for r in rows:
        by_id[r["jp_id"]] = r
    return list(by_id.values())


def main() -> int:
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    packs_by_id = {p["id"]: p for p in packs}
    existing_ids = {c["id"] for c in catalog}
    existing_jp = {
        (c.get("catalogKeys") or {}).get("jp")
        for c in catalog
        if (c.get("catalogKeys") or {}).get("jp")
    }

    added = []
    skipped_pack = []
    for row in load_scans():
        set_name = row.get("set_name")
        mapping = SET_TO_PACK.get(set_name)
        if not mapping:
            skipped_pack.append(row)
            continue
        pack_id, id_prefix = mapping
        if pack_id not in packs_by_id:
            skipped_pack.append(row)
            continue
        if row.get("jp_id") in existing_jp:
            continue
        card = to_card(row, pack_id, id_prefix)
        if not card or card["id"] in existing_ids:
            # number collision — suffix with rarity
            card["id"] = f"{id_prefix}-{str(row['collector']).zfill(3)}-{card['rarity'].lower()}"
        if card["id"] in existing_ids:
            continue
        catalog.append(card)
        existing_ids.add(card["id"])
        existing_jp.add(row.get("jp_id"))
        pack = packs_by_id[pack_id]
        ids = pack.setdefault("cardIds", [])
        if card["id"] not in ids:
            ids.append(card["id"])
        added.append(
            {
                "id": card["id"],
                "rarity": card["rarity"],
                "nameEn": card["nameEn"],
                "packId": pack_id,
                "number": card["number"],
            }
        )

    assign_tiers_to_catalog(catalog)
    asof = datetime.now(KST).isoformat(timespec="seconds")
    live_path = DATA / "live" / "pop-price.json"
    previous = json.loads(live_path.read_text(encoding="utf-8")) if live_path.exists() else {}
    live, stats = build_live_snapshot(catalog, packs, asof, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or live.get("source") or "seed"
    if "PSA" not in str(live["source"]) and any(
        ((v.get("pop") or {}).get("PSA") or {}).get("source") == "gemrate"
        for variants in (live.get("cards") or {}).values()
        for v in variants.values()
    ):
        src = live["source"]
        live["source"] = f"{src}+PSA" if src != "seed" else "seed+PSA"
    live["generatedAt"] = asof
    last_run = {"ranAt": asof, "stats": {"secretRaresAdded": added, **stats}}
    write_data_bundle(DATA, packs, catalog, live, last_run)

    mur = [a for a in added if a["rarity"] == "MUR"]
    print(
        json.dumps(
            {
                "added": len(added),
                "mur": mur,
                "addedSample": added[:15],
                "skippedUnknownSet": len(skipped_pack),
                "liveCards": stats.get("cardsLive"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
