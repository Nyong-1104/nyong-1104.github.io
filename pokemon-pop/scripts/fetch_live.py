# -*- coding: utf-8 -*-
"""Daily refresh of live/pop-price.json and data.js.

BRG POP: always synced from break.co.kr unless --seed-only / --skip-brg.
Prices: eBay Browse medians when EBAY_CLIENT_ID / EBAY_CLIENT_SECRET are set.
Other graders: seed placeholders.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"

KST = timezone(timedelta(hours=9))

sys.path.insert(0, str(SCRIPTS))
from brg_pop import fetch_brg_for_packs, restore_brg_pops  # noqa: E402
from bwr_cards import ensure_bwr_cards  # noqa: E402
from ebay_prices import (  # noqa: E402
    fetch_ebay_batch,
    has_credentials,
    live_source_label,
    restore_ebay_prices,
)
from gemrate_pop import restore_psa_pops  # noqa: E402
from pokepop_snapshot import (  # noqa: E402
    assign_tiers_to_catalog,
    build_live_snapshot,
    write_data_bundle,
)


def load_dotenv(path: Path) -> None:
    """Minimal .env loader (KEY=VALUE). Does not override existing env."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Refresh PokePop live POP/price snapshot")
    p.add_argument(
        "--ebay-limit",
        type=int,
        default=int(os.environ.get("EBAY_FETCH_LIMIT", "200")),
        help="Max card×lang eBay searches this run (default 200)",
    )
    p.add_argument("--pack", default=None, help="Only refresh one pack id")
    p.add_argument(
        "--langs",
        default=None,
        help="Comma-separated langs to fetch (default: each pack's languages)",
    )
    p.add_argument(
        "--max-age-days",
        type=int,
        default=7,
        help="Re-fetch eBay prices older than this many days",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch eBay even if recent price exists",
    )
    p.add_argument(
        "--sleep",
        type=float,
        default=0.35,
        help="Seconds between eBay API calls",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan fetches but do not write overlays",
    )
    p.add_argument(
        "--seed-only",
        action="store_true",
        help="Skip eBay and BRG",
    )
    p.add_argument("--skip-brg", action="store_true", help="Skip BRG POP sync")
    p.add_argument("--skip-ebay", action="store_true", help="Skip eBay price sync")
    return p.parse_args(argv)


def has_break_brg(live: dict) -> bool:
    for variants in (live.get("cards") or {}).values():
        for v in variants.values():
            if ((v.get("pop") or {}).get("BRG") or {}).get("source") == "break":
                return True
    return False


def main(argv: list[str] | None = None) -> int:
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT.parent / ".env")
    args = parse_args(argv)

    now = datetime.now(KST)
    asof_iso = now.isoformat(timespec="seconds")
    packs = load_json(DATA / "packs.json")
    catalog = load_json(DATA / "catalog.json")
    catalog = ensure_bwr_cards(catalog, packs)
    tier_counts = assign_tiers_to_catalog(catalog)

    live_path = DATA / "live" / "pop-price.json"
    previous = load_json(live_path) if live_path.exists() else {}

    live, stats = build_live_snapshot(catalog, packs, asof_iso, previous)
    stats["tiers"] = tier_counts
    stats["ebayPricesRestored"] = restore_ebay_prices(live, previous)
    stats["brgPopsRestored"] = restore_brg_pops(live, previous)
    stats["psaPopsRestored"] = restore_psa_pops(live, previous)

    langs = [x.strip() for x in args.langs.split(",")] if args.langs else None

    brg_stats: dict = {"brgEnabled": False}
    if not args.seed_only and not args.skip_brg:
        brg_stats = fetch_brg_for_packs(
            catalog,
            packs,
            live,
            asof_iso,
            pack_id=args.pack,
            langs=langs,
            sleep_s=0.2,
            dry_run=args.dry_run,
        )

    ebay_stats: dict = {"ebayEnabled": False}
    if not args.seed_only and not args.skip_ebay and has_credentials():
        ebay_stats = fetch_ebay_batch(
            catalog,
            packs,
            live,
            asof_iso,
            limit=args.ebay_limit,
            pack_id=args.pack,
            langs=langs,
            max_age_days=args.max_age_days,
            force=args.force,
            sleep_s=args.sleep,
            dry_run=args.dry_run,
        )
    elif not args.seed_only and not args.skip_ebay:
        ebay_stats = {
            "ebayEnabled": False,
            "note": "Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET to enable eBay prices",
        }

    live["source"] = live_source_label(live)
    if has_break_brg(live):
        src = live["source"]
        if "BRG" not in src:
            live["source"] = f"{src}+BRG" if src != "seed" else "seed+BRG"

    live["generatedAt"] = asof_iso
    stats["brg"] = brg_stats
    stats["ebay"] = ebay_stats
    stats["liveSource"] = live["source"]

    last_run = {"ranAt": asof_iso, "stats": stats}
    (DATA / "live" / "last-run.json").write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if not args.dry_run:
        write_data_bundle(DATA, packs, catalog, live, last_run)

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
