# -*- coding: utf-8 -*-
"""Fetch GemRate PSA set POP (item-details-advanced) once per day.

Uses Playwright (real Chromium) because plain HTTP gets Cloudflare 403.
Writes slim JSON dumps + CSV under data/gemrate/, then applies into live pop.PSA.

Only packs listed in gemrate_pop.GEMRATE_SETS are fetched.
EN Mega Evolution is shared by Mega Brave + Mega Symphonia (reuseFrom).
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
    lang_meta,
    mark_live_source,
    resolve_dump_path,
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


def _page_debug_snapshot(page: Any) -> str:
    try:
        title = page.title()
        href = page.url
        body = (page.inner_text("body") or "").strip().replace("\n", " ")[:240]
        rd_type = page.evaluate(
            """() => {
              const rd = window.RowData;
              if (rd == null) return 'null';
              if (typeof rd === 'string') return 'string:' + rd.length;
              if (Array.isArray(rd)) return 'array:' + rd.length;
              return typeof rd;
            }"""
        )
        return f"title={title!r} url={href!r} RowData={rd_type} body={body!r}"
    except Exception as e:  # noqa: BLE001
        return f"debug-failed: {e}"


def fetch_row_data_with_playwright(
    url: str,
    *,
    timeout_ms: int = 180_000,
    retries: int = 2,
) -> list[dict[str, Any]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise SystemExit(
            "playwright is required. Install with:\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        ) from e

    last_err: Exception | None = None
    for attempt in range(1, max(1, retries) + 1):
        with sync_playwright() as p:
            # Prefer full Chromium over headless_shell — Cloudflare is less twitchy.
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = browser.new_context(
                viewport={"width": 1400, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                java_script_enabled=True,
            )
            page = context.new_page()
            try:
                page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                )
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                # Give Cloudflare / SPA a moment before polling RowData.
                page.wait_for_timeout(3_000)
                try:
                    page.wait_for_load_state("networkidle", timeout=min(30_000, timeout_ms))
                except Exception:  # noqa: BLE001
                    pass
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
            except Exception as e:  # noqa: BLE001
                snap = _page_debug_snapshot(page)
                browser.close()
                last_err = RuntimeError(f"{e} | {snap}")
                print(
                    f"[gemrate] attempt {attempt}/{retries} failed: {last_err}",
                    flush=True,
                )
                if attempt < retries:
                    time.sleep(5 * attempt)
                    continue
    assert last_err is not None
    raise last_err


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
        default=60.0,
        help="Seconds between set page fetches (default 60 — slower looks less bot-like)",
    )
    p.add_argument(
        "--timeout-ms",
        type=int,
        default=180_000,
        help="Playwright timeout per page (default 180000)",
    )
    p.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Fetch retries per set page (default 2)",
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
                reuse = meta.get("reuseFrom") if isinstance(meta, dict) else None
                if isinstance(reuse, dict) and reuse.get("packId"):
                    src_pack = str(reuse["packId"])
                    src_lang = str(reuse.get("lang") or lang)
                    src_path = dump_path_for(src_pack, src_lang)
                    fetch_stats.append(
                        {
                            "packId": pack_id,
                            "lang": lang,
                            "ok": src_path.is_file(),
                            "reusedFrom": f"{src_pack}/{src_lang}",
                            "skippedFetch": True,
                            "json": str(src_path.relative_to(ROOT)) if src_path.is_file() else None,
                            "error": None
                            if src_path.is_file()
                            else f"missing shared dump: {src_path.name}",
                        }
                    )
                    continue
                url = build_url(meta)
                try:
                    print(f"[gemrate] fetch {pack_id}/{lang} …", flush=True)
                    rows = fetch_row_data_with_playwright(
                        url,
                        timeout_ms=args.timeout_ms,
                        retries=args.retries,
                    )
                    if not rows:
                        raise RuntimeError("empty RowData")
                    json_path = write_dump(pack_id, lang, meta, rows, fetched_at)
                    csv_path = write_csv(pack_id, lang, rows)
                    print(
                        f"[gemrate] ok {pack_id}/{lang} rows={len(rows)}",
                        flush=True,
                    )
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
                    print(f"[gemrate] FAIL {pack_id}/{lang}: {e}", flush=True)
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
            path = resolve_dump_path(pack_id, lang)
            if not path.is_file():
                apply_stats.append(
                    {"packId": pack_id, "lang": lang, "error": f"missing dump: {path.name}"}
                )
                continue
            dump = json.loads(path.read_text(encoding="utf-8"))
            # Shared EN dump still says lang=en / Mega Evolution set name — OK for matching.
            meta = lang_meta(pack_id, lang) or {}
            reuse = meta.get("reuseFrom") if isinstance(meta, dict) else None
            stat = apply_dump_to_live(
                live,
                catalog,
                dump,
                pack_id=pack_id,
                lang=lang,
                asof_iso=asof_iso,
                dry_run=args.dry_run,
            )
            if isinstance(reuse, dict) and reuse.get("packId"):
                stat["reusedFrom"] = f"{reuse['packId']}/{reuse.get('lang') or lang}"
            apply_stats.append(stat)

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
