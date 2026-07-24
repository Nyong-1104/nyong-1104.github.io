# -*- coding: utf-8 -*-
import json
import re
import time
import urllib.request
from pathlib import Path

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}
OUT = Path(__file__).resolve().parent.parent / "data" / "_tmp" / "mur_extra.json"


def fetch(cid: int):
    url = f"https://www.pokemon-card.com/card-search/details.php/card/{cid}"
    req = urllib.request.Request(url, headers=UA)
    try:
        html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    except Exception:
        return None
    name = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    num = re.search(
        r"regulation_logo_1/([A-Za-z0-9\-]+)\.gif[^>]*>\s*&nbsp;(\d+)\s*&nbsp;/\s*&nbsp;(\d+)",
        html,
        re.S,
    )
    rare = re.search(r"ic_rare_([A-Za-z0-9_]+)\.gif", html)
    img = re.search(r'card_images/large/([^"]+)', html)
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


found = []
OUT.parent.mkdir(parents=True, exist_ok=True)
for cid in range(50150, 50320):
    info = fetch(cid)
    time.sleep(0.08)
    if not info:
        continue
    rare = (info.get("rarity") or "").upper()
    if rare == "MUR" or (
        info["set_name"] == "M4"
        and info["collector"] > info["set_total"]
        and "ゲッコウガ" in (info.get("name") or "")
    ):
        found.append(info)
        OUT.write_text(json.dumps(found, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

OUT.write_text(json.dumps(found, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("done", len(found), "out=", OUT)
