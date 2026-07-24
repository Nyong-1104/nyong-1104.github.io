# -*- coding: utf-8 -*-
"""Add three promo packs: Yu Nagaba, s8a-P 25th, Victini BWR."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from brg_pop import restore_brg_pops  # noqa: E402
from ebay_prices import restore_ebay_prices  # noqa: E402
from pokepop_snapshot import build_live_snapshot, write_data_bundle  # noqa: E402

KST = timezone(timedelta(hours=9))

CURSOR_ASSETS = Path(
    r"C:\Users\User\.cursor\projects\c-Users-User-nyong-app-nyong-1104-github-io\assets"
)

PACK_IMAGE_SOURCES = {
    "pack-yu-nagaba.png": "c__Users_User_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images________-560a376f-6120-4ff9-aa26-588cbee34c48.png",
    "pack-s8a-p-25th.png": "c__Users_User_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_25_____-0ca8ceff-773e-40e0-95d4-f3905f9cdd5d.png",
    "pack-victini-bwr-promo.png": "c__Users_User_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images________________-05385e7e-1972-4a6d-ae5e-16d5c1f8b2ec.png",
}

NAGABA_IMG = {
    "062": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/043691_P_IBUI.jpg",
    "063": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/043692_P_SHIXYAWAZU.jpg",
    "064": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/043693_P_SANDASU.jpg",
    "065": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/043694_P_BUSUTA.jpg",
    "066": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/043695_P_EFUI.jpg",
    "067": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/043696_P_BURAKKI.jpg",
    "068": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/043697_P_RIFUIA.jpg",
    "069": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/043698_P_GUREISHIA.jpg",
    "070": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/043699_P_NINFUIA.jpg",
}

VICTINI_IMG = {
    "272": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/047709_T_ENERUGITENSOU.jpg",
    "273": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/047710_T_KIZUGUSURI.jpg",
    "274": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/047711_T_KURASSHIXYUHANMA.jpg",
    "275": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/047712_T_HAIPABORU.jpg",
    "276": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/047713_T_POKEMONIREKAE.jpg",
    "277": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/047714_T_POKEMONKIXYATCHIXYA.jpg",
    "278": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/047715_T_BOSUNOSHIREI.jpg",
    "279": "https://www.pokemon-card.com/assets/images/card_images/large/SV-P/047716_T_CHIEREN.jpg",
}


def s8a_img(n: int) -> str:
    return f"https://www.pokemon-card.com/ex/25th/assets/images/s8aP/card-{n}.png"


def card(
    *,
    cid: str,
    pack_id: str,
    name_ko: str,
    name_en: str,
    name_ja: str,
    number: str,
    typ: str,
    image: str,
    catalog_jp: int | None = None,
    lang_images: dict | None = None,
    seed_price: int = 40,
    seed_pop: int = 20,
) -> dict:
    images = lang_images or {"jp": image, "kr": None, "en": None}
    return {
        "id": cid,
        "packId": pack_id,
        "nameKo": name_ko,
        "nameEn": name_en,
        "nameJa": name_ja,
        "number": number,
        "rarity": "PROMO",
        "type": typ,
        "typeKo": "트레이너" if typ == "trainer" else None,
        "holoStyle": "holo",
        "image": image,
        "images": images,
        "catalogKeys": {"jp": catalog_jp, "kr": None, "en": None},
        "seed": {"basePrice": seed_price, "basePop": seed_pop},
    }


def build_nagaba() -> tuple[dict, list[dict]]:
    pack_id = "yu-nagaba-eevee-promo"
    rows = [
        ("062", "이브이", "Eevee", "イーブイ", "colorless", 43691),
        ("063", "샤미드", "Vaporeon", "シャワーズ", "water", 43692),
        ("064", "쥬피썬더", "Jolteon", "サンダース", "lightning", 43693),
        ("065", "부스터", "Flareon", "ブースター", "fire", 43694),
        ("066", "에브이", "Espeon", "エーフィ", "psychic", 43695),
        ("067", "블래키", "Umbreon", "ブラッキー", "darkness", 43696),
        ("068", "리피아", "Leafeon", "リーフィア", "grass", 43697),
        ("069", "글레이시아", "Glaceon", "グレイシア", "water", 43698),
        ("070", "님피아", "Sylveon", "ニンフィア", "psychic", 43699),
    ]
    cards = []
    for num, ko, en, ja, typ, oid in rows:
        img = NAGABA_IMG[num]
        cards.append(
            card(
                cid=f"nagaba-{num}",
                pack_id=pack_id,
                name_ko=ko,
                name_en=en,
                name_ja=ja,
                number=f"{num}/SV-P",
                typ=typ,
                image=img,
                catalog_jp=oid,
                seed_price=120,
                seed_pop=30,
            )
        )
    pack = {
        "id": pack_id,
        "nameKo": "YU NAGABA × 포켓몬카드게임 프로모카드팩",
        "nameEn": "YU NAGABA × Pokémon Card Game Promo Pack",
        "nameJa": "YU NAGABA × ポケモンカードゲーム プロモカードパック",
        "nameShort": "YU NAGABA",
        "code": "NAGABA-P",
        "releaseYear": 2023,
        "listGroup": "promo",
        "listComplete": True,
        "languages": ["jp"],
        "blurb": "나가바 유 콜라보 — 이브이 일족 전 9종 중 랜덤 1장.",
        "blurbEn": "Yu Nagaba collab — 1 of 9 Eevee-line promos.",
        "blurbJa": "長場雄コラボ — イーブイたち全9種からランダム1枚。",
        "packImage": "./assets/pack-yu-nagaba.png",
        "coverCardId": "nagaba-062",
        "brgSets": {
            "jp": {"setName": "POKEMON S&V JAPANESE PROMO", "year": 2023},
        },
        "cardIds": [c["id"] for c in cards],
    }
    return pack, cards


def build_s8a_p() -> tuple[dict, list[dict]]:
    pack_id = "s8a-p-25th-anniversary"
    rows = [
        (1, "리자몽", "Charizard", "リザードン", "fire"),
        (2, "이상해꽃", "Venusaur", "フシギバナ", "grass"),
        (3, "거북왕", "Blastoise", "カメックス", "water"),
        (4, "가짜 오박사", "Imposter Professor Oak", "にせオーキドはかせ", "trainer"),
        (5, "나쁜 갸라도스", "Dark Gyarados", "わるいギャラドス", "water"),
        (6, "로켓단 등장!", "Here Comes Team Rocket!", "ロケット団参上！", "trainer"),
        (7, "___의 피카츄", "___'s Pikachu", "＿のピカチュウ", "lightning"),
        (8, "R단의 썬더", "Rocket's Zapdos", "R団のサンダー", "lightning"),
        (9, "삐", "Cleffa", "ピィ", "psychic"),
        (10, "빛나는 잉어킹", "Shining Magikarp", "ひかるコイキング", "water"),
        (11, "마그마단의 그란돈", "Team Magma's Groudon", "マグマ団のグラードン", "fighting"),
        (12, "블래키☆", "Umbreon ☆", "ブラッキー☆", "darkness"),
        (13, "로켓단의 간부", "Rocket's Admin.", "ロケット団の幹部", "trainer"),
        (14, "뮤ex", "Mew ex", "ミュウex", "psychic"),
        (15, "가디안ex δ", "Gardevoir ex δ", "サーナイトex δ", "fire"),
        (16, "점토도리", "Claydol", "ネンドール", "fighting"),
        (17, "렌트라GL LV.X", "Luxray GL LV.X", "レントラーGL LV.X", "lightning"),
        (18, "한카리아스C LV.X", "Garchomp C LV.X", "ガブリアスC LV.X", "colorless"),
        (19, "코리갑", "Donphan", "ドンファン", "fighting"),
        (20, "레시라무", "Reshiram", "レシラム", "fire"),
        (21, "제크로무", "Zekrom", "ゼクロム", "lightning"),
        (22, "뮤츠EX", "Mewtwo EX", "ミュウツーEX", "psychic"),
        (23, "제르네아스EX", "Xerneas EX", "ゼルネアスEX", "fairy"),
        (24, "M레쿠쟈EX", "M Rayquaza EX", "MレックウザEX", "colorless"),
        (25, "카푸느지느GX", "Tapu Lele GX", "カプ・テテフGX", "psychic"),
    ]
    cards = []
    for n, ko, en, ja, typ in rows:
        num = f"{n:03d}"
        img = s8a_img(n)
        cards.append(
            card(
                cid=f"s8a-p-{num}",
                pack_id=pack_id,
                name_ko=ko,
                name_en=en,
                name_ja=ja,
                number=f"{num}/025",
                typ=typ,
                image=img,
                lang_images={"jp": img, "kr": img, "en": None},
                seed_price=80,
                seed_pop=25,
            )
        )
    pack = {
        "id": pack_id,
        "nameKo": "프로모 카드팩 25th ANNIVERSARY edition",
        "nameEn": "Promo Card Pack 25th ANNIVERSARY edition",
        "nameJa": "プロモカードパック 25th ANNIVERSARY edition",
        "nameShort": "s8a-P 25th",
        "code": "s8a-P",
        "releaseYear": 2021,
        "listGroup": "promo",
        "listComplete": True,
        "languages": ["kr", "jp"],
        "blurb": "25주년 기념 프로모 — 클래식 카드 전 25종 중 랜덤 1장.",
        "blurbEn": "25th Anniversary promos — 1 of 25 classic reprints.",
        "blurbJa": "25周年プロモ — 歴代カード全25種からランダム1枚。",
        "packImage": "./assets/pack-s8a-p-25th.png",
        "coverCardId": "s8a-p-001",
        "brgSets": {
            "jp": {"setName": "POKEMON SWSH JAPANESE S8AP", "year": 2021},
            "kr": {"setName": "POKEMON SWSH KOREAN S8AP", "year": 2021},
        },
        "cardIds": [c["id"] for c in cards],
    }
    return pack, cards


def build_victini() -> tuple[dict, list[dict]]:
    pack_id = "victini-bwr-promo"
    rows = [
        ("272", "에너지 전송", "Energy Transfer", "エネルギー転送", 47709),
        ("273", "상처약", "Potion", "きずぐすり", 47710),
        ("274", "크래시 해머", "Crushing Hammer", "クラッシュハンマー", 47711),
        ("275", "하이퍼볼", "Ultra Ball", "ハイパーボール", 47712),
        ("276", "포켓몬 교체", "Switch", "ポケモンいれかえ", 47713),
        ("277", "포켓몬 캐처", "Pokémon Catcher", "ポケモンキャッチャー", 47714),
        ("278", "보스의 지령", "Boss's Orders", "ボスの指令", 47715),
        ("279", "체렌", "Cheren", "チェレン", 47716),
    ]
    cards = []
    for num, ko, en, ja, oid in rows:
        img = VICTINI_IMG[num]
        cards.append(
            card(
                cid=f"victini-bwr-{num}",
                pack_id=pack_id,
                name_ko=ko,
                name_en=en,
                name_ja=ja,
                number=f"{num}/SV-P",
                typ="trainer",
                image=img,
                catalog_jp=oid,
                seed_price=35,
                seed_pop=40,
            )
        )
    pack = {
        "id": pack_id,
        "nameKo": "비크티니ex 쟁탈전 프로모카드팩",
        "nameEn": "Victini ex Battle Promo Card Pack",
        "nameJa": "ビクティニex 争奪戦 プロモカードパック",
        "nameShort": "Victini BWR",
        "code": "VICTINI-P",
        "releaseYear": 2025,
        "listGroup": "promo",
        "listComplete": True,
        "languages": ["jp"],
        "blurb": "비크티니 BWR 쟁탈전 — 트레이너 전 8종 중 랜덤 1장.",
        "blurbEn": "Victini BWR battle — 1 of 8 trainer promos.",
        "blurbJa": "ビクティニBWR争奪戦 — トレーナーズ全8種からランダム1枚。",
        "packImage": "./assets/pack-victini-bwr-promo.png",
        "coverCardId": "victini-bwr-279",
        "brgSets": {},
        "cardIds": [c["id"] for c in cards],
    }
    return pack, cards


def copy_pack_images() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for dest_name, src_name in PACK_IMAGE_SOURCES.items():
        src = CURSOR_ASSETS / src_name
        if not src.exists():
            raise FileNotFoundError(f"Missing pack image source: {src}")
        dest = ASSETS / dest_name
        shutil.copy2(src, dest)
        print(f"copied {dest_name} ({dest.stat().st_size} bytes)")


def upsert_psa(packs: list[dict]) -> None:
    path = DATA / "psa-sets.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for pack in packs:
        langs = pack.get("languages") or ["jp"]
        entry = {lang: None for lang in langs}
        entry["_meta"] = {
            "code": pack.get("code"),
            "year": pack.get("releaseYear"),
            "nameEn": pack.get("nameEn") or pack.get("nameShort"),
        }
        data[pack["id"]] = entry
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    copy_pack_images()

    built = [build_nagaba(), build_s8a_p(), build_victini()]
    new_packs = [p for p, _ in built]
    new_cards = [c for _, cards in built for c in cards]
    pack_ids = {p["id"] for p in new_packs}

    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))

    packs = [p for p in packs if p["id"] not in pack_ids]
    packs.extend(new_packs)
    catalog = [c for c in catalog if c.get("packId") not in pack_ids]
    catalog.extend(new_cards)

    upsert_psa(new_packs)

    asof_iso = datetime.now(KST).isoformat(timespec="seconds")
    live_path = DATA / "live" / "pop-price.json"
    previous = json.loads(live_path.read_text(encoding="utf-8")) if live_path.exists() else {}

    live, stats = build_live_snapshot(catalog, packs, asof_iso, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    live["source"] = previous.get("source") or "seed"
    live["generatedAt"] = asof_iso
    keep_ids = {c["id"] for c in catalog}
    live["cards"] = {k: v for k, v in (live.get("cards") or {}).items() if k in keep_ids}

    last_run = {
        "ranAt": asof_iso,
        "stats": {
            **stats,
            "promoPacks": {
                p["id"]: len(p["cardIds"]) for p in new_packs
            },
        },
    }
    (DATA / "live" / "last-run.json").write_text(
        json.dumps(last_run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_data_bundle(DATA, packs, catalog, live, last_run)

    summary = {
        "packs": [{ "id": p["id"], "cards": len(p["cardIds"]) } for p in new_packs],
        "totalCardsAdded": len(new_cards),
        "generatedAt": asof_iso,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
