# -*- coding: utf-8 -*-
"""Split S8a Pikachu V-UNION collage into 4 catalog cards and rebuild data.js."""
from __future__ import annotations

import io
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pokepop_snapshot import (  # noqa: E402
    build_live_snapshot,
    load_previous_live,
    write_data_bundle,
)
from ebay_prices import restore_ebay_prices  # noqa: E402
from brg_pop import restore_brg_pops  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "PokePopVUnion/1.0"}

COLLAGE_URL = (
    "https://www.pokemon-card.com/assets/images/card_images/large/S8a/"
    "040090_P_PIKACHIXYUUVUNION.jpg"
)
KR_COLLAGE = "https://cards.image.pokemonkorea.co.kr/data/wmimages/S/S8a/S8a_025.png?w=800"

# quadrant order matching official 左上/右上/左下/右下
PIECES = [
    {
        "id": "s8a-025",
        "number": "025/028",
        "posKo": "좌상",
        "posEn": "Top Left",
        "posJa": "左上",
        "quad": (0, 0),
    },
    {
        "id": "s8a-026",
        "number": "026/028",
        "posKo": "우상",
        "posEn": "Top Right",
        "posJa": "右上",
        "quad": (1, 0),
    },
    {
        "id": "s8a-027",
        "number": "027/028",
        "posKo": "좌하",
        "posEn": "Bottom Left",
        "posJa": "左下",
        "quad": (0, 1),
    },
    {
        "id": "s8a-028",
        "number": "028/028",
        "posKo": "우하",
        "posEn": "Bottom Right",
        "posJa": "右下",
        "quad": (1, 1),
    },
]


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def crop_quadrants(img_bytes: bytes, prefix: str) -> dict[str, str]:
    """Return map piece_id -> relative asset path."""
    ASSETS.mkdir(parents=True, exist_ok=True)
    im = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    w, h = im.size
    cw, ch = w // 2, h // 2
    out = {}
    for piece in PIECES:
        qx, qy = piece["quad"]
        box = (qx * cw, qy * ch, (qx + 1) * cw, (qy + 1) * ch)
        crop = im.crop(box)
        fname = f"{prefix}-{piece['id'].split('-')[1]}.png"
        dest = ASSETS / fname
        crop.save(dest, "PNG")
        out[piece["id"]] = f"./assets/{fname}"
    return out


def main() -> int:
    print("Downloading JP collage…")
    jp_bytes = download(COLLAGE_URL)
    jp_paths = crop_quadrants(jp_bytes, "s8a-vunion-jp")

    kr_paths = {}
    try:
        print("Downloading KR collage…")
        kr_bytes = download(KR_COLLAGE)
        kr_paths = crop_quadrants(kr_bytes, "s8a-vunion-kr")
    except Exception as e:
        print("KR crop skipped:", e)

    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))

    # remove existing v-union / 025-028 s8a cards
    remove_ids = {p["id"] for p in PIECES} | {"s8a-025"}
    catalog = [c for c in catalog if c.get("id") not in remove_ids or c.get("packId") != "s8a-25th"]
    # cleaner: drop any s8a 025-028
    catalog = [
        c
        for c in catalog
        if not (
            c.get("packId") == "s8a-25th"
            and str(c.get("number") or "").split("/")[0] in {"025", "026", "027", "028"}
        )
    ]

    new_cards = []
    for i, piece in enumerate(PIECES):
        seed = {"basePrice": 95 + (i * 3), "basePop": 55 - (i * 2)}
        card = {
            "id": piece["id"],
            "packId": "s8a-25th",
            "nameKo": f"피카츄 V-UNION ({piece['posKo']})",
            "nameEn": f"Pikachu V-UNION ({piece['posEn']})",
            "nameJa": f"ピカチュウV-UNION（{piece['posJa']}）",
            "number": piece["number"],
            "rarity": "RRR",
            "type": "lightning",
            "typeKo": "번개",
            "holoStyle": "holo",
            "image": jp_paths[piece["id"]],
            "images": {
                "jp": jp_paths[piece["id"]],
                "kr": kr_paths.get(piece["id"]),
                "en": jp_paths[piece["id"]],
            },
            "catalogKeys": {"jp": 40090, "kr": None, "en": None},
            "vUnionGroup": "s8a-pikachu-vunion",
            "vUnionPart": piece["posEn"],
            "seed": seed,
        }
        new_cards.append(card)

    # insert after last s8a card before 029 if present, else append
    insert_at = len(catalog)
    for i, c in enumerate(catalog):
        if c.get("packId") == "s8a-25th" and str(c.get("number") or "").startswith("029"):
            insert_at = i
            break
    catalog[insert_at:insert_at] = new_cards

    # update pack cardIds
    for pack in packs:
        if pack.get("id") != "s8a-25th":
            continue
        ids = [cid for cid in pack.get("cardIds") or [] if cid not in remove_ids]
        # insert four pieces where 025 was, or before 029
        if "s8a-029" in ids:
            idx = ids.index("s8a-029")
            ids[idx:idx] = [p["id"] for p in PIECES]
        else:
            ids.extend(p["id"] for p in PIECES)
        # dedupe preserve order
        seen = set()
        ordered = []
        for cid in ids:
            if cid in seen:
                continue
            seen.add(cid)
            ordered.append(cid)
        pack["cardIds"] = ordered

    asof = datetime.now(KST).isoformat(timespec="seconds")
    previous = load_previous_live(DATA)
    live, stats = build_live_snapshot(catalog, packs, asof, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or live.get("source") or "seed"
    live["generatedAt"] = asof
    write_data_bundle(DATA, packs, catalog, live)
    print(json.dumps({"added": [c["id"] for c in new_cards], **stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
