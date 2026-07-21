# -*- coding: utf-8 -*-
"""Daily refresh of live/pop-price.json and data.js."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"

KST = timezone(timedelta(hours=9))

sys.path.insert(0, str(SCRIPTS))
from pokepop_snapshot import build_live_snapshot, write_data_bundle  # noqa: E402


def kst_today() -> str:
    return datetime.now(KST).strftime("%Y-%m-%d")


def kst_now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    now = datetime.now(KST)
    asof_iso = now.isoformat(timespec="seconds")
    packs = load_json(DATA / "packs.json")
    catalog = load_json(DATA / "catalog.json")

    live_path = DATA / "live" / "pop-price.json"
    previous = load_json(live_path) if live_path.exists() else {}

    live, stats = build_live_snapshot(catalog, packs, asof_iso, previous)

    last_run = {
        "ranAt": asof_iso,
        "stats": stats,
    }
    (DATA / "live" / "last-run.json").write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    write_data_bundle(DATA, packs, catalog, live, last_run)

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
