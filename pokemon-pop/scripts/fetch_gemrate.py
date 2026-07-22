# -*- coding: utf-8 -*-
"""Fetch GemRate PSA set POP (item-details-advanced) once per day.

Uses Playwright (real Chromium) because plain HTTP gets Cloudflare 403.
Writes slim JSON dumps + CSV under data/gemrate/, then applies into live pop.PSA.

Only packs listed in gemrate_pop.GEMRATE_SETS are fetched (pilot: sv2a-151).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
GEMRATE_DIR = DATA / "gemrate"
SCRIPTS = ROOT / "scripts"

KST = timezone(timedelta(hours=9))

sys.path.insert(0, str(SCRIPTS))
from gemrate_pop import (  # noqa: E402
    GEMRATE_SETS,
    apply_dump_to_live,
    dump_path_for,
    mark_live_source,
)
from pokepop_snapshot import write_data_bundle  # noqa: E402

ROW_KEEP = (
    "card_number",
    "name",
    "parallel",
    "g10",
    "g9",
    "g8",
    "card_total_grades",
    "card_total_standard",
    "gemrate_id",
    "card_gems",
    "details",
)

CSV_FIELDS = [
    "card_number",
    "name",
    "parallel",
    "g10",
    "g9",
    "g8",
    "card_gems",
    "card_total_grades",
    "gemrate_id",
    "details",
]


def slim_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: r.get(k) for k in ROW_KEEP} for r in rows]


def build_url(meta: dict[str, Any]) -> str:
    if meta.get("url"):
        return str(meta["url"])
    set_name = quote(str(meta["set_name"]), safe="+")
    year = meta.get("year", 2023)
    return (
        "https://www.gemrate.com/item-details-advanced"
        f"?grader=PSA&category=tcg-cards&year={year}&set_name={set_name}"
    )


def parse_row_data(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return []
        raw = json.loads(raw)
    if isinstance(raw, dict) and "rows" in raw:
        raw = raw["rows"]
    if not isinstance(raw, list):
        raise TypeError(f"Unexpected RowData type: {type(raw)}")
    return [r for r in raw if isinstance(r, dict)]


def fetch_row_data_with_playwright(url: str, *, timeout_ms: int = 90_000) -> list[dict[str, Any]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise SystemExit(
            "playwright is required. Install with:\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        ) from e

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_function(
            """() => {
              const rd = window.RowData;
              if (rd == null) return false;
              if (typeof rd === 'string') {
                try { return JSON.parse(rd).length > 0; } catch (e) { return false; }
              }
              return Array.isArray(rd) && rd.length > 0;
            }""",
            timeout=timeout_ms,
        )
        raw = page.evaluate("() => window.RowData")
        browser.close()
    return parse_row_data(raw)


def write_dump(
    pack_id: str,
    lang: str,
    meta: dict[str, Any],
    rows: list[dict[str, Any]],
    fetched_at: str,
) -> Path:
    GEMRATE_DIR.mkdir(parents=True, exist_ok=True)
    path = dump_path_for(pack_id, lang)
    payload = {
        "set": meta.get("set_name"),
        "lang": lang,
        "grader": "PSA",
        "year": meta.get("year"),
        "url": build_url(meta),
        "fetchedAt": fetched_at[:10],
        "rows": slim_rows(rows),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_csv(pack_id: str, lang: str, rows: list[dict[str, Any]]) -> Path:
    GEMRATE_DIR.mkdir(parents=True, exist_ok=True)
    path = GEMRATE_DIR / f"{pack_id}-{lang}.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in slim_rows(rows):
            writer.writerow(row)
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch GemRate PSA dumps and apply to live")
    p.add_argument("--pack", default=None, help="Only one pack id (default: all in GEMRATE_SETS)")
    p.add_argument(
        "--langs",
        default=None,
        help="Comma-separated langs (default: each pack's configured langs)",
    )
    p.add_argument(
        "--sleep",
        type=float,
        default=2.0,
        help="Seconds between set page fetches (default 2)",
    )
    p.add_argument("--fetch-only", action="store_true", help="Save dumps/CSV only, do not apply")
    p.add_argument("--apply-only", action="store_true", help="Skip fetch; apply existing dumps")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    asof_iso = datetime.now(KST).isoformat(timespec="seconds")
    fetched_at = asof_iso

    packs_cfg = GEMRATE_SETS
    pack_ids = [args.pack] if args.pack else list(packs_cfg.keys())
    lang_filter = (
        [x.strip() for x in args.langs.split(",") if x.strip()] if args.langs else None
    )

    fetch_stats: list[dict[str, Any]] = []
    apply_stats: list[dict[str, Any]] = []

    if not args.apply_only:
        for pack_id in pack_ids:
            pack_meta = packs_cfg.get(pack_id)
            if not pack_meta:
                fetch_stats.append({"packId": pack_id, "error": "not in GEMRATE_SETS"})
                continue
            langs = lang_filter or list(pack_meta.keys())
            for lang in langs:
                meta = pack_meta.get(lang)
                if not meta:
                    fetch_stats.append(
                        {"packId": pack_id, "lang": lang, "error": "lang not configured"}
                    )
                    continue
                url = build_url(meta)
                try:
                    rows = fetch_row_data_with_playwright(url)
                    if not rows:
                        raise RuntimeError("empty RowData")
                    json_path = write_dump(pack_id, lang, meta, rows, fetched_at)
                    csv_path = write_csv(pack_id, lang, rows)
                    fetch_stats.append(
                        {
                            "packId": pack_id,
                            "lang": lang,
                            "rows": len(rows),
                            "json": str(json_path.relative_to(ROOT)),
                            "csv": str(csv_path.relative_to(ROOT)),
                            "ok": True,
                        }
                    )
                except Exception as e:
                    fetch_stats.append(
                        {
                            "packId": pack_id,
                            "lang": lang,
                            "ok": False,
                            "error": str(e)[:400],
                        }
                    )
                time.sleep(max(0.0, args.sleep))

    if args.fetch_only:
        print(json.dumps({"fetch": fetch_stats}, ensure_ascii=False, indent=2))
        # Fail CI if any configured fetch failed
        if any(not s.get("ok") for s in fetch_stats if "ok" in s):
            return 1
        return 0

    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    live_path = DATA / "live" / "pop-price.json"
    live = json.loads(live_path.read_text(encoding="utf-8"))

    for pack_id in pack_ids:
        pack_meta = packs_cfg.get(pack_id) or {}
        langs = lang_filter or list(pack_meta.keys()) or ["jp", "kr", "en"]
        for lang in langs:
            path = dump_path_for(pack_id, lang)
            if not path.is_file():
                apply_stats.append(
                    {"packId": pack_id, "lang": lang, "error": f"missing dump: {path.name}"}
                )
                continue
            dump = json.loads(path.read_text(encoding="utf-8"))
            apply_stats.append(
                apply_dump_to_live(
                    live,
                    catalog,
                    dump,
                    pack_id=pack_id,
                    lang=lang,
                    asof_iso=asof_iso,
                    dry_run=args.dry_run,
                )
            )

    if not args.dry_run and any(s.get("matched") for s in apply_stats):
        mark_live_source(live)
        live["generatedAt"] = asof_iso
        last_run_path = DATA / "live" / "last-run.json"
        prev = {}
        if last_run_path.exists():
            try:
                prev = json.loads(last_run_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                prev = {}
        stats = dict(prev.get("stats") or {})
        stats["gemrateFetch"] = fetch_stats
        stats["gemratePsa"] = apply_stats
        last_run = {"ranAt": asof_iso, "stats": stats}
        write_data_bundle(DATA, packs, catalog, live, last_run)

    out = {"fetch": fetch_stats, "gemratePsa": apply_stats}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if fetch_stats and any(not s.get("ok") for s in fetch_stats if "ok" in s):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
