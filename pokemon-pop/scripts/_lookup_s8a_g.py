# -*- coding: utf-8 -*-
"""Lookup S8a-G 25th Anniversary Golden Box cards from PTCG-database."""
from __future__ import annotations

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

UA = {"User-Agent": "PokePopCatalogBuilder/1.0"}
RAW = "https://raw.githubusercontent.com/type-null/PTCG-database/main/data_jp/S8a-G"
API = "https://api.github.com/repos/type-null/PTCG-database/contents/data_jp/S8a-G"
OUT = Path(__file__).resolve().parent.parent / "data" / "_tmp" / "s8a_g_cards.json"


def http_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_card(jid: int) -> dict:
    data = http_json(f"{RAW}/{jid}.json")
    data["_jp_file_id"] = jid
    return data


def sort_key(card: dict):
    num = str(card.get("number") or "")
    left = num.split("/")[0].strip() if "/" in num else num.strip()
    try:
        return (0, int(left))
    except ValueError:
        return (1, left)


def main() -> int:
    items = http_json(API)
    ids = [int(x["name"].replace(".json", "")) for x in items if x["name"].endswith(".json")]
    cards: list[dict] = []
    with ThreadPoolExecutor(max_workers=24) as ex:
        futs = [ex.submit(fetch_card, jid) for jid in ids]
        for fut in as_completed(futs):
            cards.append(fut.result())
    cards.sort(key=sort_key)

    slim = []
    for c in cards:
        row = {
            "jp_id": c.get("_jp_file_id"),
            "number": c.get("number"),
            "name": c.get("name"),
            "rarity": c.get("rarity"),
            "types": c.get("types"),
            "supertype": c.get("supertype") or c.get("cardType"),
            "imageURL": c.get("imageURL"),
            "all_keys": sorted(c.keys()),
        }
        for k, v in c.items():
            kl = k.lower()
            if "image" in kl or "img" in kl or kl.endswith("url"):
                row[k] = v
        slim.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(slim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} count={len(slim)}")
    for row in slim:
        print(
            f"{row.get('number')} | jp_id={row.get('jp_id')} | rarity={row.get('rarity')} | keys={row.get('all_keys')}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
