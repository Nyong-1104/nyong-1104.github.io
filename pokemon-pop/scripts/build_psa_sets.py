# -*- coding: utf-8 -*-
"""Generate psa-sets.json skeleton from packs.json and merge known PSA set URLs."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Manually curated PSA set POP pages (HeadingID in URL).
# Fill more as you find them on psacard.com/pop/tcg-cards/...
KNOWN = {
    "sv2p-snow-hazard": {
        "jp": "https://www.psacard.com/pop/tcg-cards/2023/pokemon-japanese-sv2p-snow-hazard/236821",
    },
    "sv8-super-electric-breaker": {
        "jp": "https://www.psacard.com/pop/tcg-cards/2024/pokemon-japanese-sv8-super-electric-breaker/284389",
    },
}


def main() -> int:
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    out_path = DATA / "psa-sets.json"
    existing = {}
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))

    out: dict = {}
    for pack in packs:
        pid = pack["id"]
        langs = pack.get("languages") or ["jp"]
        row = dict(existing.get(pid) or {})
        known = KNOWN.get(pid) or {}
        for lang in langs:
            if lang in known and known[lang]:
                row[lang] = known[lang]
            elif lang not in row:
                row[lang] = None
        row["_meta"] = {
            "code": pack.get("code"),
            "year": pack.get("releaseYear"),
            "nameEn": pack.get("nameEn"),
        }
        out[pid] = row

    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    filled = sum(
        1
        for row in out.values()
        for k, v in row.items()
        if k != "_meta" and v
    )
    print(f"Wrote {out_path} ({len(out)} packs, {filled} set URLs filled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
