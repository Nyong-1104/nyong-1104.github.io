# -*- coding: utf-8 -*-
"""Shared POP/price snapshot helpers for PokePop."""
import hashlib
import json
from pathlib import Path

TIER_A = {"SAR", "SIR", "HR", "UR", "SR"}
TIER_B = {"AR", "RR", "PRISM", "R"}


def seed_int(key: str) -> int:
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


def tier_for_rarity(rarity: str) -> str:
    if rarity in TIER_A:
        return "A"
    if rarity in TIER_B:
        return "B"
    return "C"


def full_pop(key: str, base_pop10: int, lang: str) -> dict:
    s = seed_int(f"{key}-{lang}")
    mult = 0.42 if lang == "kr" else 1.0
    p10 = max(3, int(base_pop10 * mult * (0.7 + (s % 40) / 100)))
    p9 = int(p10 * (0.6 + (s % 20) / 100))
    p8 = int(p10 * (0.15 + (s % 15) / 100))
    total = p10 + p9 + p8 + (s % 40)
    bgs10 = max(0, p10 // 18)
    cgc10 = max(0, p10 // 12)
    return {
        "PSA": {"10": p10, "9": p9, "8": p8, "total": total},
        "BGS": {
            "10": bgs10,
            "9.5": bgs10 * 3 + 2,
            "9": bgs10 * 2,
            "total": bgs10 * 6 + 8,
        }
        if bgs10 or lang == "jp"
        else None,
        "CGC": {
            "10": cgc10,
            "9.5": cgc10 + 4,
            "9": max(1, cgc10 // 2),
            "total": cgc10 * 3 + 10,
        },
        "BRG": None,
        "TAG": {"10": max(0, p10 // 80), "9": max(0, p10 // 50), "total": max(0, p10 // 30)}
        if lang == "jp"
        else None,
        "ACE": None,
        "AGS": {"10": max(0, p10 // 120), "9": max(0, p10 // 80), "total": max(0, p10 // 50)}
        if lang == "jp" and p10 > 100
        else None,
    }


def price_snapshot(key: str, base_price: int, lang: str, asof_iso: str) -> dict:
    s = seed_int(f"{key}-{lang}")
    mult = 0.42 if lang == "kr" else 1.0 if lang == "jp" else 0.95
    amount = max(8, int(base_price * mult * (0.85 + (s % 30) / 100)))
    return {
        "source": "PSA",
        "grade": "10",
        "amount": amount,
        "currency": "USD",
        "asOf": asof_iso[:10],
    }


def live_variant(card_id: str, tier: str, base_price: int, base_pop: int, lang: str, asof_iso: str):
    if tier == "C":
        return None
    if tier == "B":
        return {
            "price": price_snapshot(card_id, base_price, lang, asof_iso),
            "pop": None,
            "updatedAt": asof_iso,
        }
    return {
        "price": price_snapshot(card_id, base_price, lang, asof_iso),
        "pop": full_pop(card_id, base_pop, lang),
        "updatedAt": asof_iso,
    }


def finalize_catalog_card(card: dict) -> dict:
    out = {k: v for k, v in card.items() if k != "_seed"}
    if "_seed" in card:
        out["seed"] = card["_seed"]
    return out


def build_live_snapshot(catalog, packs, asof_iso: str, previous=None):
    """Build live POP/price data. Tier C cards are omitted."""
    previous = previous or {}
    prev_cards = previous.get("cards") or {}
    packs_by_id = {p["id"]: p for p in packs}

    live_cards = {}
    stats = {
        "asOf": asof_iso[:10],
        "asOfIso": asof_iso,
        "cardsTotal": len(catalog),
        "cardsLive": 0,
        "skippedTierC": 0,
        "variantsWritten": 0,
        "variantsKept": 0,
        "variantsFailed": 0,
    }

    for card in catalog:
        tier = card.get("tier", "C")
        if tier == "C":
            stats["skippedTierC"] += 1
            continue

        pack = packs_by_id.get(card["packId"])
        if not pack:
            continue

        seed = card.get("seed") or {}
        base_price = int(seed.get("basePrice", 50))
        base_pop = int(seed.get("basePop", 100))
        prev_card = prev_cards.get(card["id"], {})

        variants = {}
        for lang in pack.get("languages", []):
            try:
                variant = live_variant(
                    card["id"],
                    tier,
                    base_price,
                    base_pop,
                    lang,
                    asof_iso,
                )
                if variant:
                    variants[lang] = variant
                    stats["variantsWritten"] += 1
            except Exception:
                if lang in prev_card:
                    variants[lang] = prev_card[lang]
                    stats["variantsKept"] += 1
                else:
                    stats["variantsFailed"] += 1

        if variants:
            live_cards[card["id"]] = variants
            stats["cardsLive"] += 1

    live = {
        "generatedAt": asof_iso,
        "source": "seed",
        "cards": live_cards,
    }
    return live, stats


def write_data_bundle(data_dir: Path, packs, catalog, live, last_run=None) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    live_dir = data_dir / "live"
    live_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "packs.json").write_text(
        json.dumps(packs, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (data_dir / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (live_dir / "pop-price.json").write_text(
        json.dumps(live, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    last_run_path = live_dir / "last-run.json"
    if last_run is None and last_run_path.exists():
        last_run = json.loads(last_run_path.read_text(encoding="utf-8"))

    data_js = (
        "window.POP_PACKS = "
        + json.dumps(packs, ensure_ascii=False, indent=2)
        + ";\nwindow.POP_CATALOG = "
        + json.dumps(catalog, ensure_ascii=False, indent=2)
        + ";\nwindow.POP_LIVE = "
        + json.dumps(live, ensure_ascii=False, indent=2)
        + ";\nwindow.POP_LAST_RUN = "
        + json.dumps(last_run or {}, ensure_ascii=False, indent=2)
        + ";\n"
    )
    (data_dir / "data.js").write_text(data_js, encoding="utf-8")
