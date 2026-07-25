# -*- coding: utf-8 -*-
"""eBay Browse API helpers — median active asking prices for PSA 10 / 9 / 8."""
from __future__ import annotations

import base64
import json
import os
import re
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
# Collectibles › Trading Cards › CCG Individual Cards
CATEGORY_CCG = "183454"
MARKETPLACE = "EBAY_US"
OAUTH_SCOPE = "https://api.ebay.com/oauth/api_scope"

GRADE_PATTERNS = {
    "10": re.compile(r"\bPSA\s*10\b", re.I),
    "9": re.compile(r"\bPSA\s*9\b(?!\s*[\.\d])", re.I),
    "8": re.compile(r"\bPSA\s*8\b(?!\s*[\.\d])", re.I),
}

LANG_QUERY = {
    "jp": "Japanese",
    "kr": "Korean",
    "en": "English",
}

# Collector numbers in titles: 080/073, 040/M-P, #040, No.040
_SLASH_NUM_RE = re.compile(r"\b#?\s*0*(\d{1,4})\s*/\s*([A-Za-z0-9-]{1,12})\b", re.I)
_HASH_NUM_RE = re.compile(r"#\s*0*(\d{1,4})\b")
_NO_NUM_RE = re.compile(r"\bNo\.?\s*0*(\d{1,4})\b", re.I)
# Strip PSA grade tokens before looking for bare numbers
_PSA_TOKEN_RE = re.compile(r"\bPSA\s*(?:10|9|8)\b", re.I)
# Common TCG set codes that appear in eBay titles (not exhaustive; conflict filter)
_SET_CODE_RE = re.compile(
    r"\b("
    r"SV\d{1,2}[A-Z]{0,2}|S\d{1,2}[A-Z]{0,2}|SM\d{1,2}[A-Z+]{0,2}|"
    r"SWSH\d{0,2}|XY\d{0,2}|BW\d{0,2}|CP\d{1,2}|"
    r"M\d{1,2}[A-Z]{0,2}"
    r")\b",
    re.I,
)
# Named sets that often appear instead of codes
_NAMED_SET_RE = re.compile(
    r"\b("
    r"TRIPLET\s*BEAT|151|CROWN\s*ZENITH|PALDEA\s*EVOLVED|"
    r"OBSIDIAN\s*FLAMES|PARADOX\s*RIFT|TEMPORAL\s*FORCES|"
    r"TWILIGHT\s*MASQUERADE|SHROUDED\s*FABLE|STELLAR\s*CROWN|"
    r"SURGING\s*SPARKS|PRISMATIC\s*EVOLUTIONS|JOURNEY\s*TOGETHER|"
    r"DESTINED\s*RIVALS|BLACK\s*BOLT|WHITE\s*FLARE"
    r")\b",
    re.I,
)
# Numbers that collide with PSA grades — require stronger patterns
_GRADE_COLLISION_NUMS = frozenset({"8", "9", "10"})


def has_credentials() -> bool:
    return bool(os.environ.get("EBAY_CLIENT_ID") and os.environ.get("EBAY_CLIENT_SECRET"))


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def get_app_token(client_id: str | None = None, client_secret: str | None = None) -> str:
    client_id = client_id or os.environ["EBAY_CLIENT_ID"]
    client_secret = client_secret or os.environ["EBAY_CLIENT_SECRET"]
    body = urllib.parse.urlencode(
        {"grant_type": "client_credentials", "scope": OAUTH_SCOPE}
    ).encode("utf-8")
    req = urllib.request.Request(
        EBAY_TOKEN_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": _basic_auth_header(client_id, client_secret),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"eBay token response missing access_token: {data}")
    return token


def card_number_query(number: str | None) -> str:
    """Prefer leading collector number (001 from 001/165)."""
    if not number:
        return ""
    head = str(number).split("/")[0].strip()
    return head


def card_number_suffix(number: str | None) -> str:
    """Trailing set/promo code from 040/M-P or 080/073."""
    if not number or "/" not in str(number):
        return ""
    return str(number).split("/", 1)[1].strip()


def normalize_num(value: str | None) -> str:
    """Normalize collector number to unpadded digits (040 → 40)."""
    if not value:
        return ""
    head = str(value).split("/")[0].strip()
    digits = re.sub(r"\D", "", head)
    if not digits:
        return head.upper()
    return str(int(digits))


def normalize_set_token(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^A-Z0-9]+", "", str(value).upper())


def is_promo_card(card: dict, pack: dict | None) -> bool:
    if (card.get("rarity") or "").upper() == "PROMO":
        return True
    if pack and (pack.get("listGroup") or "").lower() == "promo":
        return True
    code = normalize_set_token((pack or {}).get("code"))
    return bool(code.endswith("PROMO") or code.endswith("P") and len(code) <= 8)


def pack_identity_tokens(pack: dict | None, card: dict | None = None) -> set[str]:
    """Tokens that positively identify the pack/set in a listing title."""
    tokens: set[str] = set()
    if not pack:
        return tokens
    for key in ("code", "nameShort", "nameEn"):
        raw = (pack.get(key) or "").strip()
        if not raw:
            continue
        tokens.add(normalize_set_token(raw))
        for part in re.split(r"[\s/×x+\-–—]+", raw):
            norm = normalize_set_token(part)
            if len(norm) >= 2:
                tokens.add(norm)
    suffix = card_number_suffix((card or {}).get("number") if card else None)
    if suffix:
        tokens.add(normalize_set_token(suffix))
    # Korean MG promo cards print as M-P
    code = normalize_set_token(pack.get("code"))
    if code in {"MGPROMO", "MP"} or "FESTA" in normalize_set_token(
        pack.get("nameShort") or ""
    ):
        tokens.update({"MP", "MGFESTA", "MEGAFESTA", "SEOUL", "STAMP"})
    tokens.discard("")
    return tokens


def extract_title_card_numbers(title: str) -> list[tuple[str, str | None]]:
    """Return (normalized_num, suffix_or_None) from explicit card-number forms."""
    found: list[tuple[str, str | None]] = []
    for m in _SLASH_NUM_RE.finditer(title or ""):
        found.append((str(int(m.group(1))), m.group(2).upper()))
    for m in _HASH_NUM_RE.finditer(title or ""):
        found.append((str(int(m.group(1))), None))
    for m in _NO_NUM_RE.finditer(title or ""):
        found.append((str(int(m.group(1))), None))
    return found


def title_has_wanted_number(title: str, want_num: str, want_suffix: str = "") -> bool:
    """True if title clearly references the catalog collector number."""
    if not want_num:
        return True
    explicit = extract_title_card_numbers(title)
    slash_forms = [(n, s) for n, s in explicit if s]
    if slash_forms:
        for num, suffix in slash_forms:
            if num != want_num:
                continue
            if want_suffix:
                if normalize_set_token(suffix) == normalize_set_token(want_suffix):
                    return True
                continue
            # Catalog has no suffix (e.g. promo "040") — any 040/XXX is a number hit;
            # foreign set codes are rejected separately.
            return True
        return False

    for num, _suffix in explicit:
        if num == want_num:
            return True

    # Bare number (padded or not), avoiding PSA grade collisions
    if want_num in _GRADE_COLLISION_NUMS:
        return False
    stripped = _PSA_TOKEN_RE.sub(" ", title or "")
    padded = want_num.zfill(3)
    patterns = [
        rf"\b0*{re.escape(want_num)}\b",
        rf"\b{re.escape(padded)}\b",
    ]
    return any(re.search(p, stripped, re.I) for p in patterns)


def title_has_conflicting_number(title: str, want_num: str) -> bool:
    """Reject when title shows a different explicit collector number."""
    if not want_num:
        return False
    for num, _suffix in extract_title_card_numbers(title):
        if num != want_num:
            return True
    return False


def title_set_codes(title: str) -> set[str]:
    codes = {normalize_set_token(m.group(1)) for m in _SET_CODE_RE.finditer(title or "")}
    for m in _NAMED_SET_RE.finditer(title or ""):
        codes.add(normalize_set_token(m.group(1)))
    return {c for c in codes if c}


def title_has_pack_signal(title: str, pack_tokens: set[str]) -> bool:
    if not pack_tokens:
        return False
    title_norm = normalize_set_token(title)
    title_codes = title_set_codes(title)
    upper = (title or "").upper()
    for tok in pack_tokens:
        if len(tok) < 2:
            continue
        if tok in title_codes or tok in title_norm:
            return True
    for phrase in ("MG FESTA", "MEGA FESTA", "SEOUL STAMP", "M-P", "M/P"):
        if phrase in upper and normalize_set_token(phrase) in pack_tokens:
            return True
    return False


def title_has_foreign_set(title: str, pack_tokens: set[str]) -> bool:
    """True if title names a set/code that is clearly not our pack."""
    foreign = title_set_codes(title)
    if not foreign:
        return False
    for code in foreign:
        if code in pack_tokens:
            continue
        return True
    return False


def listing_matches_card(
    title: str, card: dict, pack: dict | None = None
) -> bool:
    """Return True when an eBay title plausibly refers to this catalog card."""
    want_num = normalize_num(card.get("number"))
    want_suffix = card_number_suffix(card.get("number"))
    pack_tokens = pack_identity_tokens(pack, card)
    promo = is_promo_card(card, pack)

    if want_num and title_has_conflicting_number(title, want_num):
        return False
    if want_num and not title_has_wanted_number(title, want_num, want_suffix):
        return False
    if title_has_foreign_set(title, pack_tokens):
        return False

    # Promos: name + PSA + language is too loose — require a set/promo signal
    if promo:
        explicit = extract_title_card_numbers(title)
        suffix_hit = bool(want_suffix) and any(
            n == want_num
            and s
            and normalize_set_token(s) == normalize_set_token(want_suffix)
            for n, s in explicit
        )
        if suffix_hit:
            return True
        if not title_has_pack_signal(title, pack_tokens):
            return False
    return True


def build_search_query(card: dict, pack: dict | None, lang: str) -> str:
    name = (card.get("nameEn") or card.get("nameJa") or card.get("nameKo") or "").strip()
    num = card_number_query(card.get("number"))
    suffix = card_number_suffix(card.get("number"))
    set_hint = ""
    if pack:
        set_hint = (pack.get("nameShort") or pack.get("code") or "").strip()
    lang_hint = LANG_QUERY.get(lang, "")
    parts = [p for p in [name, num, suffix, set_hint, "Pokemon", "PSA", lang_hint] if p]
    return " ".join(parts)


def ebay_web_search_url(card: dict, pack: dict | None, lang: str) -> str:
    q = build_search_query(card, pack, lang)
    params = urllib.parse.urlencode(
        {"_nkw": q, "_sacat": CATEGORY_CCG, "LH_TitleDesc": "0"}
    )
    return f"https://www.ebay.com/sch/i.html?{params}"


def _http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"eBay HTTP {e.code}: {detail[:500]}") from e


def search_item_summaries(
    token: str,
    q: str,
    *,
    limit: int = 50,
    marketplace: str = MARKETPLACE,
) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "q": q,
            "category_ids": CATEGORY_CCG,
            "limit": str(limit),
            "filter": "buyingOptions:{FIXED_PRICE|AUCTION}",
        }
    )
    url = f"{EBAY_SEARCH_URL}?{params}"
    data = _http_get_json(
        url,
        {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace,
            "Accept": "application/json",
        },
    )
    return list(data.get("itemSummaries") or [])


def _item_price_usd(item: dict[str, Any]) -> float | None:
    price = item.get("price") or {}
    currency = (price.get("currency") or "USD").upper()
    if currency != "USD":
        return None
    try:
        return float(price.get("value"))
    except (TypeError, ValueError):
        return None


def grades_from_listings(
    items: list[dict[str, Any]],
    card: dict | None = None,
    pack: dict | None = None,
) -> dict[str, list[float]]:
    buckets: dict[str, list[float]] = {"10": [], "9": [], "8": []}
    for item in items:
        title = item.get("title") or ""
        if card is not None and not listing_matches_card(title, card, pack):
            continue
        amount = _item_price_usd(item)
        if amount is None or amount <= 0:
            continue
        # Prefer the highest grade match in the title (PSA 10 before PSA 1)
        matched = None
        for grade in ("10", "9", "8"):
            if GRADE_PATTERNS[grade].search(title):
                matched = grade
                break
        if matched:
            buckets[matched].append(amount)
    return buckets


def mean_int(values: list[float]) -> int | None:
    if not values:
        return None
    return int(round(statistics.mean(values)))


def price_from_buckets(
    buckets: dict[str, list[float]], asof_iso: str
) -> dict[str, Any] | None:
    grades: dict[str, int] = {}
    samples: dict[str, int] = {}
    ranges: dict[str, dict[str, int]] = {}
    for g in ("10", "9", "8"):
        vals = buckets.get(g) or []
        avg = mean_int(vals)
        if avg is not None:
            grades[g] = avg
            samples[g] = len(vals)
            ranges[g] = {
                "min": int(round(min(vals))),
                "max": int(round(max(vals))),
            }
    if not grades:
        return None
    return {
        "source": "eBay",
        "currency": "USD",
        "asOf": asof_iso[:10],
        "grades": grades,
        "range": ranges,
        "sampleSize": samples,
        "listingCount": sum(samples.values()),
        "method": "mean-active",
    }


def fetch_card_lang_price(
    token: str,
    card: dict,
    pack: dict | None,
    lang: str,
    asof_iso: str,
    *,
    limit: int = 50,
) -> dict[str, Any] | None:
    q = build_search_query(card, pack, lang)
    items = search_item_summaries(token, q, limit=limit)
    return price_from_buckets(grades_from_listings(items, card, pack), asof_iso)


def restore_ebay_prices(live: dict, previous: dict | None) -> int:
    """Keep prior eBay price objects when rebuilding from seed."""
    if not previous:
        return 0
    prev_cards = previous.get("cards") or {}
    kept = 0
    for card_id, variants in (live.get("cards") or {}).items():
        prev_variants = prev_cards.get(card_id) or {}
        for lang, variant in variants.items():
            prev = prev_variants.get(lang) or {}
            prev_price = prev.get("price") or {}
            if prev_price.get("source") == "eBay" and prev_price.get("grades"):
                variant["price"] = prev_price
                if prev.get("updatedAt"):
                    variant["updatedAt"] = prev["updatedAt"]
                kept += 1
    return kept


def apply_ebay_price(
    live: dict, card_id: str, lang: str, price: dict, asof_iso: str
) -> None:
    cards = live.setdefault("cards", {})
    variants = cards.setdefault(card_id, {})
    variant = variants.setdefault(lang, {})
    variant["price"] = price
    variant["updatedAt"] = asof_iso


def needs_ebay_refresh(variant: dict | None, max_age_days: int = 7) -> bool:
    if not variant:
        return True
    price = variant.get("price") or {}
    if price.get("source") != "eBay":
        return True
    asof = price.get("asOf")
    if not asof:
        return True
    # YYYY-MM-DD — refresh if older than max_age_days (caller may also force)
    try:
        from datetime import date

        d = date.fromisoformat(str(asof)[:10])
        age = (date.today() - d).days
        return age >= max_age_days
    except ValueError:
        return True


def select_refresh_targets(
    catalog: list[dict],
    packs_by_id: dict[str, dict],
    live: dict,
    *,
    limit: int,
    pack_id: str | None = None,
    langs: list[str] | None = None,
    max_age_days: int = 7,
    force: bool = False,
) -> list[tuple[dict, dict | None, str]]:
    """Return (card, pack, lang) jobs prioritized by missing/stale eBay price."""
    jobs: list[tuple[dict, dict | None, str]] = []
    live_cards = live.get("cards") or {}
    for card in catalog:
        if pack_id and card.get("packId") != pack_id:
            continue
        pack = packs_by_id.get(card["packId"])
        card_langs = langs or (pack.get("languages") if pack else None) or ["jp"]
        for lang in card_langs:
            variant = (live_cards.get(card["id"]) or {}).get(lang)
            if force or needs_ebay_refresh(variant, max_age_days=max_age_days):
                jobs.append((card, pack, lang))
    # Prefer higher seed basePrice first (more useful market signal)
    jobs.sort(
        key=lambda row: -int((row[0].get("seed") or {}).get("basePrice") or 0)
    )
    return jobs[: max(0, limit)]


def fetch_ebay_batch(
    catalog: list[dict],
    packs: list[dict],
    live: dict,
    asof_iso: str,
    *,
    limit: int = 200,
    pack_id: str | None = None,
    langs: list[str] | None = None,
    max_age_days: int = 7,
    force: bool = False,
    sleep_s: float = 0.35,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Fetch a batch of eBay prices and merge into live. Returns stats."""
    stats: dict[str, Any] = {
        "ebayEnabled": True,
        "jobsPlanned": 0,
        "jobsOk": 0,
        "jobsEmpty": 0,
        "jobsFailed": 0,
        "dryRun": dry_run,
    }
    if not has_credentials():
        stats["ebayEnabled"] = False
        return stats

    packs_by_id = {p["id"]: p for p in packs}
    jobs = select_refresh_targets(
        catalog,
        packs_by_id,
        live,
        limit=limit,
        pack_id=pack_id,
        langs=langs,
        max_age_days=max_age_days,
        force=force,
    )
    stats["jobsPlanned"] = len(jobs)
    if dry_run or not jobs:
        return stats

    token = get_app_token()
    for i, (card, pack, lang) in enumerate(jobs):
        try:
            price = fetch_card_lang_price(token, card, pack, lang, asof_iso)
            if price:
                apply_ebay_price(live, card["id"], lang, price, asof_iso)
                stats["jobsOk"] += 1
            else:
                stats["jobsEmpty"] += 1
        except Exception as exc:  # noqa: BLE001 — continue batch
            stats["jobsFailed"] += 1
            stats.setdefault("errors", []).append(
                {"cardId": card.get("id"), "lang": lang, "error": str(exc)[:200]}
            )
            # Re-auth once on 401-ish failures
            if "401" in str(exc) or "access token" in str(exc).lower():
                try:
                    token = get_app_token()
                except Exception:
                    break
        if sleep_s > 0 and i + 1 < len(jobs):
            time.sleep(sleep_s)

    return stats


def live_source_label(live: dict) -> str:
    cards = live.get("cards") or {}
    ebay = 0
    total = 0
    for variants in cards.values():
        for v in variants.values():
            total += 1
            if (v.get("price") or {}).get("source") == "eBay":
                ebay += 1
    if ebay == 0:
        return "seed"
    if ebay >= total:
        return "eBay"
    return "eBay+seed"
