# -*- coding: utf-8 -*-
"""
Build packs.json + catalog.json for all cards in the three PokePop packs.

Sources:
  - type-null/PTCG-database (JP card meta + images from pokemon-card.com)
  - sindresorhus/pokemon (KO / EN species names by Pokédex number)
  - TCGdex EN set sv03.5 (English card names for 151, when available)
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
KST = timezone(timedelta(hours=9))

sys.path.insert(0, str(SCRIPTS))
from pokepop_snapshot import build_live_snapshot, write_data_bundle  # noqa: E402
from bwr_cards import ensure_bwr_cards  # noqa: E402

GITHUB_RAW = "https://raw.githubusercontent.com/type-null/PTCG-database/main/data_jp"
GITHUB_API = "https://api.github.com/repos/type-null/PTCG-database/contents/data_jp"
UA = {"User-Agent": "PokePopCatalogBuilder/1.0"}

TYPE_MAP = {
    "Grass": ("grass", "풀"),
    "Fire": ("fire", "불"),
    "Water": ("water", "물"),
    "Electric": ("lightning", "번개"),
    "Lightning": ("lightning", "번개"),
    "Psychic": ("psychic", "초"),
    "Fighting": ("fighting", "격투"),
    "Darkness": ("darkness", "악"),
    "Dark": ("darkness", "악"),
    "Metal": ("metal", "강철"),
    "Steel": ("metal", "강철"),
    "Fairy": ("fairy", "페어리"),
    "Dragon": ("dragon", "드래곤"),
    "Colorless": ("colorless", "무색"),
}

RARITY_MAP = {
    "rare_c_c": "C",
    "rare_u_c": "U",
    "rare_r_c": "R",
    "rare_rr": "RR",
    "rare_sr_c": "SR",
    "rare_sr": "SR",
    "rare_ar": "AR",
    "rare_sar": "SAR",
    "rare_ur_c": "UR",
    "rare_ur": "UR",
    "rare_hr": "HR",
    "rare_bwr": "BWR",
    "bwr": "BWR",
    "prismstar": "PRISM",
}

SEED_BY_RARITY = {
    "BWR": (280, 120),
    "SAR": (220, 900),
    "SIR": (200, 850),
    "HR": (160, 220),
    "UR": (90, 280),
    "SR": (95, 420),
    "RRR": (70, 180),
    "AR": (35, 2400),
    "RR": (45, 520),
    "PRISM": (50, 400),
    "R": (22, 650),
    "U": (10, 120),
    "C": (6, 90),
}

PACKS = [
    {
        "id": "sv2a-151",
        "nameKo": "포켓몬카드 151",
        "nameEn": "Pokémon Card 151",
        "nameJa": "ポケモンカード151",
        "nameShort": "151",
        "code": "sv2a",
        "releaseYear": 2023,
        "languages": ["jp", "kr", "en"],
        "blurb": "원조 151마리를 모은 강화 확장팩. 리자몽·뮤 SAR가 대표 카드입니다.",
        "blurbEn": "Enhanced expansion featuring the original 151. Charizard and Mew SARs headline the set.",
        "blurbJa": "初代151匹を集めた強化拡張パック。リザードン・ミュウSARが代表カードです。",
        "packImage": "./assets/pack-151.png",
        "coverCardId": "sv2a-201",
        "sourceFolder": "SV2a",
        "idPrefix": "sv2a",
    },
    {
        "id": "pokekyun",
        "nameKo": "포켓심쿵 컬렉션",
        "nameEn": "PokéKyun Collection",
        "nameJa": "ポケキュンコレクション",
        "code": "CP3",
        "releaseYear": 2016,
        "languages": ["jp", "kr"],
        "blurb": "2016년 발매된 귀여움 특화 세트. 피카츄·데덴네가 대표 카드입니다.",
        "blurbEn": "A 2016 cute-themed concept set. Pikachu and Dedenne are the face cards.",
        "blurbJa": "2016年発売のかわいい特化セット。ピカチュウ・デデンネが代表カードです。",
        "packImage": "./assets/pack-pokekyun.png",
        "coverCardId": "cp3-010",
        "sourceFolder": "CP3",
        "idPrefix": "cp3",
    },
    {
        "id": "thunderclap-spark",
        "nameKo": "플라스마 스파크",
        "nameEn": "Plasma Spark",
        "nameJa": "迅雷スパーク",
        "code": "sm7a",
        "releaseYear": 2018,
        "languages": ["jp", "kr"],
        "blurb": "썬&문 강화 확장팩. 제라오라 GX·게노세크트 GX가 대표 카드입니다.",
        "blurbEn": "Sun & Moon enhanced expansion. Zeraora-GX and Genesect-GX headline the set.",
        "blurbJa": "サン＆ムーン強化拡張パック。ゼラオラGX・ゲノセクトGXが代表カードです。",
        "packImage": "./assets/pack-ThunderclapSpark.png",
        "coverCardId": "sm7a-063",
        "sourceFolder": "SM7a",
        "idPrefix": "sm7a",
    },
]


def http_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_species_names(lang: str) -> list[str]:
    url = f"https://raw.githubusercontent.com/sindresorhus/pokemon/master/data/{lang}.json"
    return http_json(url)


def list_github_folder(folder: str) -> list[dict]:
    return http_json(f"{GITHUB_API}/{folder}")


def fetch_jp_cards(folder: str) -> list[dict]:
    cache_dir = DATA / "_tmp" / "jp_cards" / folder
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest = cache_dir / "_files.json"
    if manifest.exists():
        files = json.loads(manifest.read_text(encoding="utf-8"))
    else:
        files = list_github_folder(folder)
        manifest.write_text(json.dumps(files, ensure_ascii=False), encoding="utf-8")

    by_num: dict[str, dict] = {}
    for f in files:
        name = f.get("name") or ""
        if not name.endswith(".json"):
            continue
        local = cache_dir / name
        if local.exists():
            card = json.loads(local.read_text(encoding="utf-8"))
        else:
            card = http_json(f["download_url"])
            local.write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")
        raw_num = str(card.get("number") or "")
        num = raw_num.split("/")[0].zfill(3)
        prev = by_num.get(num)
        if prev is None or ("/" in raw_num and "/" not in str(prev.get("number") or "")):
            by_num[num] = card
    return [by_num[k] for k in sorted(by_num.keys(), key=lambda x: int(x))]


def build_ja_dex_index(ja_names: list[str]) -> dict[str, int]:
    """Map Japanese species name -> national dex (1-based)."""
    index: dict[str, int] = {}
    for i, name in enumerate(ja_names):
        index[name] = i + 1
        # Also index without dakuten variants if needed later
    return index


# Common JP trainer/item display names → Korean (SV2a + frequent SM/XY goods)
TRAINER_KO = {
    "エネルギーシール": "에너지 스티커",
    "スナッチアーム": "스내치 암",
    "古びたかいの化石": "낡은 조개의 화석",
    "古びたこうらの化石": "낡은 등껍질의 화석",
    "古びたひみつのコハク": "낡은 비밀의 호박",
    "安全ゴーグル": "안전 고글",
    "大きなふうせん": "큰 풍선",
    "ガチガチバンド": "단단한 밴드",
    "たべのこし": "먹다 남은 음식",
    "エリカの招待": "민화의 초대",
    "サカキのカリスマ": "비주의 카리스마",
    "ナナミの手助け": "나미의 도움",
    "マサキ의転送": "마사키의 전송",
    "マサキの転送": "마사키의 전송",
    "サイクリングロード": "사이클링 로드",
    "ポケモンいれかえ": "포켓몬 교체",
    "基本超エネルギー": "기본 초 에너지",
    "エネルギーつけかえ": "에너지 붙이기",
    "エレキパワー": "일렉파워",
    "カスタムキャッチャー": "커스텀 캐처",
    "スーパーポケモン回収": "슈퍼 포켓몬 회수",
    "ハイパーボール": "하이퍼볼",
    "ポケモンキャッチャー": "포켓몬 캐처",
    "ミックスハーブ": "믹스 허브",
    "カウンターゲイン": "카운터 게인",
    "こだわりハチマキ": "고집 머리띠",
    "カヒリ": "카힐리",
    "かんこうきゃく": "관광객",
    "ジャッジマン": "저지맨",
    "サンダーマウンテン◇": "썬더마운틴◇",
    "サンダーマウンテン": "썬더마운틴",
    "ダブル無色エネルギー": "더블 무색 에너지",
    "ユニットエネルギー草炎水": "유닛 에너지 풀불물",
    "おはなのかんむり": "꽃의 화관",
    "ミツル": "미츠루",
    # Expanded trainers / forms (also used by fix_korean_names.py)
    "基本草エネルギー": "기본 풀 에너지",
    "基本炎エネルギー": "기본 불 에너지",
    "基本水エネルギー": "기본 물 에너지",
    "基本悪エネルギー": "기본 악 에너지",
    "基本鋼エネルギー": "기본 강철 에너지",
    "メガシグナル": "메가 시그널",
    "アイアンディフェンダー": "아이언 디펜더",
    "パワープロテイン": "파워 프로틴",
    "ファイトゴング": "파이트 공",
    "むしよけスプレー": "벌레 퇴치 스프레이",
    "マチスの取引": "마티스의 거래",
    "リーリエの決心": "릴리에의 결심",
    "危ない廃墟": "위험한 폐허",
}


def map_rarity(raw: str | None, card: dict | None = None) -> str:
    """Map PTCG-database rarity codes. BWR is never inferred — only whitelist overrides."""
    _ = card
    if not raw:
        return "C"
    mapped = RARITY_MAP.get(raw)
    if mapped:
        return mapped
    cleaned = raw.upper().replace("RARE_", "").replace("_C", "")
    if cleaned in {
        "BWR",
        "SAR",
        "SIR",
        "SSR",
        "S_2",
        "HR",
        "UR",
        "SR",
        "AR",
        "RR",
        "RRR",
        "PRISM",
        "R",
        "U",
        "C",
        "PROMO",
    }:
        return cleaned
    return cleaned[:6] or "C"


def map_type(card: dict) -> tuple[str, str]:
    types = card.get("types") or []
    if types:
        return TYPE_MAP.get(types[0], ("colorless", "무색"))
    ctype = (card.get("card_type") or "").lower()
    if "pokemon" in ctype or "ポケモン" in (card.get("card_type") or ""):
        return "colorless", "무색"
    return "trainer", "트레이너"


def holo_for_rarity(rarity: str) -> str:
    if rarity in {"SAR", "SIR", "BWR"}:
        return "sar"
    if rarity == "AR":
        return "reverse"
    if rarity in {"SR", "HR", "UR", "RR", "PRISM", "SSR", "S_2"}:
        return "holo"
    return "reverse"


def split_suffix(jp_name: str) -> tuple[str, str, bool]:
    """Return (base_jp_for_lookup, display_suffix, is_mega)."""
    name = jp_name.strip()
    name = name.replace("◇", "").replace("◆", "").replace("prismstar", "").strip()
    mega = False
    # Latin "Mega …" or Japanese "メガ…"
    if name.lower().startswith("mega"):
        mega = True
        name = name[4:].lstrip()
    elif name.startswith("メガ"):
        mega = True
        name = name[2:].lstrip()
    for suffix, label in (
        ("VMAX", " VMAX"),
        ("V-UNION", " V-UNION"),
        ("GX", " GX"),
        ("EX", " EX"),
        ("ex", " ex"),
        ("V", " V"),
    ):
        if name.endswith(suffix):
            return name[: -len(suffix)].strip(), label, mega
    return name, "", mega


def species_name(names: list[str], dex: int | None, suffix: str, mega: bool = False) -> str | None:
    if not dex or dex < 1 or dex > len(names):
        return None
    base = names[dex - 1]
    if mega:
        # ko list uses plain names; prefix in Korean / English separately in caller
        pass
    return base + suffix


def resolve_dex(card: dict, jp_name: str, ja_index: dict[str, int]) -> tuple[int | None, bool]:
    base, _, mega = split_suffix(jp_name)
    dex = card.get("pokedex_number")
    try:
        if dex not in (None, ""):
            return int(dex), mega
    except (TypeError, ValueError):
        pass
    return ja_index.get(base), mega


def seed_for(rarity: str, name_en: str, name_jp: str) -> dict:
    base_price, base_pop = SEED_BY_RARITY.get(rarity, (15, 150))
    bump = 1.0
    blob = f"{name_en} {name_jp}".lower()
    if "v-union" in blob or "vunion" in blob.replace("-", ""):
        bump = 12.0
    elif any(k in blob for k in ("charizard", "リザードン", "리자몽")):
        bump = 2.4 if rarity in {"SAR", "HR", "SR", "SAR"} else 1.6
    elif any(k in blob for k in ("mew", "ミュウ", "뮤")) and "mewtwo" not in blob and "ミュウツー" not in blob:
        bump = 1.8 if rarity in {"SAR", "HR", "SR"} else 1.35
    elif any(k in blob for k in ("pikachu", "ピカチュウ", "피카츄")):
        bump = 2.2 if rarity in {"SAR", "HR", "SR", "RR"} else 1.5
    elif any(k in blob for k in ("zeraora", "ゼラオラ", "제라오라")):
        bump = 1.7
    elif rarity in {"SAR", "SIR", "HR"}:
        bump = 1.8
    return {
        "basePrice": max(5, int(base_price * bump)),
        "basePop": max(10, int(base_pop / max(bump * 0.7, 0.5))),
    }


def number_display(card: dict) -> str:
    raw = str(card.get("number") or "")
    if "/" in raw:
        return raw
    total = str(card.get("set_total") or "").zfill(3) if card.get("set_total") else None
    num = raw.split("/")[0].zfill(3)
    return f"{num}/{total}" if total else num


def to_catalog_card(
    card: dict,
    pack: dict,
    ko_names: list[str],
    en_names: list[str],
    ja_index: dict[str, int],
) -> dict:
    num = str(card.get("number") or "").split("/")[0].zfill(3)
    rarity = map_rarity(card.get("rarity"), card)
    type_id, type_ko = map_type(card)
    jp_name = card.get("name") or f"Card {num}"
    base_jp, suffix, mega = split_suffix(jp_name)
    dex_i, _mega_flag = resolve_dex(card, jp_name, ja_index)
    mega = mega or _mega_flag

    name_ko = species_name(ko_names, dex_i, suffix)
    name_en = species_name(en_names, dex_i, suffix)
    if name_ko and mega:
        name_ko = f"메가 {name_ko}"
    if name_en and mega:
        name_en = f"M {name_en}"
    if not name_ko:
        name_ko = TRAINER_KO.get(jp_name) or TRAINER_KO.get(base_jp) or TRAINER_KO.get(base_jp + "◇") or jp_name
    if not name_en:
        name_en = jp_name

    # Prism star marker
    if rarity == "PRISM" and "◇" not in name_ko:
        name_ko = name_ko + "◇"
        if "◇" not in name_en:
            name_en = f"{name_en} ◇"
    seed = seed_for(rarity, name_en or "", jp_name)
    jp_img = card.get("img") or ""
    return {
        "id": f"{pack['idPrefix']}-{num}",
        "packId": pack["id"],
        "nameKo": name_ko,
        "nameEn": name_en or jp_name,
        "nameJa": jp_name,
        "number": number_display(card),
        "rarity": rarity,
        "type": type_id,
        "typeKo": type_ko,
        "holoStyle": holo_for_rarity(rarity),
        "image": jp_img,
        "images": {"jp": jp_img, "kr": None, "en": None},
        "catalogKeys": {"jp": card.get("jp_id"), "kr": None, "en": None},
        "seed": seed,
    }


# Manual extras: SM7a secret rares missing from the scraped folder (067–073)
SM7A_EXTRAS = [
    {
        "id": "sm7a-067",
        "packId": "thunderclap-spark",
        "nameKo": "비리디온 GX",
        "nameEn": "Virizion GX",
        "nameJa": "ビリジオンGX",
        "number": "067/060",
        "rarity": "HR",
        "type": "grass",
        "typeKo": "풀",
        "holoStyle": "sar",
        "image": "https://images.pokemontcg.io/sm8/196_hires.png",
        "images": {
            "jp": "https://images.pokemontcg.io/sm8/196_hires.png",
            "kr": None,
            "en": "https://images.pokemontcg.io/sm8/196_hires.png",
        },
        "catalogKeys": {"jp": None, "kr": None, "en": None},
        "seed": {"basePrice": 280, "basePop": 140},
    },
    {
        "id": "sm7a-068",
        "packId": "thunderclap-spark",
        "nameKo": "마그카르고 GX",
        "nameEn": "Magcargo GX",
        "nameJa": "マグカルゴGX",
        "number": "068/060",
        "rarity": "HR",
        "type": "fire",
        "typeKo": "불",
        "holoStyle": "sar",
        "image": "https://images.pokemontcg.io/sm8/202_hires.png",
        "images": {
            "jp": "https://images.pokemontcg.io/sm8/202_hires.png",
            "kr": None,
            "en": "https://images.pokemontcg.io/sm8/202_hires.png",
        },
        "catalogKeys": {"jp": None, "kr": None, "en": None},
        "seed": {"basePrice": 240, "basePop": 150},
    },
    {
        "id": "sm7a-069",
        "packId": "thunderclap-spark",
        "nameKo": "제라오라 GX",
        "nameEn": "Zeraora GX",
        "nameJa": "ゼラオラGX",
        "number": "069/060",
        "rarity": "HR",
        "type": "lightning",
        "typeKo": "번개",
        "holoStyle": "sar",
        "image": "https://images.pokemontcg.io/sm8/201_hires.png",
        "images": {
            "jp": "https://images.pokemontcg.io/sm8/201_hires.png",
            "kr": None,
            "en": "https://images.pokemontcg.io/sm8/201_hires.png",
        },
        "catalogKeys": {"jp": None, "kr": None, "en": None},
        "seed": {"basePrice": 320, "basePop": 180},
    },
    {
        "id": "sm7a-070",
        "packId": "thunderclap-spark",
        "nameKo": "게노세크트 GX",
        "nameEn": "Genesect GX",
        "nameJa": "ゲノセクトGX",
        "number": "070/060",
        "rarity": "HR",
        "type": "metal",
        "typeKo": "강철",
        "holoStyle": "sar",
        "image": "https://images.pokemontcg.io/sm8/60_hires.png",
        "images": {
            "jp": "https://images.pokemontcg.io/sm8/60_hires.png",
            "kr": None,
            "en": "https://images.pokemontcg.io/sm8/60_hires.png",
        },
        "catalogKeys": {"jp": None, "kr": None, "en": None},
        "seed": {"basePrice": 260, "basePop": 160},
    },
    {
        "id": "sm7a-071",
        "packId": "thunderclap-spark",
        "nameKo": "일렉파워",
        "nameEn": "Electropower",
        "nameJa": "エレキパワー",
        "number": "071/060",
        "rarity": "UR",
        "type": "trainer",
        "typeKo": "트레이너",
        "holoStyle": "holo",
        "image": "https://images.pokemontcg.io/sm8/172_hires.png",
        "images": {
            "jp": "https://images.pokemontcg.io/sm8/172_hires.png",
            "kr": None,
            "en": "https://images.pokemontcg.io/sm8/172_hires.png",
        },
        "catalogKeys": {"jp": None, "kr": None, "en": None},
        "seed": {"basePrice": 90, "basePop": 220},
    },
    {
        "id": "sm7a-072",
        "packId": "thunderclap-spark",
        "nameKo": "커스텀 캐처",
        "nameEn": "Custom Catcher",
        "nameJa": "カスタムキャッチャー",
        "number": "072/060",
        "rarity": "UR",
        "type": "trainer",
        "typeKo": "트레이너",
        "holoStyle": "holo",
        "image": "https://images.pokemontcg.io/sm8/171_hires.png",
        "images": {
            "jp": "https://images.pokemontcg.io/sm8/171_hires.png",
            "kr": None,
            "en": "https://images.pokemontcg.io/sm8/171_hires.png",
        },
        "catalogKeys": {"jp": None, "kr": None, "en": None},
        "seed": {"basePrice": 70, "basePop": 200},
    },
    {
        "id": "sm7a-073",
        "packId": "thunderclap-spark",
        "nameKo": "카운터 게인",
        "nameEn": "Counter Gain",
        "nameJa": "カウンターゲイン",
        "number": "073/060",
        "rarity": "UR",
        "type": "trainer",
        "typeKo": "트레이너",
        "holoStyle": "holo",
        "image": "https://images.pokemontcg.io/sm8/170_hires.png",
        "images": {
            "jp": "https://images.pokemontcg.io/sm8/170_hires.png",
            "kr": None,
            "en": "https://images.pokemontcg.io/sm8/170_hires.png",
        },
        "catalogKeys": {"jp": None, "kr": None, "en": None},
        "seed": {"basePrice": 75, "basePop": 210},
    },
]


def load_en_151_images() -> tuple[dict[str, str], dict[str, list[tuple[str, str]]]]:
    """Return (by_local_id, by_normalized_name -> [(localId, imageUrl)])."""
    try:
        data = http_json("https://api.tcgdex.net/v2/en/sets/sv03.5")
    except Exception:
        return {}, {}
    by_id: dict[str, str] = {}
    by_name: dict[str, list[tuple[str, str]]] = {}
    for c in data.get("cards") or []:
        lid = str(c.get("localId") or "").zfill(3)
        base = c.get("image")
        if not base:
            continue
        url = base if base.endswith((".png", ".webp", ".jpg")) else f"{base}/high.webp"
        by_id[lid] = url
        key = re.sub(r"[^a-z0-9]+", "", (c.get("name") or "").lower())
        by_name.setdefault(key, []).append((lid, url))
    return by_id, by_name


def attach_multilang_images(catalog: list[dict]) -> None:
    """Attach EN images for 151 where possible. KR is filled separately from KR sources."""
    en_by_id, en_by_name = load_en_151_images()

    def pick_en(card: dict) -> str | None:
        num = str(card.get("number") or "").split("/")[0].zfill(3)
        try:
            n = int(num)
        except ValueError:
            n = 0
        # Main 151 Pokémon numbers usually align JP↔EN
        if 1 <= n <= 151 and num in en_by_id:
            return en_by_id[num]
        key = re.sub(r"[^a-z0-9]+", "", (card.get("nameEn") or "").lower())
        candidates = en_by_name.get(key) or []
        if not candidates:
            return en_by_id.get(num)
        # Prefer EN localId closest to JP number (handles SAR/SR/AR shifts)
        def score(item: tuple[str, str]) -> tuple[int, int]:
            lid = int(re.sub(r"\D", "", item[0]) or 0)
            return (abs(lid - n), lid)

        return sorted(candidates, key=score)[0][1]

    for card in catalog:
        images = card.setdefault("images", {"jp": card.get("image"), "kr": None, "en": None})
        images["jp"] = images.get("jp") or card.get("image")
        # Do not fake KR with JP art — leave null until a real KR source is attached
        if card.get("packId") != "sv2a-151":
            if not images.get("en"):
                images["en"] = images.get("jp")
            continue
        images["en"] = pick_en(card) or images.get("jp")
        card["image"] = images.get("jp") or card.get("image")


def main() -> int:
    print("Loading species name lists…")
    ko_names = load_species_names("ko")
    en_names = load_species_names("en")
    ja_names = load_species_names("ja")
    ja_index = build_ja_dex_index(ja_names)

    packs_out = []
    catalog = []

    for pack in PACKS:
        print(f"Fetching {pack['sourceFolder']}…")
        jp_cards = fetch_jp_cards(pack["sourceFolder"])
        built = [to_catalog_card(c, pack, ko_names, en_names, ja_index) for c in jp_cards]
        if pack["id"] == "thunderclap-spark":
            existing_ids = {c["id"] for c in built}
            for extra in SM7A_EXTRAS:
                if extra["id"] not in existing_ids:
                    built.append(extra)
        pack_row = {k: v for k, v in pack.items() if k not in {"sourceFolder", "idPrefix"}}
        pack_row["cardIds"] = [c["id"] for c in built]
        packs_out.append(pack_row)
        catalog.extend(built)
        print(f"  → {len(built)} cards")

    print("Attaching multilingual images…")
    attach_multilang_images(catalog)

    print("Applying BWR whitelist…")
    catalog = ensure_bwr_cards(catalog, packs_out)

    asof = datetime.now(KST).isoformat(timespec="seconds")
    live, stats = build_live_snapshot(catalog, packs_out, asof)
    write_data_bundle(DATA, packs_out, catalog, live)

    print(json.dumps({"packs": len(packs_out), "catalog": len(catalog), **stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
