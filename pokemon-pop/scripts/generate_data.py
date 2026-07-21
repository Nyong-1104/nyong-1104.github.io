# -*- coding: utf-8 -*-
"""Generate packs.json, cards.json, and data.js for PokePop MVP."""
import json
import hashlib
from pathlib import Path

ROOT = Path(r"C:\Users\User\nyong-app\nyong-1104.github.io\pokemon-pop")
ASOF = "2026-07-21"


def seed_int(key: str) -> int:
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


def variant(key: str, base_price: int, base_pop10: int, lang: str):
    s = seed_int(f"{key}-{lang}")
    mult = 0.42 if lang == "kr" else 1.0
    price = max(8, int(base_price * mult * (0.85 + (s % 30) / 100)))
    p10 = max(3, int(base_pop10 * mult * (0.7 + (s % 40) / 100)))
    p9 = int(p10 * (0.6 + (s % 20) / 100))
    p8 = int(p10 * (0.15 + (s % 15) / 100))
    total = p10 + p9 + p8 + (s % 40)
    bgs10 = max(0, p10 // 18)
    cgc10 = max(0, p10 // 12)
    return {
        "price": {
            "source": "PSA",
            "grade": "10",
            "amount": price,
            "currency": "USD",
            "asOf": ASOF,
        },
        "pop": {
            "PSA": {"10": p10, "9": p9, "8": p8, "total": total},
            "BGS": {
                "10": bgs10,
                "9.5": bgs10 * 3 + 2,
                "9": bgs10 * 2,
                "total": bgs10 * 6 + 8,
            }
            if bgs10 or lang == "jp"
            else None,
            "CGC": {
                "10": cgc10,
                "9.5": cgc10 + 4,
                "9": max(1, cgc10 // 2),
                "total": cgc10 * 3 + 10,
            },
            "BRG": None,
            "TAG": {"10": max(0, p10 // 80), "9": max(0, p10 // 50), "total": max(0, p10 // 30)}
            if lang == "jp"
            else None,
            "ACE": None,
            "AGS": {"10": max(0, p10 // 120), "9": max(0, p10 // 80), "total": max(0, p10 // 50)}
            if lang == "jp" and p10 > 100
            else None,
        },
        "updatedAt": ASOF,
    }


def card(id_, pack_id, name_ko, name_en, number, rarity, type_, type_ko, holo, image, base_price, base_pop):
    return {
        "id": id_,
        "packId": pack_id,
        "nameKo": name_ko,
        "nameEn": name_en,
        "number": number,
        "rarity": rarity,
        "type": type_,
        "typeKo": type_ko,
        "holoStyle": holo,
        "image": image,
        "variants": {
            "jp": variant(id_, base_price, base_pop, "jp"),
            "kr": variant(id_, base_price, base_pop, "kr"),
        },
    }


packs = [
    {
        "id": "sv2a-151",
        "nameKo": "Pokémon TCG: Scarlet & Violet—151",
        "nameEn": "Pokémon TCG: Scarlet & Violet—151",
        "nameShort": "151",
        "code": "sv2a",
        "releaseYear": 2023,
        "languages": ["kr", "jp"],
        "blurb": "원조 151마리를 모은 강화 확장팩. 리자몽·뮤 SAR가 대표 카드입니다.",
        "packImage": "./assets/pack-151.png",
        "coverCardId": "sv2a-charizard-sar",
        "cardIds": [],
    },
    {
        "id": "pokekyun",
        "nameKo": "PokéKyun Collection",
        "nameEn": "PokéKyun Collection",
        "code": "CP1",
        "releaseYear": 2016,
        "languages": ["kr", "jp"],
        "blurb": "2016년 발매된 귀여움 특화 세트. 피카츄·데덴네가 대표 카드입니다.",
        "packImage": "./assets/pack-pokekyun.png",
        "coverCardId": "kyun-pikachu",
        "cardIds": [],
    },
    {
        "id": "thunderclap-spark",
        "nameKo": "플라즈마 스파크",
        "nameEn": "Thunderclap Spark",
        "code": "sm7a",
        "releaseYear": 2018,
        "languages": ["kr", "jp"],
        "blurb": "썬&문 강화 확장팩. 제라오라 GX·게노세크트 GX가 대표 카드입니다.",
        "packImage": "./assets/pack-ThunderclapSpark.png",
        "coverCardId": "sm7a-zeraora-gx-sr",
        "cardIds": [],
    },
]

cards = [
    # --- 151 (10) ---
    card("sv2a-charizard-sar", "sv2a-151", "리자몽 ex", "Charizard ex", "201/165", "SAR", "fire", "불", "sar",
         "https://images.pokemontcg.io/sv3pt5/199_hires.png", 850, 1240),
    card("sv2a-venusaur-sar", "sv2a-151", "이상해꽃 ex", "Venusaur ex", "200/165", "SAR", "grass", "풀", "sar",
         "https://images.pokemontcg.io/sv3pt5/198_hires.png", 220, 980),
    card("sv2a-blastoise-sar", "sv2a-151", "거북왕 ex", "Blastoise ex", "202/165", "SAR", "water", "물", "sar",
         "https://images.pokemontcg.io/sv3pt5/200_hires.png", 240, 910),
    card("sv2a-alakazam-sar", "sv2a-151", "후딘 ex", "Alakazam ex", "203/165", "SAR", "psychic", "초", "sar",
         "https://images.pokemontcg.io/sv3pt5/201_hires.png", 160, 720),
    card("sv2a-zapdos-sar", "sv2a-151", "썬더 ex", "Zapdos ex", "204/165", "SAR", "lightning", "번개", "sar",
         "https://images.pokemontcg.io/sv3pt5/202_hires.png", 190, 800),
    card("sv2a-mew-sar", "sv2a-151", "뮤 ex", "Mew ex", "205/165", "SAR", "psychic", "초", "sar",
         "https://images.pokemontcg.io/sv3pt5/151_hires.png", 280, 980),
    card("sv2a-erika-sar", "sv2a-151", "이상해씨의 초대", "Erika's Invitation", "206/165", "SAR", "trainer", "트레이너", "sar",
         "https://images.pokemontcg.io/sv3pt5/203_hires.png", 95, 1100),
    card("sv2a-giovanni-sar", "sv2a-151", "비주의 카리스마", "Giovanni's Charisma", "207/165", "SAR", "trainer", "트레이너", "sar",
         "https://images.pokemontcg.io/sv3pt5/204_hires.png", 110, 1050),
    card("sv2a-charizard-sr", "sv2a-151", "리자몽 ex", "Charizard ex", "185/165", "SR", "fire", "불", "holo",
         "https://images.pokemontcg.io/sv3pt5/183_hires.png", 95, 2100),
    card("sv2a-bulbasaur-ar", "sv2a-151", "이상해씨", "Bulbasaur", "166/165", "AR", "grass", "풀", "reverse",
         "https://images.pokemontcg.io/sv3pt5/166_hires.png", 35, 3200),
    # --- PokéKyun (10) ---
    card("kyun-pikachu", "pokekyun", "피카츄", "Pikachu", "010/032", "RR", "lightning", "번개", "holo",
         "https://images.pokemontcg.io/g1/RC29_hires.png", 190, 145),
    card("kyun-dedenne", "pokekyun", "데덴네", "Dedenne", "012/032", "U", "lightning", "번개", "reverse",
         "https://images.pokemontcg.io/g1/RC10_hires.png", 120, 98),
    card("kyun-jirachi", "pokekyun", "지라치", "Jirachi", "015/032", "R", "psychic", "초", "holo",
         "https://images.pokemontcg.io/xy10/42_hires.png", 85, 160),
    card("kyun-sylveon-ex", "pokekyun", "님피아 EX", "Sylveon EX", "025/032", "RR", "fairy", "페어리", "holo",
         "https://images.pokemontcg.io/xy7/92_hires.png", 140, 120),
    card("kyun-charizard", "pokekyun", "리자몽", "Charizard", "005/032", "R", "fire", "불", "holo",
         "https://images.pokemontcg.io/xy12/11_hires.png", 110, 200),
    card("kyun-flareon-ex", "pokekyun", "부스터 EX", "Flareon EX", "006/032", "RR", "fire", "불", "holo",
         "https://images.pokemontcg.io/xy8/20_hires.png", 95, 130),
    card("kyun-gardevoir-ex", "pokekyun", "가디안 EX", "Gardevoir EX", "019/032", "RR", "fairy", "페어리", "holo",
         "https://images.pokemontcg.io/xy7/78_hires.png", 100, 150),
    card("kyun-diancie", "pokekyun", "디안시", "Diancie", "027/032", "R", "fairy", "페어리", "holo",
         "https://images.pokemontcg.io/xy6/71_hires.png", 55, 180),
    card("kyun-espurr", "pokekyun", "냐스퍼", "Espurr", "016/032", "C", "psychic", "초", "reverse",
         "https://images.pokemontcg.io/xy4/42_hires.png", 40, 90),
    card("kyun-raichu", "pokekyun", "라이츄", "Raichu", "011/032", "R", "lightning", "번개", "holo",
         "https://images.pokemontcg.io/g1/RC9_hires.png", 70, 110),
    # --- Thunderclap Spark / 플라즈마 스파크 (10) ---
    card("sm7a-zeraora-gx-sr", "thunderclap-spark", "제라오라 GX", "Zeraora-GX", "063/060", "SR", "lightning", "번개", "holo",
         "https://images.pokemontcg.io/sm8/201_hires.png", 180, 420),
    card("sm7a-zeraora-gx-hr", "thunderclap-spark", "제라오라 GX", "Zeraora-GX", "069/060", "HR", "lightning", "번개", "sar",
         "https://images.pokemontcg.io/sm8/201_hires.png", 320, 180),
    card("sm7a-virizion-gx-sr", "thunderclap-spark", "비리디온 GX", "Virizion-GX", "061/060", "SR", "grass", "풀", "holo",
         "https://images.pokemontcg.io/sm8/196_hires.png", 95, 350),
    card("sm7a-genesect-gx-sr", "thunderclap-spark", "게노세크트 GX", "Genesect-GX", "064/060", "SR", "metal", "강철", "holo",
         "https://images.pokemontcg.io/sm8/60_hires.png", 110, 300),
    card("sm7a-magcargo-gx-sr", "thunderclap-spark", "마그카르고 GX", "Magcargo-GX", "062/060", "SR", "fire", "불", "holo",
         "https://images.pokemontcg.io/sm8/202_hires.png", 80, 280),
    card("sm7a-kahili-sr", "thunderclap-spark", "카힐리", "Kahili", "065/060", "SR", "trainer", "트레이너", "holo",
         "https://images.pokemontcg.io/sm8/190_hires.png", 250, 95),
    card("sm7a-judge-sr", "thunderclap-spark", "저지맨", "Judge", "066/060", "SR", "trainer", "트레이너", "holo",
         "https://images.pokemontcg.io/sm8/191_hires.png", 210, 110),
    card("sm7a-tapu-koko", "thunderclap-spark", "카푸코코", "Tapu Koko", "032/060", "R", "lightning", "번개", "holo",
         "https://images.pokemontcg.io/sm2/47_hires.png", 25, 600),
    card("sm7a-ditto-prism", "thunderclap-spark", "메타몽◇", "Ditto ◇", "043/060", "PRISM", "colorless", "무색", "holo",
         "https://images.pokemontcg.io/sm8/154_hires.png", 45, 400),
    card("sm7a-electropower-ur", "thunderclap-spark", "일렉파워", "Electropower", "071/060", "UR", "trainer", "트레이너", "holo",
         "https://images.pokemontcg.io/sm8/172_hires.png", 90, 220),
]

for p in packs:
    p["cardIds"] = [c["id"] for c in cards if c["packId"] == p["id"]]

(ROOT / "data" / "packs.json").write_text(
    json.dumps(packs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(ROOT / "data" / "cards.json").write_text(
    json.dumps(cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
data_js = (
    "window.POP_PACKS = "
    + json.dumps(packs, ensure_ascii=False, indent=2)
    + ";\nwindow.POP_CARDS = "
    + json.dumps(cards, ensure_ascii=False, indent=2)
    + ";\n"
)
(ROOT / "data" / "data.js").write_text(data_js, encoding="utf-8")
print(f"packs={len(packs)} cards={len(cards)}")
for p in packs:
    print(p["id"], len(p["cardIds"]))
