# -*- coding: utf-8 -*-
"""Find secret rares for M1L/M1S and all MUR cards we care about."""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0"}
OUT = Path(__file__).resolve().parent.parent / "data" / "_tmp" / "mur_scan.json"


def fetch(cid: int) -> dict | None:
    url = f"https://www.pokemon-card.com/card-search/details.php/card/{cid}"
    req = urllib.request.Request(url, headers=UA)
    try:
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    except Exception:
        return None
    if "card_images" not in html:
        return None
    name = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    num = re.search(
        r"regulation_logo_1/([A-Za-z0-9\-]+)\.gif[^>]*>\s*&nbsp;(\d+)\s*&nbsp;/\s*&nbsp;(\d+)",
        html,
        re.S,
    )
    rare = re.search(r"ic_rare_([A-Za-z0-9_]+)\.gif", html)
    img = re.search(r"card_images/large/([^\"]+)", html)
    if not num:
        return None
    return {
        "jp_id": cid,
        "name": re.sub("<[^>]+>", "", name.group(1)).strip() if name else None,
        "set_name": num.group(1),
        "number": f"{int(num.group(2)):03d}/{int(num.group(3)):03d}",
        "collector": int(num.group(2)),
        "set_total": int(num.group(3)),
        "rarity": rare.group(1) if rare else None,
        "img": (
            "https://www.pokemon-card.com/assets/images/card_images/large/" + img.group(1)
            if img
            else None
        ),
    }


def main() -> None:
    found: list[dict] = []
    # Known / likely ranges for M1 secrets and later MURs
    ranges = [
        range(48400, 48620),  # M1L/M1S secrets
        range(48780, 48850),  # start deck / Charizard Y area
        range(49880, 50050),  # Mega Dream / Dragonite area
        range(50500, 50700),
        range(51000, 51200),
    ]
    # Also probe known IDs
    known = [48449, 48801, 49992, 48353, 49983]
    seen = set()
    for cid in list(known) + [c for r in ranges for c in r]:
        if cid in seen:
            continue
        seen.add(cid)
        info = fetch(cid)
        if not info:
            continue
        rare = (info.get("rarity") or "").upper()
        coll = info.get("collector") or 0
        total = info.get("set_total") or 0
        keep = rare == "MUR" or (
            info["set_name"] in {"M1L", "M1S"} and coll > total
        )
        if keep:
            found.append(info)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(found, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mur = [x for x in found if (x.get("rarity") or "").upper() == "MUR"]
    print(f"found={len(found)} mur={len(mur)} out={OUT}")
    for x in mur:
        print(f"MUR {x['jp_id']} {x['set_name']} {x['number']} {x['name']}".encode("utf-8", "replace").decode("utf-8"))


if __name__ == "__main__":
    main()
