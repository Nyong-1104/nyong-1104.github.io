# -*- coding: utf-8 -*-
"""Shared POP/price snapshot helpers for PokePop."""
import hashlib
import json
from pathlib import Path


def seed_int(key: str) -> int:
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


def full_pop(key: str, base_pop10: int, lang: str) -> dict:
    """POP shell. BRG is filled later from break.co.kr; other graders stay empty until wired."""
    _ = (key, base_pop10, lang)  # reserved for future seed/live sources
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
    """Placeholder PSA-grade prices (seed). Overridden by eBay when credentials are set."""
    s = seed_int(f"{key}-{lang}")
    mult = 0.42 if lang == "kr" else 1.0 if lang == "jp" else 0.95
    p10 = max(8, int(base_price * mult * (0.85 + (s % 30) / 100)))
    p9 = max(5, int(p10 * (0.42 + (s % 18) / 100)))
    p8 = max(3, int(p10 * (0.18 + (s % 12) / 100)))
    return {
        "source": "seed",
        "currency": "USD",
        "asOf": asof_iso[:10],
        "grades": {"10": p10, "9": p9, "8": p8},
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
    return out


def build_live_snapshot(catalog, packs, asof_iso: str, previous=None):
    """Build live POP/price data for every catalog card."""
    previous = previous or {}
    prev_cards = previous.get("cards") or {}
    packs_by_id = {p["id"]: p for p in packs}

    live_cards = {}
    stats = {
        "asOf": asof_iso[:10],
        "asOfIso": asof_iso,
        "cardsTotal": len(catalog),
        "cardsLive": 0,
        "variantsWritten": 0,
        "variantsKept": 0,
        "variantsFailed": 0,
    }

    for card in catalog:
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
