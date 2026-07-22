# -*- coding: utf-8 -*-
"""Apply GemRate PSA POP dumps into live pop.PSA (leave BRG untouched).

Expected dump shape (from item-details-advanced window.RowData):

  {
    "set": "...",
    "lang": "jp"|"kr"|"en",
    "grader": "PSA",
    "year": 2023,
    "fetchedAt": "YYYY-MM-DD",
    "rows": [ { card_number, name, parallel, g10, g9, g8, card_total_grades, ... } ]
  }

Matching: card number + parallel mapped from catalog rarity/holoStyle.
Missing Texture / Master Ball parallels are ignored unless no other match exists.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
GEMRATE_DIR = DATA / "gemrate"
SCRIPTS = ROOT / "scripts"

KST = timezone(timedelta(hours=9))

# Known GemRate set pages for packs we care about.
GEMRATE_SETS: dict[str, dict[str, dict[str, Any]]] = {
    "sv2a-151": {
        "jp": {
            "year": 2023,
            "set_name": "Pokemon Japanese Sv2a-Pokemon Card 151",
            "url": (
                "https://www.gemrate.com/item-details-advanced"
                "?grader=PSA&category=tcg-cards&year=2023"
                "&set_name=Pokemon+Japanese+Sv2a-Pokemon+Card+151"
            ),
        },
        "kr": {
            "year": 2023,
            "set_name": "Pokemon Korean Sv2a-Pokemon Card 151",
            "url": (
                "https://www.gemrate.com/item-details-advanced"
                "?grader=PSA&category=tcg-cards&year=2023"
                "&set_name=Pokemon+Korean+Sv2a-Pokemon+Card+151"
            ),
        },
        "en": {
            "year": 2023,
            "set_name": "Pokemon Mew EN-151",
            "url": (
                "https://www.gemrate.com/item-details-advanced"
                "?grader=PSA&category=tcg-cards&year=2023"
                "&set_name=Pokemon+Mew+EN-151"
            ),
        },
    },
    "m1l-mega-brave": {
        "jp": {
            "year": 2025,
            "set_name": "Pokemon Japanese M1l-Mega Brave",
            "url": (
                "https://www.gemrate.com/item-details-advanced"
                "?grader=PSA&category=tcg-cards&year=2025"
                "&set_name=Pokemon+Japanese+M1l-Mega+Brave"
            ),
        },
        "kr": {
            "year": 2025,
            "set_name": "Pokemon Korean M1l-Mega Brave",
            "url": (
                "https://www.gemrate.com/item-details-advanced"
                "?grader=PSA&category=tcg-cards&year=2025"
                "&set_name=Pokemon+Korean+M1l-Mega+Brave"
            ),
        },
        # EN Mega Evolution = JP Mega Brave + Mega Symphonia combined on GemRate.
        # Fetched once here; m1s-mega-symphonia reuses this dump for lang=en.
        "en": {
            "year": 2025,
            "set_name": "Pokemon Meg EN-Mega Evolution",
            "url": (
                "https://www.gemrate.com/item-details-advanced"
                "?grader=PSA&category=tcg-cards&year=2025"
                "&set_name=Pokemon+Meg+EN-Mega+Evolution"
            ),
        },
    },
    "m1s-mega-symphonia": {
        "jp": {
            "year": 2025,
            "set_name": "Pokemon Japanese M1s-Mega Symphonia",
            "url": (
                "https://www.gemrate.com/item-details-advanced"
                "?grader=PSA&category=tcg-cards&year=2025"
                "&set_name=Pokemon+Japanese+M1s-Mega+Symphonia"
            ),
        },
        "kr": {
            "year": 2025,
            "set_name": "Pokemon Korean M1s-Mega Symphonia",
            "url": (
                "https://www.gemrate.com/item-details-advanced"
                "?grader=PSA&category=tcg-cards&year=2025"
                "&set_name=Pokemon+Korean+M1s-Mega+Symphonia"
            ),
        },
        # Same GemRate EN page as Mega Brave — do not fetch twice.
        "en": {
            "reuseFrom": {"packId": "m1l-mega-brave", "lang": "en"},
        },
    },
}

# Preferred GemRate parallel names for each catalog rarity (order = preference).
# EN 151 uses Illustration Rare / Ultra Rare / Hyper Rare naming.
PARALLEL_BY_RARITY: dict[str, list[str]] = {
    "AR": ["Art Rare", "Illustration Rare"],
    "SAR": ["Special Art Rare", "Special Illustration Rare"],
    "MUR": ["Mega Ultra Rare", "Mega Hyper Rare", "MUR", "Hyper Rare", "Gold"],
    "SR": ["Super Rare"],
    "UR": ["Ultra Rare", "Hyper Rare", "Secret Rare"],
    "RR": ["Base", "Regular", "Holo", "Holofoil"],
    "R": ["Reverse Holo", "Reverse Holofoil", "Reverse", "Reverse-Holo", "Master Ball Reverse Holo"],
    "U": ["Reverse Holo", "Reverse Holofoil", "Reverse", "Reverse-Holo", "Master Ball Reverse Holo"],
    "C": ["Reverse Holo", "Reverse Holofoil", "Reverse", "Reverse-Holo", "Master Ball Reverse Holo"],
}

# When lang=en, prefer English PSA labels first (SR≠JP Super Rare).
PARALLEL_BY_RARITY_EN: dict[str, list[str]] = {
    "AR": ["Illustration Rare", "Art Rare"],
    "SAR": ["Special Illustration Rare", "Special Art Rare"],
    "MUR": ["Mega Hyper Rare", "Mega Ultra Rare", "MUR", "Hyper Rare", "Gold"],
    "SR": ["Ultra Rare", "Super Rare"],
    "UR": ["Hyper Rare", "Secret Rare", "Ultra Rare"],
    "RR": ["Base", "Regular", "Holo", "Holofoil"],
    "R": ["Reverse Holo", "Reverse Holofoil", "Reverse", "Reverse-Holo", "Master Ball Reverse Holo"],
    "U": ["Reverse Holo", "Reverse Holofoil", "Reverse", "Reverse-Holo", "Master Ball Reverse Holo"],
    "C": ["Reverse Holo", "Reverse Holofoil", "Reverse", "Reverse-Holo", "Master Ball Reverse Holo"],
}

# EN Mew 151 gold cards use different collector numbers than JP/KR.
EN_SV2A_NUM_MAP = {"208": "205", "209": "206", "210": "207"}

# Catalog sometimes keeps JP trainer names in nameEn.
NAME_EN_ALIASES = {
    "ポケモンいれかえ": "Switch",
}

HOLO_PARALLEL: dict[str, list[str]] = {
    "sar": ["Special Art Rare", "Special Illustration Rare"],
    "holo": ["Base", "Holo", "Holofoil", "Regular"],
    "reverse": [
        "Reverse Holo",
        "Reverse Holofoil",
        "Reverse",
        "Reverse-Holo",
        "Master Ball Reverse Holo",
    ],
}


def normalize_num(value: str | None) -> str:
    if not value:
        return ""
    head = str(value).split("/")[0].strip()
    digits = re.sub(r"\D", "", head)
    if not digits:
        return head.upper()
    return str(int(digits))


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    s = str(value).upper()
    s = s.replace("É", "E").replace("é", "E")
    s = re.sub(r"\bEX\b", " EX ", s)
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def catalog_name_en(card: dict) -> str:
    raw = (card.get("nameEn") or "").strip()
    if raw in NAME_EN_ALIASES:
        return NAME_EN_ALIASES[raw]
    if normalize_name(raw):
        return raw
    return NAME_EN_ALIASES.get(card.get("nameJa") or "", raw)


def parallel_norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def is_missing_texture(parallel: str | None) -> bool:
    return "missing texture" in parallel_norm(parallel)


def is_master_ball(parallel: str | None) -> bool:
    return "master ball" in parallel_norm(parallel)


def wanted_parallels(card: dict, lang: str | None = None) -> list[str]:
    rarity = (card.get("rarity") or "").strip().upper()
    holo = (card.get("holoStyle") or "").strip().lower()
    table = PARALLEL_BY_RARITY_EN if (lang or "").lower() == "en" else PARALLEL_BY_RARITY
    names: list[str] = []
    for src in (table.get(rarity) or [], HOLO_PARALLEL.get(holo) or []):
        for n in src:
            if n not in names:
                names.append(n)
    if not names:
        names = ["Base", "Reverse Holo"]
    return names


def psa_pop_object(row: dict[str, Any], asof: str, *, set_name: str | None) -> dict[str, Any]:
    def grade(key: str) -> int | None:
        v = row.get(key)
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    total = grade("card_total_grades")
    if total is None:
        total = grade("card_total_standard")

    le7_parts = [grade(f"g{i}") for i in range(1, 8)]
    le7_parts.append(grade("auth"))
    known = [v for v in le7_parts if v is not None]
    if known:
        le7 = sum(known)
    elif total is not None:
        high = sum(v for v in (grade("g10"), grade("g9"), grade("g8")) if v is not None)
        le7 = max(0, total - high)
    else:
        le7 = None

    return {
        "10": grade("g10"),
        "9": grade("g9"),
        "8": grade("g8"),
        "le7": le7,
        "total": total,
        "source": "gemrate",
        "asOf": asof[:10],
        "gemrateId": row.get("gemrate_id"),
        "parallel": row.get("parallel"),
        "setName": set_name,
    }


def parallel_matches(parallel: str, want: str) -> bool:
    p = parallel_norm(parallel)
    w = parallel_norm(want)
    if not p or not w:
        return False
    if p == w:
        return True
    # Avoid "Art Rare" matching "Special Art Rare"
    if w in ("art rare", "illustration rare") and p.startswith("special "):
        return False
    if w in ("ultra rare",) and p.startswith("special "):
        return False
    if w == p.replace("-", " "):
        return True
    return False


def pick_gemrate_row(
    catalog_card: dict,
    rows: list[dict[str, Any]],
    *,
    lang: str | None = None,
) -> dict[str, Any] | None:
    want_num = normalize_num(catalog_card.get("number"))
    preferred = wanted_parallels(catalog_card, lang)
    nums = {want_num} if want_num else set()
    if (lang or "").lower() == "en" and want_num in EN_SV2A_NUM_MAP:
        nums.add(EN_SV2A_NUM_MAP[want_num])
    same_num = [
        r
        for r in rows
        if normalize_num(str(r.get("card_number") or "")) in nums
    ]

    def score(row: dict[str, Any]) -> tuple:
        p = row.get("parallel")
        miss = 1 if is_missing_texture(p) else 0
        master = 1 if is_master_ball(p) else 0
        pref = 99
        for i, want in enumerate(preferred):
            if parallel_matches(p, want):
                pref = i
                break
        name_boost = 0
        want_name = normalize_name(catalog_name_en(catalog_card))
        row_name = normalize_name(row.get("name"))
        if want_name and row_name:
            if want_name == row_name:
                name_boost = -2
            elif want_name in row_name or row_name in want_name:
                name_boost = -1
        try:
            total = int(row.get("card_total_grades") or 0)
        except (TypeError, ValueError):
            total = 0
        return (miss, master, pref, name_boost, -total)

    def choose(candidates: list[dict[str, Any]], *, require_parallel: bool) -> dict | None:
        if not candidates:
            return None
        candidates = list(candidates)
        candidates.sort(key=score)
        best = candidates[0]
        hit = any(parallel_matches(best.get("parallel"), w) for w in preferred)
        if hit:
            return best
        if not require_parallel and len(candidates) == 1:
            return best
        filtered = [
            r
            for r in candidates
            if not is_master_ball(r.get("parallel"))
            and not is_missing_texture(r.get("parallel"))
            and any(parallel_matches(r.get("parallel"), w) for w in preferred)
        ]
        if filtered:
            filtered.sort(key=score)
            return filtered[0]
        return None

    picked = choose(same_num, require_parallel=len(same_num) > 1)

    def name_matches_row(row: dict[str, Any] | None, want: str) -> bool:
        if not row or not want:
            return False
        row_name = normalize_name(row.get("name"))
        if not row_name:
            return False
        return want == row_name or want in row_name or row_name in want

    # EN Mega Evolution (etc.) renumbers vs JP — reject number hits whose name
    # clearly doesn't match, then fall back to name + parallel.
    want_name = normalize_name(catalog_name_en(catalog_card))
    if picked:
        if (lang or "").lower() != "en" or not want_name or name_matches_row(
            picked, want_name
        ):
            return picked
        # Number collided with a different card in a multi-set EN dump.

    if not want_name:
        return None
    by_name = []
    for r in rows:
        if not name_matches_row(r, want_name):
            continue
        if any(parallel_matches(r.get("parallel"), w) for w in preferred):
            by_name.append(r)
    return choose(by_name, require_parallel=True)


def apply_psa_to_live(
    live: dict,
    card_id: str,
    lang: str,
    psa_pop: dict[str, Any],
    asof_iso: str,
) -> None:
    variants = live.setdefault("cards", {}).setdefault(card_id, {})
    variant = variants.setdefault(lang, {})
    pop = variant.setdefault("pop", {})
    pop["PSA"] = psa_pop
    variant["updatedAt"] = asof_iso


def restore_psa_pops(live: dict, previous: dict | None) -> int:
    if not previous:
        return 0
    kept = 0
    prev_cards = previous.get("cards") or {}
    for card_id, variants in (live.get("cards") or {}).items():
        prev_variants = prev_cards.get(card_id) or {}
        for lang, variant in variants.items():
            prev = prev_variants.get(lang) or {}
            prev_psa = (prev.get("pop") or {}).get("PSA")
            if isinstance(prev_psa, dict) and prev_psa.get("source") == "gemrate":
                variant.setdefault("pop", {})["PSA"] = prev_psa
                kept += 1
    return kept


def load_dump(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"rows": data, "lang": None, "set": None}
    if "rows" not in data:
        raise ValueError(f"GemRate dump missing rows: {path}")
    return data


def dump_path_for(pack_id: str, lang: str) -> Path:
    return GEMRATE_DIR / f"{pack_id}-{lang}.json"


def lang_meta(pack_id: str, lang: str) -> dict[str, Any] | None:
    pack = GEMRATE_SETS.get(pack_id) or {}
    meta = pack.get(lang)
    return meta if isinstance(meta, dict) else None


def resolve_dump_path(pack_id: str, lang: str) -> Path:
    """Dump JSON path, following reuseFrom (shared EN Mega Evolution, etc.)."""
    meta = lang_meta(pack_id, lang) or {}
    reuse = meta.get("reuseFrom")
    if isinstance(reuse, dict) and reuse.get("packId"):
        return dump_path_for(str(reuse["packId"]), str(reuse.get("lang") or lang))
    return dump_path_for(pack_id, lang)


def apply_dump_to_live(
    live: dict,
    catalog: list[dict],
    dump: dict[str, Any],
    *,
    pack_id: str,
    lang: str,
    asof_iso: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    rows = list(dump.get("rows") or [])
    set_name = dump.get("set")
    asof = dump.get("fetchedAt") or asof_iso
    matched = 0
    missed = 0
    skipped_tier = 0
    examples: list[dict] = []

    pack_cards = [c for c in catalog if c.get("packId") == pack_id]
    live_ids = set((live.get("cards") or {}).keys())

    for card in pack_cards:
        if card["id"] not in live_ids:
            skipped_tier += 1
            continue
        row = pick_gemrate_row(card, rows, lang=lang)
        if not row:
            missed += 1
            if len(examples) < 12:
                examples.append(
                    {
                        "id": card["id"],
                        "number": card.get("number"),
                        "rarity": card.get("rarity"),
                        "want": wanted_parallels(card, lang),
                    }
                )
            continue
        psa = psa_pop_object(row, asof, set_name=set_name)
        if not dry_run:
            apply_psa_to_live(live, card["id"], lang, psa, asof_iso)
        matched += 1

    return {
        "packId": pack_id,
        "lang": lang,
        "rows": len(rows),
        "matched": matched,
        "missed": missed,
        "skippedNotLive": skipped_tier,
        "missExamples": examples,
        "setName": set_name,
    }


def mark_live_source(live: dict) -> None:
    src = live.get("source") or "seed"
    if "PSA" in src or "gemrate" in src.lower():
        return
    if src == "seed":
        live["source"] = "seed+PSA"
    else:
        live["source"] = f"{src}+PSA"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Import GemRate PSA POP dumps into live data")
    p.add_argument("--pack", default="sv2a-151", help="Pack id (default sv2a-151)")
    p.add_argument(
        "--langs",
        default="jp,kr,en",
        help="Comma-separated langs to apply (default jp,kr,en)",
    )
    p.add_argument(
        "--dump",
        default=None,
        help="Optional single dump JSON path (implies one lang via --langs)",
    )
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    import sys

    sys.path.insert(0, str(SCRIPTS))
    from pokepop_snapshot import write_data_bundle  # noqa: WPS433

    args = parse_args(argv)
    asof_iso = datetime.now(KST).isoformat(timespec="seconds")
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    live_path = DATA / "live" / "pop-price.json"
    live = json.loads(live_path.read_text(encoding="utf-8"))

    langs = [x.strip() for x in args.langs.split(",") if x.strip()]
    stats: list[dict] = []

    if args.dump:
        if len(langs) != 1:
            raise SystemExit("--dump requires exactly one --langs value")
        dump = load_dump(Path(args.dump))
        stats.append(
            apply_dump_to_live(
                live,
                catalog,
                dump,
                pack_id=args.pack,
                lang=langs[0],
                asof_iso=asof_iso,
                dry_run=args.dry_run,
            )
        )
    else:
        for lang in langs:
            path = resolve_dump_path(args.pack, lang)
            if not path.is_file():
                stats.append(
                    {
                        "packId": args.pack,
                        "lang": lang,
                        "error": f"missing dump: {path.name}",
                    }
                )
                continue
            dump = load_dump(path)
            stats.append(
                apply_dump_to_live(
                    live,
                    catalog,
                    dump,
                    pack_id=args.pack,
                    lang=lang,
                    asof_iso=asof_iso,
                    dry_run=args.dry_run,
                )
            )

    if not args.dry_run and any(s.get("matched") for s in stats):
        mark_live_source(live)
        live["generatedAt"] = asof_iso
        last_run = {
            "ranAt": asof_iso,
            "stats": {"gemratePsa": stats},
        }
        write_data_bundle(DATA, packs, catalog, live, last_run)

    print(json.dumps({"gemratePsa": stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
