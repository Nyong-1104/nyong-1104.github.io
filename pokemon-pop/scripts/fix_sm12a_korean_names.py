# -*- coding: utf-8 -*-
"""Fix Japanese leftover nameKo/nameEn on SM12a GX Tag All Stars cards."""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_catalog import split_suffix  # noqa: E402
from pokepop_snapshot import write_data_bundle  # noqa: E402

PACK_ID = "sm12a-tag-all-stars"
JP_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
UA = {"User-Agent": "PokePopSm12aFix/1.0"}

# Official KR trainer / item / energy display names for SM12a leftovers.
# Species TAG TEAM names are resolved via dex; these cover non-species cards.
TRAINER_MAP: dict[str, tuple[str, str]] = {
    "ダートじてんしゃ": ("더트자전거", "Bike"),
    "電磁レーダー": ("전자레이더", "Electromagnetic Radar"),
    "ネットボール": ("넷트볼", "Net Ball"),
    "ビーストリング": ("비스트링", "Beast Ring"),
    "プレシャスボール": ("프레셔스볼", "Precious Ball"),
    "ぼうけんのカバン": ("모험가방", "Adventure Bag"),
    "ポケギア3.0": ("포켓기어3.0", "Pokégear 3.0"),
    "ポケモン通信": ("포켓몬통신", "Pokémon Communication"),
    "炎の結晶": ("불꽃결정", "Fire Crystal"),
    "ミステリートレジャー": ("미스터리 트레져", "Mysterious Treasure"),
    "リセットスタンプ": ("리셋 스탬프", "Reset Stamp"),
    "ロストミキサー": ("로스트믹서", "Lost Blender"),
    "くろおび": ("검은띠", "Karate Belt"),
    "のろいのおふだ": ("저주의부적", "Spell Tag"),
    "メタルコアバリア": ("메탈코어 배리어", "Metal Core Barrier"),
    "Uターンボード": ("U턴 보드", "U-Turn Board"),
    "アカギprismstar": ("태홍◇", "Cyrus ◇"),
    "アカギ◇": ("태홍◇", "Cyrus ◇"),
    "アカギ": ("태홍", "Cyrus"),
    "ウツギ博士のレクチャー": ("공박사의 강연", "Professor Elm's Lecture"),
    "エリカのおもてなし": ("민화의 대접", "Erika's Hospitality"),
    "カスミ&カンナ": ("이슬&칸나", "Misty & Lorelei"),
    "カルネ": ("카르네", "Diantha"),
    "ザオボー": ("자우보", "Faba"),
    "サカキの追放": ("비주기의 추방", "Giovanni's Exile"),
    "ジュジュベ&ハチクマン": ("주즈베&담죽맨", "Bellelba & Brycen-Man"),
    "デンジ": ("전진", "Volkner"),
    "ブルーの探索": ("블루의 탐색", "Blue's Exploration"),
    "マツバ": ("유빈", "Will"),
    "マツリカ": ("말리화", "Lusamine"),
    "溶接工": ("용접공", "Welder"),
    "ルチア": ("루티아", "Lisia"),
    "レッドの挑戦": ("레드의 도전", "Red's Challenge"),
    "戒めの祠": ("굴레의 사당", "Shrine of Punishment"),
    "格闘道場": ("격투 도장", "Martial Arts Dojo"),
    "巨大なカマド": ("거대한 화덕", "Giant Hearth"),
    "テンガン山": ("천관산", "Mt. Coronet"),
    "トキワの森": ("상록숲", "Viridian Forest"),
    "ヒートファクトリーprismstar": ("히트팩토리◇", "Heat Factory ◇"),
    "ヒートファクトリー◇": ("히트팩토리◇", "Heat Factory ◇"),
    "ブラックマーケットprismstar": ("블랙마켓◇", "Black Market ◇"),
    "ブラックマーケット◇": ("블랙마켓◇", "Black Market ◇"),
    "ライフフォレストprismstar": ("라이프 포레스트◇", "Life Forest ◇"),
    "ライフフォレスト◇": ("라이프 포레스트◇", "Life Forest ◇"),
    "ワンダーラビリンスprismstar": ("원더래버린스◇", "Wondrous Labyrinth ◇"),
    "ワンダーラビリンス◇": ("원더래버린스◇", "Wondrous Labyrinth ◇"),
    "超ブーストエネルギーprismstar": ("초 부스트 에너지◇", "Super Boost Energy ◇"),
    "超ブーストエネルギー◇": ("초 부스트 에너지◇", "Super Boost Energy ◇"),
    "トリプル加速エネルギー": ("트리플 가속 에너지", "Triple Acceleration Energy"),
    "ビーストエネルギーprismstar": ("비스트에너지◇", "Beast Energy ◇"),
    "ビーストエネルギー◇": ("비스트에너지◇", "Beast Energy ◇"),
    "リサイクルエネルギー": ("리사이클 에너지", "Recycle Energy"),
    "エーフィ&デオキシスGX": ("에브이&테오키스 GX", "Espeon & Deoxys GX"),
    "ブラッキー&ダークライGX": ("블래키&다크라이 GX", "Umbreon & Darkrai GX"),
    "イツキ": ("일목", "Clair"),
    "グリーンの戦略": ("그린의 전략", "Green's Strategy"),
    "ハプウ": ("하푸우", "Hapu"),
    "ホミカ": ("보미카", "Roxie"),
    "ヤーコン": ("야콘", "Clay"),
    "基本雷エネルギー": ("기본 번개 에너지", "Basic Lightning Energy"),
    "基本闘エネルギー": ("기본 격투 에너지", "Basic Fighting Energy"),
    "基本フェアリーエネルギー": ("기본 페어리 에너지", "Basic Fairy Energy"),
    # Already had KO from build_catalog, but EN was still JP
    "エレキパワー": ("일렉트릭파워", "Electropower"),
    "カスタムキャッチャー": ("커스텀 캐쳐", "Custom Catcher"),
    "カウンターゲイン": ("카운터 게인", "Counter Gain"),
    "かんこうきゃく": ("관광객", "Sightseer"),
    "サンダーマウンテンprismstar": ("썬더마운틴◇", "Thunder Mountain ◇"),
    "サンダーマウンテン◇": ("썬더마운틴◇", "Thunder Mountain ◇"),
    "基本草エネルギー": ("기본 풀 에너지", "Basic Grass Energy"),
    "基本炎エネルギー": ("기본 불 에너지", "Basic Fire Energy"),
    "基本水エネルギー": ("기본 물 에너지", "Basic Water Energy"),
    "基本超エネルギー": ("기본 초 에너지", "Basic Psychic Energy"),
    "基本悪エネルギー": ("기본 악 에너지", "Basic Darkness Energy"),
    "基本鋼エネルギー": ("기본 강철 에너지", "Basic Metal Energy"),
}

PREFIXES = (
    ("アローラ ", "알로라 ", "Alolan "),
    ("アローラ", "알로라 ", "Alolan "),
    ("ウルトラ", "울트라 ", "Ultra "),
)


def has_jp(text: str) -> bool:
    return bool(JP_RE.search(text or ""))


def http_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_species(lang: str) -> list[str]:
    return http_json(f"https://raw.githubusercontent.com/sindresorhus/pokemon/master/data/{lang}.json")


def normalize_ja(name: str) -> str:
    return (name or "").replace("prismstar", "◇").strip()


def resolve_species_part(part: str, ja_index: dict[str, int], ko_names: list[str], en_names: list[str]):
    work = part.strip()
    ko_p = en_p = ""
    for jp_p, ko_pref, en_pref in PREFIXES:
        if work.startswith(jp_p):
            work = work[len(jp_p) :]
            ko_p, en_p = ko_pref, en_pref
            break
    base, suffix, mega = split_suffix(work)
    base = base.strip()
    dex = ja_index.get(base) or ja_index.get(base.replace(" ", ""))
    if not dex:
        return None
    ko = ko_p + ko_names[dex - 1] + suffix
    en = en_p + en_names[dex - 1] + suffix
    if mega:
        ko = f"메가 {ko}"
        en = f"Mega {en}"
    return ko, en


def resolve_tag_or_species(jp_name: str, ja_index, ko_names, en_names):
    mapped = TRAINER_MAP.get(jp_name) or TRAINER_MAP.get(normalize_ja(jp_name))
    if mapped:
        return mapped

    base, suffix, mega = split_suffix(jp_name)
    if "&" in base:
        parts = base.split("&")
        resolved = []
        for part in parts:
            one = resolve_species_part(part, ja_index, ko_names, en_names)
            if not one:
                return None
            resolved.append(one)
        ko = "&".join(r[0] for r in resolved) + suffix
        en = " & ".join(r[1] for r in resolved) + suffix
        if mega:
            ko = f"메가 {ko}"
            en = f"Mega {en}"
        return ko, en

    return resolve_species_part(jp_name, ja_index, ko_names, en_names)


def needs_fix(card: dict) -> bool:
    ko = card.get("nameKo") or ""
    en = card.get("nameEn") or ""
    ja = card.get("nameJa") or ""
    if not ko.strip():
        return True
    if has_jp(ko):
        return True
    if ko == ja and has_jp(ja):
        return True
    if has_jp(en):
        return True
    return False


def main() -> int:
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    pack = next(p for p in packs if p["id"] == PACK_ID)
    card_ids = set(pack["cardIds"])

    print("Loading species lists…")
    ko_names = load_species("ko")
    en_names = load_species("en")
    ja_names = load_species("ja")
    ja_index = {name: i + 1 for i, name in enumerate(ja_names)}

    catalog_path = DATA / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    examples: list[dict] = []
    fixed = 0
    missing: list[str] = []

    for card in catalog:
        if card.get("id") not in card_ids:
            continue
        if not needs_fix(card):
            continue

        ja = card.get("nameJa") or card.get("nameKo") or ""
        mapped = resolve_tag_or_species(ja, ja_index, ko_names, en_names)
        if not mapped:
            mapped = resolve_tag_or_species(card.get("nameKo") or "", ja_index, ko_names, en_names)
        if not mapped:
            missing.append(f"{card['id']}:{ja}")
            continue

        new_ko, new_en = mapped
        before_ko = card.get("nameKo")
        changed = False
        if has_jp(card.get("nameKo") or "") or not (card.get("nameKo") or "").strip() or card.get("nameKo") == ja:
            card["nameKo"] = new_ko
            changed = True
        elif card.get("nameKo") != new_ko and has_jp(card.get("nameEn") or ""):
            # Prefer official KR spelling when we are already touching the card for EN
            card["nameKo"] = new_ko
            changed = True
        if has_jp(card.get("nameEn") or "") or card.get("nameEn") == ja:
            card["nameEn"] = new_en
            changed = True
        if "prismstar" in (card.get("nameJa") or ""):
            card["nameJa"] = normalize_ja(card["nameJa"])
            if card.get("rarity") == "PRISM" and "◇" not in (card.get("nameKo") or ""):
                card["nameKo"] = (card.get("nameKo") or "") + "◇"
            changed = True
        if not changed:
            missing.append(f"{card['id']}:{ja}:no_change")
            continue
        fixed += 1
        if len(examples) < 15:
            examples.append(
                {
                    "id": card["id"],
                    "before": before_ko,
                    "after": card["nameKo"],
                    "en": card["nameEn"],
                }
            )

    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    live = json.loads((DATA / "live" / "pop-price.json").read_text(encoding="utf-8"))
    write_data_bundle(DATA, packs, catalog, live)

    by_id = {c["id"]: c for c in catalog}
    still = []
    for cid in pack["cardIds"]:
        c = by_id[cid]
        if needs_fix(c):
            still.append({"id": cid, "nameKo": c.get("nameKo"), "nameEn": c.get("nameEn")})

    report = {
        "pack": PACK_ID,
        "fixed": fixed,
        "still_issues": len(still),
        "missing": missing,
        "examples": examples,
        "still_sample": still[:20],
    }
    out = SCRIPTS / "_sm12a_fix_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps({"fixed": fixed, "still_issues": len(still), "missing": missing}, ensure_ascii=True))
    return 1 if still or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
