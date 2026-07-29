# -*- coding: utf-8 -*-
"""Add Monster Ball (MB) and Master Ball (MSB) mirror variants for sv2a-151.

JP 151 packs can pull Reverse Holo (monster ball) and Master Ball Reverse Holo
on C/U/R cards (~153). Register them as separate catalog rarities so pack-open
simulation and POP matching can target them explicitly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pokepop_snapshot import (  # noqa: E402
    assign_tiers_to_catalog,
    build_live_snapshot,
    write_data_bundle,
)
from ebay_prices import restore_ebay_prices  # noqa: E402
from brg_pop import restore_brg_pops  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402

KST = timezone(timedelta(hours=9))
PACK_ID = "sv2a-151"
BASE_RARITIES = {"C", "U", "R"}

VARIANT_SPECS = {
    "mb": {
        "suffix": "-mb",
        "rarity": "MB",
        "parallel": "monster-ball",
        "holoStyle": "monster-ball",
        "seedPrice": 18,
        "seedPop": 90,
        "nameSuffixKo": " (몬스터볼)",
        "nameSuffixEn": " (Monster Ball)",
        "nameSuffixJa": "（モンスターボール）",
    },
    "msb": {
        "suffix": "-msb",
        "rarity": "MSB",
        "parallel": "master-ball",
        "holoStyle": "master-ball",
        "seedPrice": 65,
        "seedPop": 220,
        "nameSuffixKo": " (마스터볼)",
        "nameSuffixEn": " (Master Ball)",
        "nameSuffixJa": "（マスターボール）",
    },
}


def clone_variant(base: dict, kind: str) -> dict:
    spec = VARIANT_SPECS[kind]
    out = dict(base)
    out["id"] = f"{base['id']}{spec['suffix']}"
    out["baseId"] = base["id"]
    out["rarity"] = spec["rarity"]
    out["parallel"] = spec["parallel"]
    out["holoStyle"] = spec["holoStyle"]
    out.pop("tier", None)
    out["seed"] = {
        "basePrice": spec["seedPrice"],
        "basePop": spec["seedPop"],
    }
    # Keep same art for now; UI can badge by rarity/parallel.
    for key, suffix in (
        ("nameKo", "nameSuffixKo"),
        ("nameEn", "nameSuffixEn"),
        ("nameJa", "nameSuffixJa"),
    ):
        base_name = (base.get(key) or "").strip()
        if base_name and not base_name.endswith(spec[suffix].strip()):
            out[key] = base_name + spec[suffix]
    return out


def main() -> None:
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))

    pack = next((p for p in packs if p.get("id") == PACK_ID), None)
    if not pack:
        raise SystemExit(f"pack not found: {PACK_ID}")

    by_id = {c["id"]: c for c in catalog}
    bases = [
        c
        for c in catalog
        if c.get("packId") == PACK_ID and c.get("rarity") in BASE_RARITIES
    ]
    bases.sort(key=lambda c: c["id"])

    added = []
    for base in bases:
        for kind in ("mb", "msb"):
            variant = clone_variant(base, kind)
            if variant["id"] in by_id:
                # Refresh mutable fields on re-run
                prev = by_id[variant["id"]]
                prev.update(
                    {
                        "baseId": variant["baseId"],
                        "rarity": variant["rarity"],
                        "parallel": variant["parallel"],
                        "holoStyle": variant["holoStyle"],
                        "seed": variant["seed"],
                        "nameKo": variant.get("nameKo", prev.get("nameKo")),
                        "nameEn": variant.get("nameEn", prev.get("nameEn")),
                        "nameJa": variant.get("nameJa", prev.get("nameJa")),
                    }
                )
                prev.pop("tier", None)
                continue
            catalog.append(variant)
            by_id[variant["id"]] = variant
            added.append(variant["id"])

    # Keep pack cardIds complete and stable: base order, then mirrors after each base.
    base_ids = [c["id"] for c in bases]
    mirror_ids = []
    for bid in base_ids:
        mirror_ids.append(f"{bid}-mb")
        mirror_ids.append(f"{bid}-msb")

    existing = list(pack.get("cardIds") or [])
    non_mirror_existing = [i for i in existing if not i.endswith(("-mb", "-msb"))]
    if non_mirror_existing:
        ordered_baseish = non_mirror_existing
    else:
        ordered_baseish = sorted(
            [
                c["id"]
                for c in catalog
                if c.get("packId") == PACK_ID and not str(c["id"]).endswith(("-mb", "-msb"))
            ]
        )

    pack["cardIds"] = ordered_baseish + [
        mid for mid in mirror_ids if mid in by_id and mid not in ordered_baseish
    ]

    assign_tiers_to_catalog(catalog)

    asof_iso = datetime.now(KST).isoformat(timespec="seconds")
    live_path = DATA / "live" / "pop-price.json"
    previous = json.loads(live_path.read_text(encoding="utf-8")) if live_path.exists() else {}
    live, stats = build_live_snapshot(catalog, packs, asof_iso, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or live.get("source") or "seed"
    live["generatedAt"] = asof_iso
    keep_ids = {c["id"] for c in catalog}
    live["cards"] = {k: v for k, v in (live.get("cards") or {}).items() if k in keep_ids}

    last_run = {"ranAt": asof_iso, "stats": stats}
    write_data_bundle(DATA, packs, catalog, live, last_run)

    pack_cards = [c for c in catalog if c.get("packId") == PACK_ID]
    rar = {}
    for c in pack_cards:
        r = c.get("rarity") or "?"
        rar[r] = rar.get(r, 0) + 1

    print(
        json.dumps(
            {
                "added": len(added),
                "packCards": len(pack_cards),
                "cardIds": len(pack["cardIds"]),
                "rarityCounts": rar,
                "sample": added[:6],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
