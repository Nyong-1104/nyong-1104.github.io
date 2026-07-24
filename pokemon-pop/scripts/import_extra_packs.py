# -*- coding: utf-8 -*-
"""Copy pack art from Downloads, punch black backgrounds, rebuild catalog."""
from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
PACK_SRC = Path(r"C:\Users\admin\Downloads\pack-img")

sys.path.insert(0, str(SCRIPTS))
from build_catalog import (  # noqa: E402
    PACKS as CORE_PACKS,
    attach_multilang_images,
    build_ja_dex_index,
    fetch_jp_cards,
    load_species_names,
    to_catalog_card,
)
from pokepop_snapshot import (  # noqa: E402
    build_live_snapshot,
    load_previous_live,
    write_data_bundle,
)
from ebay_prices import restore_ebay_prices  # noqa: E402
from brg_pop import restore_brg_pops  # noqa: E402
from gemrate_pop import restore_psa_pops  # noqa: E402
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "PokePopCatalogBuilder/1.0"}

# Extra packs from Downloads/pack-img (filename stem -> metadata)
EXTRA_PACKS = [
    {
        "file": "25th 애니버서리 컬렉션.png",
        "id": "s8a-25th",
        "nameKo": "25th 애니버서리 컬렉션",
        "nameEn": "25th Anniversary Collection",
        "nameJa": "25th アニバーサリーコレクション",
        "code": "S8a",
        "releaseYear": 2021,
        "languages": ["jp", "kr"],
        "blurb": "25주년 기념 컬렉션. 특별 일러스트와 클래식 카드가 모인 하이라이트 세트입니다.",
        "blurbEn": "A 25th anniversary highlight set packed with special art and classic favorites.",
        "blurbJa": "25周年記念コレクション。特別イラストとクラシックカードが揃うハイライトセットです。",
        "sourceFolder": "S8a",
        "idPrefix": "s8a",
        "krJson": "S/S8a.json",
    },
    {
        "file": "고대의포효.png",
        "id": "sv4k-ancient-roar",
        "nameKo": "고대의 포효",
        "nameEn": "Ancient Roar",
        "nameJa": "古代の咆哮",
        "code": "SV4K",
        "releaseYear": 2023,
        "languages": ["jp", "kr", "en"],
        "blurb": "고대 포켓몬이 중심인 확장팩. 강력한 ex와 SAR가 포인트를 만듭니다.",
        "blurbEn": "An expansion centered on ancient Pokémon, with standout ex and SAR cards.",
        "blurbJa": "古代ポケモンが中心の拡張パック。強力なexとSARがポイントです。",
        "sourceFolder": "SV4K",
        "idPrefix": "sv4k",
        "krJson": "SV/SV4K.json",
    },
    {
        "file": "나이트원더러.png",
        "id": "sv6a-night-wanderer",
        "nameKo": "나이트 원더러",
        "nameEn": "Night Wanderer",
        "nameJa": "ナイトワンダラー",
        "code": "SV6a",
        "releaseYear": 2024,
        "languages": ["jp", "kr"],
        "blurb": "밤의 분위기가 강한 강화 확장팩. 테라스탈 카드가 중심입니다.",
        "blurbEn": "A night-themed enhanced set built around Terastal cards.",
        "blurbJa": "夜の雰囲気が強い強化拡張パック。テラスタルカードが中心です。",
        "sourceFolder": "SV6a",
        "idPrefix": "sv6a",
        "krJson": "SV/SV6a.json",
    },
    {
        "file": "낙원드래고나.png",
        "id": "sv7a-paradise-dragona",
        "nameKo": "낙원 드래고나",
        "nameEn": "Paradise Dragona",
        "nameJa": "楽園ドラゴーナ",
        "code": "SV7a",
        "releaseYear": 2024,
        "languages": ["jp", "kr"],
        "blurb": "드래곤 테마의 강화 확장팩. 화려한 드래곤 SAR가 대표작입니다.",
        "blurbEn": "A dragon-themed enhanced expansion with flashy Dragon SARs.",
        "blurbJa": "ドラゴンテーマの強化拡張パック。華やかなドラゴンSARが代表です。",
        "sourceFolder": "SV7a",
        "idPrefix": "sv7a",
        "krJson": None,
    },
    {
        "file": "니힐제로.png",
        "id": "m3-nihil-zero",
        "nameKo": "니힐제로",
        "nameEn": "Nihil Zero",
        "nameJa": "ムニキスゼロ",
        "code": "M3",
        "releaseYear": 2025,
        "languages": ["jp", "kr"],
        "blurb": "MEGA 시리즈 확장팩. 새로운 메가 진화 카드가 핵심입니다.",
        "blurbEn": "A MEGA series expansion focused on new Mega Evolution cards.",
        "blurbJa": "MEGAシリーズ拡張パック。新しいメガ進化カードが核心です。",
        "sourceFolder": "M3",
        "idPrefix": "m3",
        "krJson": None,
    },
    {
        "file": "닌자스피너.png",
        "id": "m4-ninja-spinner",
        "nameKo": "닌자 스피너",
        "nameEn": "Ninja Spinner",
        "nameJa": "ニンジャスピナー",
        "code": "M4",
        "releaseYear": 2025,
        "languages": ["jp", "kr"],
        "blurb": "닌자·스피드 감성의 MEGA 확장팩입니다.",
        "blurbEn": "A MEGA expansion with ninja-speed vibes.",
        "blurbJa": "ニンジャ＆スピード感のMEGA拡張パックです。",
        "sourceFolder": "M4",
        "idPrefix": "m4",
        "krJson": None,
    },
    {
        "file": "레이징서프.png",
        "id": "sv3a-raging-surf",
        "nameKo": "레이징 서프",
        "nameEn": "Raging Surf",
        "nameJa": "レイジングサーフ",
        "code": "SV3a",
        "releaseYear": 2023,
        "languages": ["jp", "kr"],
        "blurb": "서핑·파도 테마의 강화 확장팩입니다.",
        "blurbEn": "An enhanced expansion with surfing and wave themes.",
        "blurbJa": "サーフィン＆波テーマの強化拡張パックです。",
        "sourceFolder": "SV3a",
        "idPrefix": "sv3a",
        "krJson": "SV/SV3a.json",
    },
    {
        "file": "로켓단의영광.png",
        "id": "sv10-rocket-glory",
        "nameKo": "로켓단의 영광",
        "nameEn": "Glory of Team Rocket",
        "nameJa": "ロケット団の栄光",
        "code": "SV10",
        "releaseYear": 2025,
        "languages": ["jp", "kr"],
        "blurb": "로켓단이 주인공인 확장팩. 악당 감성 카드가 가득합니다.",
        "blurbEn": "A Team Rocket–centered expansion packed with villain flair.",
        "blurbJa": "ロケット団が主人公の拡張パック。悪役感あふれるカードが揃います。",
        "sourceFolder": "SV10",
        "idPrefix": "sv10",
        "krJson": None,
    },
    {
        "file": "메가브레이브.png",
        "id": "m1l-mega-brave",
        "nameKo": "메가 브레이브",
        "nameEn": "Mega Brave",
        "nameJa": "メガブレイブ",
        "code": "M1L",
        "releaseYear": 2025,
        "languages": ["jp", "kr", "en"],
        "blurb": "MEGA 시리즈의 브레이브 라인 확장팩입니다.",
        "blurbEn": "The Brave-line expansion of the MEGA series.",
        "blurbJa": "MEGAシリーズのブレイブライン拡張パックです。",
        "sourceFolder": "M1L",
        "idPrefix": "m1l",
        "krJson": None,
    },
    {
        "file": "메가심포니아.png",
        "id": "m1s-mega-symphonia",
        "nameKo": "메가 심포니아",
        "nameEn": "Mega Symphonia",
        "nameJa": "メガシンフォニア",
        "code": "M1S",
        "releaseYear": 2025,
        "languages": ["jp", "kr"],
        "blurb": "MEGA 시리즈의 심포니 라인 확장팩입니다.",
        "blurbEn": "The Symphonia-line expansion of the MEGA series.",
        "blurbJa": "MEGAシリーズのシンフォニアライン拡張パックです。",
        "sourceFolder": "M1S",
        "idPrefix": "m1s",
        "krJson": None,
    },
    {
        "file": "미래의일섬.png",
        "id": "sv4m-future-flash",
        "nameKo": "미래의 일섬",
        "nameEn": "Future Flash",
        "nameJa": "未来の一閃",
        "code": "SV4M",
        "releaseYear": 2023,
        "languages": ["jp", "kr", "en"],
        "blurb": "미래 포켓몬이 중심인 확장팩입니다.",
        "blurbEn": "An expansion centered on Future Pokémon.",
        "blurbJa": "未来ポケモンが中心の拡張パックです。",
        "sourceFolder": "SV4M",
        "idPrefix": "sv4m",
        "krJson": "SV/SV4M.json",
    },
    {
        "file": "배틀파트너즈.png",
        "id": "sv9-battle-partners",
        "nameKo": "배틀 파트너즈",
        "nameEn": "Battle Partners",
        "nameJa": "バトルパートナーズ",
        "code": "SV9",
        "releaseYear": 2025,
        "languages": ["jp", "kr"],
        "blurb": "파트너와 함께하는 배틀 테마 확장팩입니다.",
        "blurbEn": "A battle-themed expansion focused on partner play.",
        "blurbJa": "パートナーと戦うバトルテーマ拡張パックです。",
        "sourceFolder": "SV9",
        "idPrefix": "sv9",
        "krJson": None,
    },
    {
        "file": "변환의가면.png",
        "id": "sv6-mask-of-change",
        "nameKo": "변환의 가면",
        "nameEn": "Mask of Change",
        "nameJa": "変幻の仮面",
        "code": "SV6",
        "releaseYear": 2024,
        "languages": ["jp", "kr"],
        "blurb": "가면·변신 모티브가 돋보이는 확장팩입니다.",
        "blurbEn": "An expansion starring mask and transformation motifs.",
        "blurbJa": "仮面・変身モチーフが映える拡張パックです。",
        "sourceFolder": "SV6",
        "idPrefix": "sv6",
        "krJson": "SV/SV6.json",
    },
    {
        "file": "사이버저지.png",
        "id": "sv5m-cyber-judge",
        "nameKo": "사이버 저지",
        "nameEn": "Cyber Judge",
        "nameJa": "サイバージャッジ",
        "code": "SV5M",
        "releaseYear": 2024,
        "languages": ["jp", "kr"],
        "blurb": "미래·사이버 감성의 확장팩입니다.",
        "blurbEn": "A futuristic cyber-flavored expansion.",
        "blurbJa": "未来・サイバー感の拡張パックです。",
        "sourceFolder": "SV5M",
        "idPrefix": "sv5m",
        "krJson": "SV/SV5M.json",
    },
    {
        "file": "샤이니스타v.png",
        "id": "s4a-shiny-star-v",
        "nameKo": "샤이니 스타 V",
        "nameEn": "Shiny Star V",
        "nameJa": "シャイニースターV",
        "code": "S4a",
        "releaseYear": 2020,
        "languages": ["jp", "kr"],
        "blurb": "색이 다른 포켓몬이 대거 수록된 하이클래스 팩입니다.",
        "blurbEn": "A high-class set packed with Shiny Pokémon.",
        "blurbJa": "色違いポケモンが多数収録されたハイクラスパックです。",
        "sourceFolder": "S4a",
        "idPrefix": "s4a",
        "krJson": "S/S4a.json",
    },
    {
        "file": "샤이니트레저ex.png",
        "id": "sv4a-shiny-treasure",
        "nameKo": "샤이니 트레저 ex",
        "nameEn": "Shiny Treasure ex",
        "nameJa": "シャイニートレジャーex",
        "code": "SV4a",
        "releaseYear": 2023,
        "languages": ["jp", "kr"],
        "blurb": "색이 다른 포켓몬과 특별 art가 풍부한 하이클래스 팩입니다.",
        "blurbEn": "A high-class set rich in Shinies and special art.",
        "blurbJa": "色違いと特別アートが豊富なハイクラスパックです。",
        "sourceFolder": "SV4a",
        "idPrefix": "sv4a",
        "krJson": "SV/SV4a.json",
    },
    {
        "file": "스노해저드.png",
        "id": "sv2p-snow-hazard",
        "nameKo": "스노 해저드",
        "nameEn": "Snow Hazard",
        "nameJa": "スノーハザード",
        "code": "SV2P",
        "releaseYear": 2023,
        "languages": ["jp", "kr"],
        "blurb": "얼음·설원 테마의 확장팩입니다.",
        "blurbEn": "An ice-and-snow themed expansion.",
        "blurbJa": "氷・雪原テーマの拡張パックです。",
        "sourceFolder": "SV2P",
        "idPrefix": "sv2p",
        "krJson": "SV/SV2P.json",
    },
    {
        "file": "스칼렛&바이올렛 블랙볼트.png",
        "id": "sv11b-black-bolt",
        "nameKo": "블랙 볼트",
        "nameEn": "Black Bolt",
        "nameJa": "ブラックボルト",
        "code": "SV11B",
        "releaseYear": 2025,
        "languages": ["jp", "kr", "en"],
        "blurb": "스칼렛&바이올렛 후반의 블랙 볼트 세트입니다.",
        "blurbEn": "The Black Bolt set from late Scarlet & Violet.",
        "blurbJa": "スカーレット&バイオレット後半のブラックボルトです。",
        "sourceFolder": "SV11B",
        "idPrefix": "sv11b",
        "krJson": None,
    },
    {
        "file": "스칼렛&바이올렛 화이트플레어.png",
        "id": "sv11w-white-flare",
        "nameKo": "화이트 플레어",
        "nameEn": "White Flare",
        "nameJa": "ホワイトフレア",
        "code": "SV11W",
        "releaseYear": 2025,
        "languages": ["jp", "kr", "en"],
        "blurb": "스칼렛&바이올렛 후반의 화이트 플레어 세트입니다.",
        "blurbEn": "The White Flare set from late Scarlet & Violet.",
        "blurbJa": "スカーレット&バイオレット後半のホワイトフレアです。",
        "sourceFolder": "SV11W",
        "idPrefix": "sv11w",
        "krJson": None,
    },
    {
        "file": "스텔라미라클.png",
        "id": "sv7-stellar-miracle",
        "nameKo": "스텔라 미라클",
        "nameEn": "Stellar Miracle",
        "nameJa": "ステラミラクル",
        "code": "SV7",
        "releaseYear": 2024,
        "languages": ["jp", "kr"],
        "blurb": "스텔라 테라스탈이 등장하는 확장팩입니다.",
        "blurbEn": "An expansion introducing Stellar Terastal cards.",
        "blurbJa": "ステラテラスタルが登場する拡張パックです。",
        "sourceFolder": "SV7",
        "idPrefix": "sv7",
        "krJson": "SV/SV7.json",
    },
    {
        "file": "양천의볼트태클.png",
        "id": "s4-amazing-volt-tackle",
        "nameKo": "앙천의 볼트태클",
        "nameEn": "Amazing Volt Tackle",
        "nameJa": "仰天のボルテッカー",
        "code": "S4",
        "releaseYear": 2020,
        "languages": ["jp", "kr"],
        "blurb": "소드&실드 시기의 볼트태클 확장팩입니다.",
        "blurbEn": "A Sword & Shield era Volt Tackle expansion.",
        "blurbJa": "ソード&シールド期のボルテッカー拡張パックです。",
        "sourceFolder": "S4",
        "idPrefix": "s4",
        "krJson": "S/S4.json",
    },
    {
        "file": "어비스아이.png",
        "id": "m5-abyss-eye",
        "nameKo": "어비스 아이",
        "nameEn": "Abyss Eye",
        "nameJa": "アビスアイ",
        "code": "M5",
        "releaseYear": 2025,
        "languages": ["jp", "kr"],
        "blurb": "심연 테마의 MEGA 확장팩입니다.",
        "blurbEn": "An abyss-themed MEGA expansion.",
        "blurbJa": "深淵テーマのMEGA拡張パックです。",
        "sourceFolder": "M5",
        "idPrefix": "m5",
        "krJson": None,
    },
    {
        "file": "열풍의아레나.png",
        "id": "sv9a-heat-wave-arena",
        "nameKo": "열풍의 아레나",
        "nameEn": "Heat Wave Arena",
        "nameJa": "熱風のアリーナ",
        "code": "SV9a",
        "releaseYear": 2025,
        "languages": ["jp", "kr"],
        "blurb": "열풍과 아레나가 테마인 강화 확장팩입니다.",
        "blurbEn": "An enhanced set themed around heat waves and arenas.",
        "blurbJa": "熱風とアリーナがテーマの強化拡張パックです。",
        "sourceFolder": "SV9a",
        "idPrefix": "sv9a",
        "krJson": None,
    },
    {
        "file": "와일드포스.png",
        "id": "sv5k-wild-force",
        "nameKo": "와일드 포스",
        "nameEn": "Wild Force",
        "nameJa": "ワイルドフォース",
        "code": "SV5K",
        "releaseYear": 2024,
        "languages": ["jp", "kr"],
        "blurb": "고대·야생의 힘이 테마인 확장팩입니다.",
        "blurbEn": "An expansion themed around ancient wild force.",
        "blurbJa": "古代・野生の力がテーマの拡張パックです。",
        "sourceFolder": "SV5K",
        "idPrefix": "sv5k",
        "krJson": "SV/SV5K.json",
    },
    {
        "file": "이브이 히어로즈.png",
        "id": "s6a-eevee-heroes",
        "nameKo": "이브이 히어로즈",
        "nameEn": "Eevee Heroes",
        "nameJa": "イーブイヒーローズ",
        "code": "S6a",
        "releaseYear": 2021,
        "languages": ["jp", "kr"],
        "blurb": "이브이 진화들이 주인공인 인기 강화 확장팩입니다.",
        "blurbEn": "A beloved enhanced set starring Eevee evolutions.",
        "blurbJa": "イーブイ進化が主役の人気強化拡張パックです。",
        "sourceFolder": "S6a",
        "idPrefix": "s6a",
        "krJson": "S/S6a.json",
    },
    {
        "file": "인페르노X.png",
        "id": "m2-inferno-x",
        "nameKo": "인페르노 X",
        "nameEn": "Inferno X",
        "nameJa": "インフェルノX",
        "code": "M2",
        "releaseYear": 2025,
        "languages": ["jp", "kr"],
        "blurb": "화염 테마의 MEGA 확장팩입니다.",
        "blurbEn": "A fire-themed MEGA expansion.",
        "blurbJa": "炎テーマのMEGA拡張パックです。",
        "sourceFolder": "M2",
        "idPrefix": "m2",
        "krJson": None,
    },
    {
        "file": "창공스트림.png",
        "id": "s7r-blue-sky-stream",
        "nameKo": "창공 스트림",
        "nameEn": "Blue Sky Stream",
        "nameJa": "蒼空ストリーム",
        "code": "S7R",
        "releaseYear": 2021,
        "languages": ["jp", "kr"],
        "blurb": "하늘·비행 감성의 소드&실드 확장팩입니다.",
        "blurbEn": "A Sword & Shield expansion with sky-flight vibes.",
        "blurbJa": "空・飛行感のソード&シールド拡張パックです。",
        "sourceFolder": "S7R",
        "idPrefix": "s7r",
        "krJson": "S/S7R.json",
    },
    {
        "file": "초전브레이커.png",
        "id": "sv8-super-electric-breaker",
        "nameKo": "초전 브레이커",
        "nameEn": "Super Electric Breaker",
        "nameJa": "超電ブレイカー",
        "code": "SV8",
        "releaseYear": 2024,
        "languages": ["jp", "kr"],
        "blurb": "전기 에너지가 폭발하는 확장팩입니다.",
        "blurbEn": "An expansion bursting with electric energy.",
        "blurbJa": "電気エネルギーが爆発する拡張パックです。",
        "sourceFolder": "SV8",
        "idPrefix": "sv8",
        "krJson": None,
    },
    {
        "file": "크림슨헤이즈.png",
        "id": "sv5a-crimson-haze",
        "nameKo": "크림슨 헤이즈",
        "nameEn": "Crimson Haze",
        "nameJa": "クリムゾンヘイズ",
        "code": "SV5a",
        "releaseYear": 2024,
        "languages": ["jp", "kr"],
        "blurb": "진홍빛 헤이즈가 테마인 강화 확장팩입니다.",
        "blurbEn": "An enhanced set themed around crimson haze.",
        "blurbJa": "真紅のヘイズがテーマの強化拡張パックです。",
        "sourceFolder": "SV5a",
        "idPrefix": "sv5a",
        "krJson": "SV/SV5a.json",
    },
    {
        "file": "클레이버스트.png",
        "id": "sv2d-clay-burst",
        "nameKo": "클레이 버스트",
        "nameEn": "Clay Burst",
        "nameJa": "クレイバースト",
        "code": "SV2D",
        "releaseYear": 2023,
        "languages": ["jp", "kr"],
        "blurb": "땅·점토 감성의 확장팩입니다.",
        "blurbEn": "An earthy clay-burst themed expansion.",
        "blurbJa": "地面・クレイ感の拡張パックです。",
        "sourceFolder": "SV2D",
        "idPrefix": "sv2d",
        "krJson": "SV/SV2D.json",
    },
    {
        "file": "테라스탈페스타ex.png",
        "id": "sv8a-terastal-festa",
        "nameKo": "테라스탈 페스타 ex",
        "nameEn": "Terastal Fest ex",
        "nameJa": "テラスタルフェスex",
        "code": "SV8a",
        "releaseYear": 2024,
        "languages": ["jp", "kr"],
        "blurb": "테라스탈 축제를 테마로 한 하이클래스 팩입니다.",
        "blurbEn": "A high-class set themed as a Terastal festival.",
        "blurbJa": "テラスタルの祭りがテーマのハイクラスパックです。",
        "sourceFolder": "SV8a",
        "idPrefix": "sv8a",
        "krJson": None,
    },
    {
        "file": "하이클래스팩mega드림ex.png",
        "id": "m2a-mega-dream-ex",
        "nameKo": "MEGA 드림 ex",
        "nameEn": "MEGA Dream ex",
        "nameJa": "MEGAドリームex",
        "code": "M2a",
        "releaseYear": 2025,
        "languages": ["jp", "kr"],
        "blurb": "MEGA 시리즈 하이클래스 팩입니다.",
        "blurbEn": "A MEGA series high-class pack.",
        "blurbJa": "MEGAシリーズのハイクラスパックです。",
        "sourceFolder": "M2a",
        "idPrefix": "m2a",
        "krJson": None,
    },
    {
        "file": "흑염의지배자.png",
        "id": "sv3-ruler-of-black-flame",
        "nameKo": "흑염의 지배자",
        "nameEn": "Ruler of the Black Flame",
        "nameJa": "黒炎の支配者",
        "code": "SV3",
        "releaseYear": 2023,
        "languages": ["jp", "kr"],
        "blurb": "리자몽이 상징하는 흑염 테마 확장팩입니다.",
        "blurbEn": "A black-flame expansion symbolized by Charizard.",
        "blurbJa": "リザードンが象徴する黒炎テーマ拡張パックです。",
        "sourceFolder": "SV3",
        "idPrefix": "sv3",
        "krJson": "SV/SV3.json",
    },
]


def punch_black(path: Path, threshold: int = 28) -> None:
    """Make near-black pixels transparent and crop to content (vectorized)."""
    im = Image.open(path).convert("RGBA")
    # Downscale huge sources first for speed, then keep cropped result
    max_side = max(im.size)
    if max_side > 1600:
        scale = 1600 / max_side
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.Resampling.LANCZOS)

    px = im.load()
    w, h = im.size
    # Only walk every pixel once — still OK for <=1600
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r <= threshold and g <= threshold and b <= threshold:
                px[x, y] = (0, 0, 0, 0)
    bbox = im.getbbox()
    if bbox:
        pad = 4
        l, t, r2, b2 = bbox
        im = im.crop((max(0, l - pad), max(0, t - pad), min(w, r2 + pad), min(h, b2 + pad)))
    im.save(path, "PNG", optimize=True)
    print(f"punched {path.name} -> {im.size}", flush=True)


def slugify(name: str) -> str:
    s = re.sub(r"[^\w]+", "-", name, flags=re.UNICODE).strip("-").lower()
    return s or "pack"


def copy_and_punch_packs() -> dict[str, str]:
    """Returns map pack_id -> relative packImage path."""
    ASSETS.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}

    # Existing three packs already in assets — re-punch
    for name in ("pack-151.png", "pack-pokekyun.png", "pack-ThunderclapSpark.png"):
        p = ASSETS / name
        if p.exists():
            punch_black(p)

    for meta in EXTRA_PACKS:
        src = PACK_SRC / meta["file"]
        if not src.exists():
            print("missing", src)
            continue
        dest_name = f"pack-{meta['code'].lower()}.png"
        dest = ASSETS / dest_name
        shutil.copy2(src, dest)
        punch_black(dest)
        out[meta["id"]] = f"./assets/{dest_name}"
    return out


def http_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_kr_images(rel_path: str) -> dict[str, str]:
    """Map card number -> preferred KR image URL (name-aware for duplicate numbers)."""
    url = f"https://raw.githubusercontent.com/kinbo-ptcg/ptcg-kr-db/main/card_data_product/pack/{rel_path}"
    try:
        cards = http_json(url)
    except Exception as e:
        print("KR load fail", rel_path, e)
        return {}

    by_num: dict[str, list[dict]] = {}
    for c in cards:
        num = str(c.get("number") or "").split("/")[0].zfill(3)
        img = c.get("cardImgURL")
        if not img:
            continue
        if "w=" in img:
            img = re.sub(r"w=\d+", "w=800", img)
        by_num.setdefault(num, []).append({"name": c.get("name") or "", "url": img})

    def score_url(u: str) -> int:
        if "pokemonkorea.co.kr" in u:
            return 10
        if "firebasestorage" in u or "card32.appspot" in u:
            return -5
        return 0

    out: dict[str, str] = {}
    for num, entries in by_num.items():
        # Prefer official CDN; keep first official, else best scored
        entries_sorted = sorted(entries, key=lambda e: score_url(e["url"]), reverse=True)
        # For duplicate numbers store first for simple map; callers that need
        # name matching should use fix_kr_images.py / richer matcher.
        out[num] = entries_sorted[0]["url"]
        # Also index by normalized KR name for later optional use
        for e in entries_sorted:
            key = f"name:{(e['name'] or '').replace(' ', '')}"
            if key not in out:
                out[key] = e["url"]
    return out


def main() -> int:
    print("Copying / punching pack images…")
    extra_images = copy_and_punch_packs()

    print("Loading species lists…")
    ko_names = load_species_names("ko")
    en_names = load_species_names("en")
    ja_names = load_species_names("ja")
    ja_index = build_ja_dex_index(ja_names)

    packs_out = []
    catalog = []

    # Core 3 packs
    for pack in CORE_PACKS:
        print(f"Core pack {pack['sourceFolder']}…")
        jp_cards = fetch_jp_cards(pack["sourceFolder"])
        built = [to_catalog_card(c, pack, ko_names, en_names, ja_index) for c in jp_cards]
        if pack["id"] == "thunderclap-spark":
            from build_catalog import SM7A_EXTRAS

            existing = {c["id"] for c in built}
            for extra in SM7A_EXTRAS:
                if extra["id"] not in existing:
                    built.append(extra)
        row = {k: v for k, v in pack.items() if k not in {"sourceFolder", "idPrefix"}}
        row["cardIds"] = [c["id"] for c in built]
        packs_out.append(row)
        catalog.extend(built)
        print(f"  → {len(built)} cards")

    # Extra packs: pack entry always; cards only when JP folder exists
    for meta in EXTRA_PACKS:
        pack = {
            "id": meta["id"],
            "nameKo": meta["nameKo"],
            "nameEn": meta["nameEn"],
            "nameJa": meta["nameJa"],
            "code": meta["code"],
            "releaseYear": meta["releaseYear"],
            "languages": meta["languages"],
            "blurb": meta["blurb"],
            "blurbEn": meta["blurbEn"],
            "blurbJa": meta["blurbJa"],
            "packImage": extra_images.get(meta["id"], f"./assets/pack-{meta['code'].lower()}.png"),
            "coverCardId": None,
            "sourceFolder": meta["sourceFolder"],
            "idPrefix": meta["idPrefix"],
        }
        built = []
        try:
            print(f"Extra pack {meta['sourceFolder']}…")
            jp_cards = fetch_jp_cards(meta["sourceFolder"])
            built = [to_catalog_card(c, pack, ko_names, en_names, ja_index) for c in jp_cards]
            print(f"  → {len(built)} cards")
        except Exception as e:
            print(f"  (no JP catalog yet: {e})")
        if built:
            pack["coverCardId"] = built[0]["id"]
        row = {k: v for k, v in pack.items() if k not in {"sourceFolder", "idPrefix"}}
        row["cardIds"] = [c["id"] for c in built]
        packs_out.append(row)
        catalog.extend(built)

    print("Attaching multilingual images…")
    # KR map for core packs
    kr_maps = {
        "sv2a-151": load_kr_images("SV/SV2a.json"),
        "pokekyun": load_kr_images("XY/cp3.json"),
        "thunderclap-spark": load_kr_images("SM/sm7a.json"),
    }
    for meta in EXTRA_PACKS:
        if meta.get("krJson"):
            kr_maps[meta["id"]] = load_kr_images(meta["krJson"])

    attach_multilang_images(catalog)

    # Overlay real KR images (do not fake with JP)
    for card in catalog:
        images = card.setdefault("images", {})
        pack_id = card.get("packId")
        num = str(card.get("number") or "").split("/")[0].zfill(3)
        kr = (kr_maps.get(pack_id) or {}).get(num)
        images["kr"] = kr  # may be None — UI falls back honestly
        images["jp"] = images.get("jp") or card.get("image")
        if not images.get("en"):
            images["en"] = images.get("jp")

    asof = datetime.now(KST).isoformat(timespec="seconds")
    previous = load_previous_live(DATA)
    live, stats = build_live_snapshot(catalog, packs_out, asof, previous)
    restore_ebay_prices(live, previous)
    restore_brg_pops(live, previous)
    restore_psa_pops(live, previous)
    live["source"] = previous.get("source") or live.get("source") or "seed"
    live["generatedAt"] = asof
    write_data_bundle(DATA, packs_out, catalog, live)
    print(json.dumps({"packs": len(packs_out), "catalog": len(catalog), **stats}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
