# -*- coding: utf-8 -*-
"""Bundle packs.json, catalog.json, and live/pop-price.json into data.js."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def main():
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    live = json.loads((DATA / "live" / "pop-price.json").read_text(encoding="utf-8"))

    data_js = (
        "window.POP_PACKS = "
        + json.dumps(packs, ensure_ascii=False, indent=2)
        + ";\nwindow.POP_CATALOG = "
        + json.dumps(catalog, ensure_ascii=False, indent=2)
        + ";\nwindow.POP_LIVE = "
        + json.dumps(live, ensure_ascii=False, indent=2)
        + ";\n"
    )
    (DATA / "data.js").write_text(data_js, encoding="utf-8")
    print("data.js rebuilt")


if __name__ == "__main__":
    main()
