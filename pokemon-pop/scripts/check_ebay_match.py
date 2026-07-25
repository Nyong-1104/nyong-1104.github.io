# -*- coding: utf-8 -*-
"""Dry-run assertions for eBay listing ↔ catalog card matching."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from ebay_prices import (  # noqa: E402
    grades_from_listings,
    listing_matches_card,
)

MG_CARD = {
    "id": "mg-festa-040",
    "nameEn": "Magikarp",
    "number": "040/M-P",
    "rarity": "PROMO",
}
MG_PACK = {
    "id": "mg-festa-seoul-stamp",
    "nameShort": "MG Festa Seoul",
    "nameEn": "MG Festa Pokémon GO Seoul Stamp Rally",
    "code": "MG-PROMO",
    "listGroup": "promo",
}

SV1A_CARD = {
    "id": "sv1a-080",
    "nameEn": "Magikarp",
    "number": "080/073",
    "rarity": "AR",
}
SV1A_PACK = {
    "id": "sv1a-triplet-beat",
    "nameShort": "Triplet Beat",
    "nameEn": "Triplet Beat",
    "code": "SV1a",
    "listGroup": "main",
}


def main() -> int:
    sv1a_title = (
        "PSA 10 Magikarp 080/073 Korean SV1a Triplet Beat Art Rare Pokemon"
    )
    festa_title = (
        "PSA 10 Magikarp 040/M-P Korean MG Festa Seoul Stamp Rally Promo"
    )
    loose_title = "PSA 10 Magikarp Korean Pokemon Card"
    normal_title = "PSA 10 Charizard 015/165 Japanese SV2a Pokemon"

    assert listing_matches_card(sv1a_title, MG_CARD, MG_PACK) is False, (
        "SV1a #080 Magikarp must not match MG Festa 040"
    )
    assert listing_matches_card(festa_title, MG_CARD, MG_PACK) is True, (
        "040/M-P Mega Festa Magikarp should match"
    )
    assert listing_matches_card(loose_title, MG_CARD, MG_PACK) is False, (
        "name+PSA+Korean alone must not match promo"
    )
    assert listing_matches_card(sv1a_title, SV1A_CARD, SV1A_PACK) is True, (
        "SV1a listing should still match SV1a Magikarp 080/073"
    )
    assert listing_matches_card(festa_title, SV1A_CARD, SV1A_PACK) is False

    # Bucket filter: wrong listings contribute no PSA 10 prices
    items = [
        {"title": sv1a_title, "price": {"value": "399.00", "currency": "USD"}},
        {"title": loose_title, "price": {"value": "200.00", "currency": "USD"}},
    ]
    buckets = grades_from_listings(items, MG_CARD, MG_PACK)
    assert buckets["10"] == [], f"expected empty PSA 10 bucket, got {buckets['10']}"

    ok_items = [
        {"title": festa_title, "price": {"value": "120.00", "currency": "USD"}},
    ]
    ok_buckets = grades_from_listings(ok_items, MG_CARD, MG_PACK)
    assert ok_buckets["10"] == [120.0], ok_buckets

    # Normal set: number+set still works without promo strictness
    sv2a_card = {"nameEn": "Charizard", "number": "015/165", "rarity": "RR"}
    sv2a_pack = {
        "nameShort": "151",
        "code": "SV2a",
        "listGroup": "main",
    }
    assert listing_matches_card(normal_title, sv2a_card, sv2a_pack) is True

    print("check_ebay_match: all assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
