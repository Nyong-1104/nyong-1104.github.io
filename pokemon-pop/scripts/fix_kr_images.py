# -*- coding: utf-8 -*-
"""Re-attach KR card images with name-aware matching (fixes duplicate #000 etc.)."""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from import_extra_packs import EXTRA_PACKS, http_json  # noqa: E402
from pokepop_snapshot import write_data_bundle  # noqa: E402

UA = {"User-Agent": "PokePopKrFix/1.0"}


def norm_name(value: str) -> str:
    s = str(value or "")
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"\s+", "", s)
    return s.lower()


def prefer_url(urls: list[str]) -> str | None:
    if not urls:
        return None
    scored = []
    for u in urls:
        score = 0
        if "pokemonkorea.co.kr" in u:
            score += 10
        if "firebasestorage" in u or "card32.appspot" in u:
            score -= 5
        if "w=" in u:
            u = re.sub(r"w=\d+", "w=800", u)
        scored.append((score, u))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def load_kr_entries(rel_path: str) -> dict[str, list[dict]]:
    url = f"https://raw.githubusercontent.com/kinbo-ptcg/ptcg-kr-db/main/card_data_product/pack/{rel_path}"
    try:
        cards = http_json(url)
    except Exception as e:
        print("KR load fail", rel_path, e)
        return {}
    by_num: dict[str, list[dict]] = {}
    for c in cards:
        num = str(c.get("number") or "").split("/")[0].zfill(3)
        img = c.get("cardImgURL")
        if not img:
            continue
        if "w=" in img:
            img = re.sub(r"w=\d+", "w=800", img)
        by_num.setdefault(num, []).append(
            {
                "name": c.get("name") or c.get("cardID") or "",
                "url": img,
            }
        )
    return by_num


def pick_image(card: dict, entries: list[dict]) -> str | None:
    if not entries:
        return None
    names = [
        norm_name(card.get("nameKo")),
        norm_name(card.get("nameEn")),
        norm_name(card.get("nameJa")),
    ]
    names = [n for n in names if n]

    # Exact / contains name match
    named_urls = []
    for e in entries:
        en = norm_name(e["name"])
        if not en:
            continue
        for n in names:
            if en == n or en in n or n in en:
                named_urls.append(e["url"])
                break
            # energy type hint
            if "에너지" in en or "energy" in n or "エネルギー" in (card.get("nameJa") or ""):
                for token_ko, token_en, token_ja in (
                    ("풀", "grass", "草"),
                    ("불", "fire", "炎"),
                    ("물", "water", "水"),
                    ("번개", "lightning", "雷"),
                    ("초", "psychic", "超"),
                    ("격투", "fighting", "闘"),
                    ("악", "dark", "悪"),
                    ("강철", "metal", "鋼"),
                ):
                    if token_ko in en or token_ko in (card.get("nameKo") or ""):
                        if token_ko in en and token_ko in (card.get("nameKo") or ""):
                            named_urls.append(e["url"])
                            break
                    if token_ja in (card.get("nameJa") or "") and token_ko in en:
                        named_urls.append(e["url"])
                        break
    if named_urls:
        return prefer_url(named_urls)

    # Fall back: prefer official CDN among all same-number entries
    return prefer_url([e["url"] for e in entries])


def main() -> int:
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))

    kr_json_by_pack = {
        "sv2a-151": "SV/SV2a.json",
        "pokekyun": "XY/cp3.json",
        "thunderclap-spark": "SM/sm7a.json",
    }
    for meta in EXTRA_PACKS:
        if meta.get("krJson"):
            kr_json_by_pack[meta["id"]] = meta["krJson"]

    cache: dict[str, dict[str, list[dict]]] = {}
    fixed = 0
    cleared = 0

    for card in catalog:
        pack_id = card.get("packId")
        rel = kr_json_by_pack.get(pack_id)
        images = card.setdefault("images", {})
        if not rel:
            # leave as-is
            continue
        if rel not in cache:
            print("load", rel)
            cache[rel] = load_kr_entries(rel)
        num = str(card.get("number") or "").split("/")[0].zfill(3)
        entries = cache[rel].get(num) or []
        url = pick_image(card, entries)
        prev = images.get("kr")
        if url != prev:
            images["kr"] = url
            if url:
                fixed += 1
            else:
                cleared += 1

    (DATA / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    live = json.loads((DATA / "live" / "pop-price.json").read_text(encoding="utf-8"))
    write_data_bundle(DATA, packs, catalog, live)

    # verify s8a samples
    s8a = {c["id"]: c for c in catalog if c.get("packId") == "s8a-25th"}
    print(
        json.dumps(
            {
                "fixed": fixed,
                "cleared": cleared,
                "grass": (s8a.get("s8a-000") or {}).get("images", {}).get("kr"),
                "oak": (s8a.get("s8a-003") or {}).get("images", {}).get("kr"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
