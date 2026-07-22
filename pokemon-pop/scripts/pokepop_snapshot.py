# -*- coding: utf-8 -*-
"""Shared POP/price snapshot helpers for PokePop."""
import hashlib
import json
from pathlib import Path

TIER_A = {"SAR", "SIR", "HR", "UR", "SR", "AR", "SSR", "S_2", "RRR", "BWR"}
TIER_B = {"RR", "PRISM", "R", "PROMO"}
# U, C, and anything else → Tier C (catalog only)


def seed_int(key: str) -> int:
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


def tier_for_rarity(rarity: str | None) -> str:
    r = (rarity or "").strip().upper()
    if r in TIER_A:
        return "A"
    if r in TIER_B:
        return "B"
    return "C"


def ensure_card_tier(card: dict) -> str:
    tier = card.get("tier")
    if tier in ("A", "B", "C"):
        return tier
    tier = tier_for_rarity(card.get("rarity"))
    card["tier"] = tier
    return tier


def full_pop(key: str, base_pop10: int, lang: str) -> dict:
    """POP shell. BRG is filled later from break.co.kr; other graders stay empty until wired."""
    _ = (key, base_pop10, lang)
    return {
        "PSA": None,
        "BGS": None,
        "CGC": None,
        "BRG": None,
        "TAG": None,
        "ACE": None,
        "AGS": None,
    }


def price_snapshot(key: str, base_price: int, lang: str, asof_iso: str) -> dict:
    """Placeholder price shell. Real grades come from eBay when credentials are set.

    Seed amounts are intentionally omitted so the UI never shows fake prices.
    """
    _ = (key, base_price, lang)
    return {
        "source": "seed",
        "currency": "USD",
        "asOf": asof_iso[:10],
        "grades": {},
    }


def live_variant(card_id: str, base_price: int, base_pop: int, lang: str, asof_iso: str):
    return {
        "price": price_snapshot(card_id, base_price, lang, asof_iso),
        "pop": full_pop(card_id, base_pop, lang),
        "updatedAt": asof_iso,
    }


def finalize_catalog_card(card: dict) -> dict:
    out = {k: v for k, v in card.items() if k != "_seed"}
    if "_seed" in card:
        out["seed"] = card["_seed"]
    ensure_card_tier(out)
    return out


def build_live_snapshot(catalog, packs, asof_iso: str, previous=None):
    """Build live POP/price data for Tier A/B cards only (Tier C = catalog only)."""
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
        tier = ensure_card_tier(card)
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
                variants[lang] = live_variant(
                    card["id"],
                    base_price,
                    base_pop,
                    lang,
                    asof_iso,
                )
                # Keep prior eBay/BRG if restore helpers miss a path
                prev_variant = prev_card.get(lang) or {}
                prev_price = prev_variant.get("price") or {}
                if prev_price.get("source") == "eBay" and prev_price.get("grades"):
                    variants[lang]["price"] = prev_price
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


def assign_tiers_to_catalog(catalog: list[dict]) -> dict:
    counts = {"A": 0, "B": 0, "C": 0}
    for card in catalog:
        tier = ensure_card_tier(card)
        counts[tier] = counts.get(tier, 0) + 1
    return counts


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

    psa_sets_path = data_dir / "psa-sets.json"
    psa_sets = {}
    if psa_sets_path.exists():
        psa_sets = json.loads(psa_sets_path.read_text(encoding="utf-8"))

    data_js = (
        "window.POP_PACKS = "
        + json.dumps(packs, ensure_ascii=False, indent=2)
        + ";\nwindow.POP_CATALOG = "
        + json.dumps(catalog, ensure_ascii=False, indent=2)
        + ";\nwindow.POP_LIVE = "
        + json.dumps(live, ensure_ascii=False, indent=2)
        + ";\nwindow.POP_LAST_RUN = "
        + json.dumps(last_run or {}, ensure_ascii=False, indent=2)
        + ";\nwindow.POP_PSA_SETS = "
        + json.dumps(psa_sets, ensure_ascii=False, indent=2)
        + ";\n"
    )
    (data_dir / "data.js").write_text(data_js, encoding="utf-8")
