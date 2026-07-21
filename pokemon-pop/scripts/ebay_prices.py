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


def build_search_query(card: dict, pack: dict | None, lang: str) -> str:
    name = (card.get("nameEn") or card.get("nameJa") or card.get("nameKo") or "").strip()
    num = card_number_query(card.get("number"))
    set_hint = ""
    if pack:
        set_hint = (pack.get("nameShort") or pack.get("code") or "").strip()
    lang_hint = LANG_QUERY.get(lang, "")
    parts = [p for p in [name, num, set_hint, "Pokemon", "PSA", lang_hint] if p]
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


def grades_from_listings(items: list[dict[str, Any]]) -> dict[str, list[float]]:
    buckets: dict[str, list[float]] = {"10": [], "9": [], "8": []}
    for item in items:
        title = item.get("title") or ""
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


def median_int(values: list[float]) -> int | None:
    if not values:
        return None
    return int(round(statistics.median(values)))


def price_from_buckets(
    buckets: dict[str, list[float]], asof_iso: str
) -> dict[str, Any] | None:
    grades: dict[str, int] = {}
    samples: dict[str, int] = {}
    for g in ("10", "9", "8"):
        m = median_int(buckets.get(g) or [])
        if m is not None:
            grades[g] = m
            samples[g] = len(buckets[g])
    if not grades:
        return None
    return {
        "source": "eBay",
        "currency": "USD",
        "asOf": asof_iso[:10],
        "grades": grades,
        "sampleSize": samples,
        "method": "median-active",
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
    return price_from_buckets(grades_from_listings(items), asof_iso)


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
