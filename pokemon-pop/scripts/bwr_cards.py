# -*- coding: utf-8 -*-
"""Explicit BWR (Black / White / Red special-finish) whitelist.

There is no general rarity rule — only these cards:
  - Black: Zekrom ex (Black Bolt 174/086) — JP/KR/EN
  - White: Reshiram ex (White Flare 174/086) — JP/KR/EN
  - Red: Victini SR (Red Collection 070/066) — legacy
  - EN-only: Victini BWR (Black Bolt EN 171/086) — not in JP/KR Black Bolt
"""

# cardId → optional field overrides applied on top of catalog rows
BWR_CARDS = {
    "sv11b-174": {
        "nameKo": "제크로무 ex",
        "nameEn": "Zekrom ex",
        "nameJa": "ゼクロムex",
        "number": "174/086",
        "packId": "sv11b-black-bolt",
    },
    "sv11w-174": {
        "nameKo": "레시라무 ex",
        "nameEn": "Reshiram ex",
        "nameJa": "レシラムex",
        "number": "174/086",
        "packId": "sv11w-white-flare",
    },
    "bw2-070": {
        "nameKo": "비크티니",
        "nameEn": "Victini",
        "nameJa": "ビクティニ",
        "number": "070/066",
        "packId": "bw2-red-collection",
        "type": "fire",
        "typeKo": "불",
        "image": "https://images.pokemontcg.io/bw2/70_hires.png",
        "images": {
            "jp": "https://images.pokemontcg.io/bw2/70_hires.png",
            "kr": None,
            "en": "https://images.pokemontcg.io/bw2/70_hires.png",
        },
    },
    # EN Black Bolt only (JP/KR #171 is a different SAR). Shown when edition=en.
    "sv11b-victini-bwr": {
        "nameKo": "비크티니",
        "nameEn": "Victini",
        "nameJa": "ビクティニ",
        "number": "171/086",
        "packId": "sv11b-black-bolt",
        "type": "fire",
        "typeKo": "불",
        "editions": ["en"],
        "image": "./assets/sv11b-victini-bwr-en.png",
        "images": {
            "jp": None,
            "kr": None,
            "en": "./assets/sv11b-victini-bwr-en.png",
        },
    },
}

BWR_SEED = {"basePrice": 280, "basePop": 120}


def apply_bwr(card: dict) -> dict:
    """Force BWR rarity/tier/holo for whitelisted cards."""
    overrides = BWR_CARDS.get(card.get("id") or "")
    if not overrides and card.get("id") not in BWR_CARDS:
        return card
    if overrides:
        for k, v in overrides.items():
            if v is not None:
                card[k] = v
    card["rarity"] = "BWR"
    card["tier"] = "A"
    card["holoStyle"] = "sar"
    card["seed"] = dict(BWR_SEED)
    if overrides and overrides.get("editions"):
        card["editions"] = list(overrides["editions"])
    return card


def ensure_bwr_cards(catalog: list[dict], packs: list[dict]) -> list[dict]:
    """Make sure every whitelisted BWR card exists in catalog (and pack cardIds)."""
    by_id = {c["id"]: c for c in catalog}
    packs_by_id = {p["id"]: p for p in packs}

    # Ensure Red Collection pack exists for Victini
    if "bw2-red-collection" not in packs_by_id:
        packs.append(
            {
                "id": "bw2-red-collection",
                "nameKo": "레드 컬렉션",
                "nameEn": "Red Collection",
                "nameJa": "レッドコレクション",
                "nameShort": "Red Collection",
                "code": "BW2",
                "releaseYear": 2011,
                # Not a tracked booster pack — Victini BWR only (hidden from home list).
                "listHidden": True,
                "languages": ["jp", "kr"],
                "blurb": "BW 확장팩. 특수가공 BWR 비크티니가 수록된 세트로 유명합니다.",
                "blurbEn": "BW expansion remembered for the special-finish BWR Victini.",
                "blurbJa": "特殊加工BWRビクティニで知られるBW拡張パック。",
                "packImage": "https://images.pokemontcg.io/bw2/70_hires.png",
                "coverCardId": "bw2-070",
                "cardIds": ["bw2-070"],
            }
        )
    else:
        packs_by_id["bw2-red-collection"]["listHidden"] = True

    packs_by_id = {p["id"]: p for p in packs}

    for card_id, meta in BWR_CARDS.items():
        if card_id in by_id:
            apply_bwr(by_id[card_id])
            continue
        pack_id = meta.get("packId")
        card = {
            "id": card_id,
            "packId": pack_id,
            "nameKo": meta.get("nameKo") or card_id,
            "nameEn": meta.get("nameEn") or card_id,
            "nameJa": meta.get("nameJa") or card_id,
            "number": meta.get("number") or "",
            "rarity": "BWR",
            "type": meta.get("type") or "fire",
            "typeKo": meta.get("typeKo") or "불",
            "holoStyle": "sar",
            "image": meta.get("image") or "",
            "images": meta.get("images")
            or {"jp": meta.get("image"), "kr": None, "en": meta.get("image")},
            "catalogKeys": {"jp": None, "kr": None, "en": None},
            "tier": "A",
            "seed": dict(BWR_SEED),
        }
        if meta.get("editions"):
            card["editions"] = list(meta["editions"])
        catalog.append(card)
        by_id[card_id] = card
        pack = packs_by_id.get(pack_id)
        if pack is not None:
            ids = pack.setdefault("cardIds", [])
            if card_id not in ids:
                ids.append(card_id)
            if not pack.get("coverCardId"):
                pack["coverCardId"] = card_id

    return catalog
