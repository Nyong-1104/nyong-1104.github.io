# -*- coding: utf-8 -*-
"""Fetch real BRG POP counts from break.co.kr (gate.break.co.kr/brg)."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE = "https://gate.break.co.kr/brg"
HEADERS = {
    "x-country-code": "KR",
    "Accept": "application/json",
    "User-Agent": "PokePop/1.0 (BRG pop sync)",
}

LANG_MARKER = {
    "jp": "JAPANESE",
    "kr": "KOREAN",
    "en": "ENGLISH",
}

# break.co.kr often names EN sets as "... BLKEN" / "... WHTEN" without the word ENGLISH.
EN_EXCLUDE = ("JAPANESE", "KOREAN", "CHINESE", "ASIAN-ENGLISH")

# Table columns are PSA-style; map BRG manualScore → display column.
# BRG has no 9.5: 100→10, 90(+85)→9, 80→8; lower scores roll into ≤7.
BRG_TO_COL = {
    "100": "10",
    "90": "9",
    "85": "9",
    "80": "8",
}


def _is_english_set_name(name: str) -> bool:
    upper = (name or "").upper().strip()
    if not upper.startswith("POKEMON"):
        return False
    if any(x in upper for x in EN_EXCLUDE):
        return False
    if "ENGLISH" in upper:
        return True
    # e.g. POKEMON S&V BLKEN / WHTEN / TEFEN
    token = upper.split()[-1] if upper.split() else ""
    return token.endswith("EN") and len(token) >= 4


def _get_json(path: str, params: dict[str, Any]) -> dict[str, Any]:
    q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{BASE}{path}?{q}"
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"BRG HTTP {e.code}: {detail[:400]}") from e


def search_sets(keyword: str, *, limit: int = 50) -> list[dict[str, Any]]:
    data = _get_json(
        "/api/cards/pop-report/search",
        {"field": "setName", "keyword": keyword, "limit": limit, "offset": 0},
    )
    if data.get("status") != "success":
        return []
    return list((data.get("data") or {}).get("cards") or [])


def fetch_set_pop(set_name: str, year: int | str, *, limit: int = 500) -> list[dict[str, Any]]:
    data = _get_json(
        "/api/cards/pop-report",
        {"setName": set_name, "year": str(year), "limit": str(limit), "offset": "0"},
    )
    if data.get("status") != "success":
        raise RuntimeError(f"BRG pop-report failed: {data.get('message')}")
    return list((data.get("data") or {}).get("cards") or [])


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
    s = s.replace("é", "E").replace("É", "E")
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def resolve_brg_set(
    pack: dict, lang: str
) -> tuple[str, int] | None:
    """Find BRG setName + year for a pack edition."""
    # Explicit override (promo / odd naming)
    override = (pack.get("brgSets") or {}).get(lang)
    if isinstance(override, dict) and override.get("setName") and override.get("year") is not None:
        return str(override["setName"]).strip(), int(override["year"])

    code = (pack.get("code") or "").strip().upper()
    if not code:
        return None
    year_hint = pack.get("releaseYear")

    # Prefer full code; also try last segment after hyphen (MG-PROMO → PROMO)
    search_keys = [code]
    if "-" in code:
        search_keys.append(code.split("-")[-1])
        search_keys.append(code.split("-")[0])
    if lang == "en":
        # Name tokens help find BLKEN / WHTEN style sets
        for part in str(pack.get("nameEn") or "").replace("—", " ").replace("-", " ").split():
            if len(part) >= 4 and part.isascii():
                search_keys.append(part)

    candidates: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for key_code in search_keys:
        hits = search_sets(key_code)
        for row in hits:
            name = (row.get("setName") or "").strip()
            year = row.get("year")
            if not name or year is None:
                continue
            key = (name, int(year))
            if key in seen:
                continue
            upper = name.upper()
            if "POKEMON" not in upper:
                continue

            if lang == "en":
                if not _is_english_set_name(name):
                    continue
            else:
                marker = LANG_MARKER.get(lang)
                if not marker or marker not in upper:
                    continue
                token = upper.split()[-1] if upper.split() else ""
                code_ok = token == code or token == key_code.upper() or code in upper.replace(" ", "")
                if not code_ok and key_code.upper() not in upper:
                    continue

            seen.add(key)
            candidates.append(key)

    if not candidates:
        return None
    if year_hint is not None:
        for name, year in candidates:
            if int(year) == int(year_hint):
                return name, year
    candidates.sort(key=lambda x: (x[0].startswith(" "), x[1], x[0]))
    return candidates[0]


def brg_pop_object(brg_card: dict[str, Any], asof_iso: str) -> dict[str, Any]:
    """Convert break.co.kr card pop into our table shape."""
    out: dict[str, Any] = {
        "10": None,
        "9": None,
        "8": None,
        "le7": None,
        "total": None,
        "source": "break",
        "asOf": asof_iso[:10],
        "brgScores": {},
        "setName": brg_card.get("setName"),
        "brgId": brg_card.get("id"),
    }
    le7 = 0
    for row in brg_card.get("pop") or []:
        score = str(row.get("manualScore") or "").strip()
        try:
            count = int(row.get("count"))
        except (TypeError, ValueError):
            continue
        out["brgScores"][score] = count
        col = BRG_TO_COL.get(score)
        if col:
            out[col] = (out[col] or 0) + count
        elif score not in {"", "-1"}:
            le7 += count
    out["le7"] = le7
    # Successful fetch: missing grade columns are real zeros, not "unknown".
    for col in ("10", "9", "8"):
        if out[col] is None:
            out[col] = 0
    for score in ("100", "90", "80"):
        out["brgScores"].setdefault(score, 0)
    try:
        out["total"] = int(brg_card.get("total"))
    except (TypeError, ValueError):
        scored = [v for k, v in out["brgScores"].items() if k not in {"-1"}]
        out["total"] = sum(scored) if scored else 0
    return out


def pick_brg_card(
    catalog_card: dict, brg_cards: list[dict[str, Any]]
) -> dict[str, Any] | None:
    want_num = normalize_num(catalog_card.get("number"))
    if not want_num:
        return None
    same_num = [c for c in brg_cards if normalize_num(c.get("cardNumber")) == want_num]
    if not same_num:
        return None
    if len(same_num) == 1:
        return same_num[0]

    want_name = normalize_name(catalog_card.get("nameEn"))
    if want_name:
        exact = [
            c
            for c in same_num
            if normalize_name(c.get("playerName")) == want_name
        ]
        if exact:
            same_num = exact
        else:
            partial = [
                c
                for c in same_num
                if want_name in normalize_name(c.get("playerName"))
                or normalize_name(c.get("playerName")) in want_name
            ]
            if partial:
                same_num = partial

    def total_of(c: dict) -> int:
        try:
            return int(c.get("total") or 0)
        except (TypeError, ValueError):
            return 0

    return max(same_num, key=total_of)


def apply_brg_to_live(
    live: dict,
    card_id: str,
    lang: str,
    brg_pop: dict[str, Any],
    asof_iso: str,
) -> None:
    variants = live.setdefault("cards", {}).setdefault(card_id, {})
    variant = variants.setdefault(lang, {})
    pop = variant.setdefault("pop", {})
    pop["BRG"] = brg_pop
    variant["updatedAt"] = asof_iso


def restore_brg_pops(live: dict, previous: dict | None) -> int:
    if not previous:
        return 0
    kept = 0
    prev_cards = previous.get("cards") or {}
    for card_id, variants in (live.get("cards") or {}).items():
        prev_variants = prev_cards.get(card_id) or {}
        for lang, variant in variants.items():
            prev = prev_variants.get(lang) or {}
            prev_brg = (prev.get("pop") or {}).get("BRG")
            if isinstance(prev_brg, dict) and prev_brg.get("source") == "break":
                variant.setdefault("pop", {})["BRG"] = prev_brg
                kept += 1
    return kept


def fetch_brg_for_packs(
    catalog: list[dict],
    packs: list[dict],
    live: dict,
    asof_iso: str,
    *,
    pack_id: str | None = None,
    langs: list[str] | None = None,
    sleep_s: float = 0.25,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Resolve BRG sets per pack×lang and overlay BRG pop onto matching live cards."""
    packs_by_id = {p["id"]: p for p in packs}
    live_ids = set((live.get("cards") or {}).keys())
    catalog_by_pack: dict[str, list[dict]] = {}
    for card in catalog:
        # Only attempt BRG for cards that exist in the live snapshot (Tier A/B)
        if live_ids and card["id"] not in live_ids:
            continue
        catalog_by_pack.setdefault(card["packId"], []).append(card)

    stats: dict[str, Any] = {
        "brgEnabled": True,
        "setsResolved": 0,
        "setsMissing": 0,
        "setsUnavailable": 0,
        "cardsMatched": 0,
        "cardsNoBrgEntry": 0,
        "cardsAttempted": 0,
        "brgEntriesFetched": 0,
        "dryRun": dry_run,
        "setMap": [],
        "errors": [],
    }

    target_packs = packs
    if pack_id:
        target_packs = [p for p in packs if p["id"] == pack_id]

    for pack in target_packs:
        pack_langs = langs or pack.get("languages") or []
        for lang in pack_langs:
            if lang not in LANG_MARKER:
                continue
            try:
                resolved = resolve_brg_set(pack, lang)
            except Exception as exc:  # noqa: BLE001
                stats["errors"].append(
                    {"packId": pack["id"], "lang": lang, "error": str(exc)[:200]}
                )
                stats["setsMissing"] += 1
                continue

            if not resolved:
                # EN often missing on break.co.kr — track separately from lookup failures
                if lang == "en":
                    stats["setsUnavailable"] += 1
                else:
                    stats["setsMissing"] += 1
                stats["setMap"].append(
                    {"packId": pack["id"], "lang": lang, "setName": None}
                )
                continue

            set_name, year = resolved
            stats["setsResolved"] += 1
            stats["setMap"].append(
                {
                    "packId": pack["id"],
                    "lang": lang,
                    "setName": set_name,
                    "year": year,
                }
            )
            if dry_run:
                continue

            try:
                brg_cards = fetch_set_pop(set_name, year)
            except Exception as exc:  # noqa: BLE001
                stats["errors"].append(
                    {
                        "packId": pack["id"],
                        "lang": lang,
                        "setName": set_name,
                        "error": str(exc)[:200],
                    }
                )
                continue

            stats["brgEntriesFetched"] += len(brg_cards)
            for card in catalog_by_pack.get(pack["id"], []):
                stats["cardsAttempted"] += 1
                hit = pick_brg_card(card, brg_cards)
                if not hit:
                    stats["cardsNoBrgEntry"] += 1
                    continue
                apply_brg_to_live(
                    live, card["id"], lang, brg_pop_object(hit, asof_iso), asof_iso
                )
                stats["cardsMatched"] += 1

            if sleep_s > 0:
                time.sleep(sleep_s)

    attempted = stats["cardsAttempted"] or 0
    matched = stats["cardsMatched"] or 0
    stats["matchRate"] = round(matched / attempted, 4) if attempted else None
    # Keep legacy key for older dashboards
    stats["cardsUnmatched"] = stats["cardsNoBrgEntry"]
    return stats
