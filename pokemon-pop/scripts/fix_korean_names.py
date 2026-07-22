# -*- coding: utf-8 -*-
"""Patch JP leftover names in catalog.json and rebuild data.js."""
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

from build_catalog import TRAINER_KO, split_suffix  # noqa: E402
from pokepop_snapshot import write_data_bundle  # noqa: E402

JP_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
UA = {"User-Agent": "PokePopNameFix/1.0"}

# Manual JP → (KO, EN) for trainers / special forms not covered by dex lookup
EXTRA_MAP: dict[str, tuple[str, str]] = {
    "基本草エネルギー": ("기본 풀 에너지", "Basic Grass Energy"),
    "基本炎エネルギー": ("기본 불 에너지", "Basic Fire Energy"),
    "基本水エネルギー": ("기본 물 에너지", "Basic Water Energy"),
    "基本悪エネルギー": ("기본 악 에너지", "Basic Darkness Energy"),
    "基本鋼エネルギー": ("기본 강철 에너지", "Basic Metal Energy"),
    "基本超エネルギー": ("기본 초 에너지", "Basic Psychic Energy"),
    "ヒート炎エネルギー": ("히트 불 에너지", "Heat Fire Energy"),
    "スピード雷エネルギー": ("스피드 번개 에너지", "Speed Lightning Energy"),
    "ホラー超エネルギー": ("호러 초 에너지", "Horror Psychic Energy"),
    "ハイド悪エネルギー": ("하이드 악 에너지", "Hide Darkness Energy"),
    "ウォッシュ水エネルギー": ("워시 물 에너지", "Wash Water Energy"),
    "コーティング鋼エネルギー": ("코팅 강철 에너지", "Coating Metal Energy"),
    "オーロラエネルギー": ("오로라 에너지", "Aurora Energy"),
    "キャプチャーエネルギー": ("캡처 에너지", "Capture Energy"),
    "ツインエネルギー": ("트윈 에너지", "Twin Energy"),
    "パワフル無色エネルギー": ("파워풀 무색 에너지", "Powerful Colorless Energy"),
    "セラピーエネルギー": ("테라피 에너지", "Therapeutic Energy"),
    "ルミナスエネルギー": ("루미너스 에너지", "Luminous Energy"),
    "レガシーエネルギー": ("레거시 에너지", "Legacy Energy"),
    "ミストエネルギー": ("미스트 에너지", "Mist Energy"),
    "ブーメランエネルギー": ("부메랑 에너지", "Boomerang Energy"),
    "ネオアッパーエネルギー": ("네오 어퍼 에너지", "Neo Upper Energy"),
    "トレジャーエネルギー": ("트레저 에너지", "Treasure Energy"),
    "スパイクエネルギー": ("스파이크 에너지", "Spikemuth Gym"),
    "イグニッションエネルギー": ("이그니션 에너지", "Ignition Energy"),
    "プリズムエネルギー": ("프리즘 에너지", "Prism Energy"),
    "ロケット団エネルギー": ("로켓단 에너지", "Team Rocket Energy"),
    "リッチエネルギー": ("리치 에너지", "Lush Energy"),
    "ジェットエネルギー": ("제트 에너지", "Jet Energy"),
    "メディカルエネルギー": ("메디컬 에너지", "Medical Energy"),
    "リバーサルエネルギー": ("리버설 에너지", "Reversal Energy"),
    "ブーストエナジー 古代": ("부스트 에너지 고대", "Ancient Booster Energy Capsule"),
    "ブーストエナジー 未来": ("부스트 에너지 미래", "Future Booster Energy Capsule"),
    "ダブル無色エネルギー": ("더블 무색 에너지", "Double Colorless Energy"),
    "ユニットエネルギー草炎水": ("유닛 에너지 풀불물", "Unit Energy GFW"),
    "なみのりピカチュウV": ("파도타기 피카츄 V", "Surfing Pikachu V"),
    "なみのりピカチュウVMAX": ("파도타기 피카츄 VMAX", "Surfing Pikachu VMAX"),
    "そらをとぶピカチュウV": ("하늘을 나는 피카츄 V", "Flying Pikachu V"),
    "そらをとぶピカチュウVMAX": ("하늘을 나는 피카츄 VMAX", "Flying Pikachu VMAX"),
    "ピカチュウV-UNION": ("피카츄 V-UNION", "Pikachu V-UNION"),
    "ブラックキュレムex": ("블랙큐레무 ex", "Black Kyurem ex"),
    "アローラ ナッシーex": ("알로라 나시 ex", "Alolan Exeggutor ex"),
    "ガラル ヒヒダルマV": ("가라르 불비달마 V", "Galarian Darmanitan V"),
    "ガラル ヒヒダルマVMAX": ("가라르 불비달마 VMAX", "Galarian Darmanitan VMAX"),
    "ガラル ネギガナイトV": ("가라르 창파나이트 V", "Galarian Sirfetch'd V"),
    "パルデア ドオーex": ("팔데아 오뚜검? ", "Paldean Clodsire ex"),
    "パルデア ドオーex": ("팔데아 토오 ex", "Paldean Clodsire ex"),
    "オーガポン みどりのめんex": ("오거폰 녹색 가면 ex", "Ogerpon Teal Mask ex"),
    "オーガポン かまどのめんex": ("오거폰 화덕 가면 ex", "Ogerpon Hearthflame Mask ex"),
    "オーガポン いどのめんex": ("오거폰 우물 가면 ex", "Ogerpon Wellspring Mask ex"),
    "オーガポン いしずえのめんex": ("오거폰 주춧돌 가면 ex", "Ogerpon Cornerstone Mask ex"),
    "ガチグマ アカツキex": ("다투곰 아카쓰기 ex", "Bloodmoon Ursaluna ex"),
    "ナンジャモのハラバリーex": ("모란의 따라큐? ", "Iono's Bellibolt ex"),
    "ナンジャ모のハラバリーex": ("모란의 찌리리공? ", "Iono's Bellibolt ex"),
    "ナンジャモのハラバリーex": ("모란의 찌리리공? ", "Iono's Bellibolt ex"),
    "ナンジャモのハラバリーex": ("모란의 찌리리리? ", "Iono's Bellibolt ex"),
    "ナンジャモのハラバリーex": ("모란의 찌리비비드? ", "Iono's Bellibolt ex"),
    "ナンジャモのハラバリーex": ("모란의 찌리리공? ", "Iono's Bellibolt ex"),
    # Bellibolt KR = 찌리비비드
    "ナンジャモのハラバリーex": ("모란의 찌리비비드 ex", "Iono's Bellibolt ex"),
    "Nのゾロアークex": ("N의 조로아크 ex", "N's Zoroark ex"),
    "ホップのザシアンex": ("호프의 자시안 ex", "Hop's Zacian ex"),
    "ヒビキのホウオウex": ("히비키의 칠색조 ex", "Ethan's Ho-Oh ex"),
    "シロナのガブリアスex": ("난천의 한카리아스 ex", "Cynthia's Garchomp ex"),
    "ペパーのマフィティフex": ("페퍼의 마피티프 ex", "Pepper's Mabosstiff ex"),
    "リーリエのピッピex": ("릴리에의 삐삐 ex", "Lillie's Clefairy ex"),
    "ロケット団のファイヤーex": ("로켓단의 파이어 ex", "Team Rocket's Moltres ex"),
    "ロケット団のミュウツーex": ("로켓단의 뮤츠 ex", "Team Rocket's Mewtwo ex"),
    "ロケット団のニドキングex": ("로켓단의 니드킹 ex", "Team Rocket's Nidoking ex"),
    "ロケット団のクロバットex": ("로켓단의 크로뱃 ex", "Team Rocket's Crobat ex"),
    "ロケット団のペルシアンex": ("로켓단의 페르시온 ex", "Team Rocket's Persian ex"),
    "メガフシギバナex": ("메가 이상해꽃 ex", "Mega Venusaur ex"),
    "メガバクーダex": ("메가 폭타 ex", "Mega Camerupt ex"),
    "メガルカリオex": ("메가 루카리오 ex", "Mega Lucario ex"),
    "メガサーナイトex": ("메가 가디안 ex", "Mega Gardevoir ex"),
    "メガリザードンXex": ("메가 리자몽X ex", "Mega Charizard X ex"),
    "メガリザードンYex": ("메가 리자몽Y ex", "Mega Charizard Y ex"),
    "メガカイリューex": ("메가 망나뇽 ex", "Mega Dragonite ex"),
    "メガゲッコウガex": ("메가 개굴닌자 ex", "Mega Greninja ex"),
    "メガジガルデex": ("메가 지가르데 ex", "Mega Zygarde ex"),
    "メガダークライex": ("메가 다크라이 ex", "Mega Darkrai ex"),
    "メガアブソルex": ("메가 앱솔 ex", "Mega Absol ex"),
    "メガクチートex": ("메가 입치트 ex", "Mega Mawile ex"),
    "メガユキノオーex": ("메가 눈설왕 ex", "Mega Abomasnow ex"),
    "メガライボルトex": ("메가 썬더라이 ex", "Mega Manectric ex"),
    "メガサーナイトex": ("메가 가디안 ex", "Mega Gardevoir ex"),
    "メガラティアスex": ("메가 라티아스 ex", "Mega Latias ex"),
    "メガガルーラex": ("메가 캥카 ex", "Mega Kangaskhan ex"),
    # Common trainers / items
    "博士の研究（オーキド博士）": ("박사의 연구（오박사）", "Professor's Research (Professor Oak)"),
    "博士の研究（マグノリア博士）": ("박사의 연구（마그놀리아 박사）", "Professor's Research (Professor Magnolia)"),
    "博士の研究": ("박사의 연구", "Professor's Research"),
    "カビゴンドール": ("잠만보 인형", "Snorlax Doll"),
    "大地の器": ("대지의 그릇", "Earthen Vessel"),
    "まけんきチョッキ": ("오기 조끼", "Covert Cloak"),
    "ワザマシン デヴォリューション": ("기술머신 디볼루션", "Technical Machine: Devolution"),
    "ワザマシン エナジーターボ": ("기술머신 에너지터보", "Technical Machine: Turbo Energize"),
    "ワザマシン やみうち": ("기술머신 기습", "Technical Machine: Blindside"),
    "ワザマシン エヴォリューション": ("기술머신 에볼루션", "Technical Machine: Evolution"),
    "ワザマシン かじばのいっぱつ": ("기술머신 불티의 일발", "Technical Machine: Turbo Energize"),
    "ワザマシン フローライト": ("기술머신 플로라이트", "Technical Machine: Evolution"),
    "オーリム博士の気迫": ("사다 박사의 기백", "Professor Sada's Vitality"),
    "フトゥー博士のシナリオ": ("투로 박사의 시나리오", "Professor Turo's Scenario"),
    "センリ": ("제리", "Carmine"),
    "メロコ": ("멜로코", "Mela"),
    "ゴージャスマント": ("고저스 망토", "Sparkling Crystal"),
    "デンジャラス光線": ("덴저러스 광선", "Dangerous Laser"),
    "ポケバイタルA": ("포켓바이탈 A", "Poké Vital A"),
    "夜のタンカ": ("밤의 들것", "Night Stretcher"),
    "くさりもち": ("사슬 망치", "Binding Mochi"),
    "力の砂時計": ("힘의 모래시계", "Powerglass"),
    "アクロマの執念": ("아크로마의 집념", "Colress's Tenacity"),
    "アンズの秘技": ("안즈의 비기", "Janine's Secret Art"),
    "カシオペア": ("카시오페아", "Cassiopeia"),
    "クセロシキのたくらみ": ("크세로시키의 음모", "Xerosic's Machinations"),
    "ニュートラルセンター": ("뉴트럴 센터", "Neutral Center"),
    "夜のアカデミー": ("밤의 아카데미", "Night Academy"),
    "エネルギー転送PRO": ("에너지 전송 PRO", "Energy Transfer PRO"),
    "おたすけベル": ("도우미 벨", "Helpful Bell"),
    "ダークボール": ("다크볼", "Dark Ball"),
    "ぼうがいレター": ("방해 레터", "Jamming Letter"),
    "メガトンブロアー": ("메가톤 블로어", "Megaton Blower"),
    "竜の秘薬": ("용의 비약", "Dragon Elixir"),
    "イトケのみ": ("이토케열매", "Occa Berry"),
    "カキツバタ": ("브라이어", "Briar"),
    "サーファー": ("서퍼", "Surfer"),
    "ドラセナ": ("드라세나", "Drasna"),
    "ルチアのアピール": ("루치아의 어필", "Lucia's Appeal"),
    "ふしぎなアメ": ("이상한 사탕", "Rare Candy"),
    "アオキ": ("제이드", "Kieran"),
    "シキミ": ("레이시", "Lacey"),
    "チリ": ("칠리", "Crispin"),
    "パラソルおねえさん": ("파라솔 아가씨", "Parasol Lady"),
    "ビーチコート": ("비치 코트", "Beach Court"),
    "ロケット団のおじゃまロボ": ("로켓단의 방해 로봇", "Team Rocket's Interfere Robo"),
    "ロケット団のスーパーボール": ("로켓단의 슈퍼볼", "Team Rocket's Great Ball"),
    "ロケット団のびっくりボム": ("로켓단의 깜짝 폭탄", "Team Rocket's Surprise Bomb"),
    "ロケット団のレシーバー": ("로켓단의 리시버", "Team Rocket's Receiver"),
    "ロケット団のアテナ": ("로켓단의 아테나", "Team Rocket's Ariana"),
    "ロケット団のアポロ": ("로켓단의 아폴로", "Team Rocket's Archer"),
    "ロケット団のサカキ": ("로켓단의 비주", "Team Rocket's Giovanni"),
    "ロケット団のラムダ": ("로켓단의 람다", "Team Rocket's Proton"),
    "ロケット団のランス": ("로켓단의 란스", "Team Rocket's Petrel"),
    "ロケット団の監視塔": ("로켓단의 감시탑", "Team Rocket's Watchtower"),
    "ロケット団のファクトリー": ("로켓단의 팩토리", "Team Rocket's Factory"),
    "メガシグナル": ("메가 시그널", "Mega Signal"),
    "アイアンディフェンダー": ("아이언 디펜더", "Iron Defender"),
    "パワープロテイン": ("파워 프로틴", "Power Protein"),
    "ファイトゴング": ("파이트 공", "Fighting Gong"),
    "むしよけスプレー": ("벌레 퇴치 스프레이", "Repel"),
    "マチスの取引": ("마티스의 거래", "Lt. Surge's Bargain"),
    "リーリエの決心": ("릴리에의 결심", "Lillie's Determination"),
    "危ない廃墟": ("위험한 폐허", "Dangerous Ruins"),
    "リーリエのしんじゅ": ("릴리에의 진주", "Lillie's Pearl"),
    "むしとりセット": ("벌레잡이 세트", "Bug Catching Set"),
    "ファイトオレ": ("파이트 올레", "Fighting Au Lait"),
    "ジャミングタワー": ("재밍 타워", "Jamming Tower"),
    "あやしい時計": ("수상한 시계", "Unidentified Fossil"),
    "アセロラのいたずら": ("아세로라의 장난", "Acerola's Mischief"),
    "ミツルの思いやり": ("미츠루의 배려", "Mallow's Freshness"),
    "活力の森": ("활력의 숲", "Forest of Vitality"),
    "なみのりビーチ": ("파도타기 비치", "Surfing Beach"),
    "ミステリーガーデン": ("미스터리 가든", "Mystery Garden"),
    "カウンターキャッチャー": ("카운터 캐처", "Counter Catcher"),
    "テクノレーダー": ("테크노 레이더", "Techno Radar"),
    "のろいのはたき": ("저주의 먼지떨이", "Cursed Feather"),
    "ヒョウタ": ("효타", "Larry"),
    "リップ": ("립", "Rip"),
    "いいきずぐすり": ("좋은 상처약", "Potion"),
    "Nのポイントアップ": ("N의 포인트 업", "N's PP Up"),
    "とりかえチケット": ("교환 티켓", "Switch Cart"),
    "ホップのバッグ": ("호프의 가방", "Hop's Bag"),
    "ホップのこだわりハチマキ": ("호프의 고집 머리띠", "Hop's Choice Band"),
    "アイリスの闘志": ("아이리스의 투지", "Iris's Fighting Spirit"),
    "怖いお兄さん": ("무서운 오빠", "Spikemuth Gym"),
    "タケシのスカウト": ("웅의 스카우트", "Brock's Scouting"),
    "Nの城": ("N의 성", "N's Castle"),
    "ハッコウシティ": ("핫코우 시티", "Castelia City"),
    "ハロンタウン": ("하론 타운", "Opelucid City"),
    "鬼の仮面": ("귀신의 가면", "Mask of Ogerpon"),
    "おはやし笛": ("응원 피리", "Festival Lead"),
    "シークレットボックス": ("시크릿 박스", "Secret Box"),
    "ポケモン回収サイクロン": ("포켓몬 회수 사이클론", "Pokémon Catcher"),
    "ハンディサーキュレーター": ("핸디 서큘레이터", "Handheld Fan"),
    "スグリ": ("스구리", "Cyrano"),
    "ゼイユ": ("제이유", "Jacq"),
    "ハッサク": ("핫사쿠", "Hassaku"),
    "お祭り会場": ("축제 회장", "Festival Grounds"),
    "改造ハンマー": ("개조 해머", "Enhanced Hammer"),
    "なかよしポフィン": ("절친 포핀", "Buddy-Buddy Poffin"),
    "ハンドトリマー": ("핸드 트리머", "Hand Trimmer"),
    "プライムキャッチャー": ("프라임 캐처", "Prime Catcher"),
    "リブートポッド": ("리부트 포드", "Reboot Pod"),
    "ヒーローマント": ("히어로 망토", "Hero's Cape"),
    "ヘビーバトン": ("헤비 바톤", "Heavy Baton"),
    "暗号マニアの解読": ("암호 매니아의 해독", "Cryptographic Code"),
    "セイジ": ("세이지", "Clavell"),
    "ベルのまごころ": ("벨의 진심", "Bianca's Devotion"),
    "フルメタルラボ": ("풀메탈 랩", "Full Metal Lab"),
    "エール団のおうえんタオル": ("응원단의 응원 타월", "Cheer Towel"),
    "回収ネット": ("회수 네트", "Rescue Net"),
    "クイックボール": ("퀵볼", "Quick Ball"),
    "しんかのおこう": ("진화의 향로", "Evolution Incense"),
    "すごいきずぐすり": ("대단한 상처약", "Hyper Potion"),
    "ターボパッチ": ("터보 패치", "Energy Switch"),
    "たっぷりバケツ": ("듬뿍 양동이", "Nest Ball"),
    "ツールスクラッパー": ("툴 스크래퍼", "Tool Scrapper"),
    "ふつうのつりざお": ("보통 낚싯대", "Ordinary Rod"),
    "めずらしい化石": ("희귀한 화석", "Rare Fossil"),
    "メタルソーサー": ("메탈 소서", "Metal Saucer"),
    "ロトムじてんしゃ": ("로토무 자전거", "Rotom Bike"),
    "くちたけん": ("썩은 검", "Rusted Sword"),
    "くちたたて": ("썩은 방패", "Rusted Shield"),
    "タフネスマント": ("터프니스 망토", "Air Balloon"),
    "ふうせん": ("풍선", "Air Balloon"),
    "とりつかい": ("새조련사", "Bird Keeper"),
    "ネズ": ("네즈", "Piers"),
    "ボールガイ": ("볼 가이", "Ball Guy"),
    "ボスの指令（サカキ）": ("보스의 지령（비주）", "Boss's Orders (Giovanni)"),
    "ボスの指令": ("보스의 지령", "Boss's Orders"),
    "マリィ": ("마리", "Marnie"),
    "ローズ": ("로즈", "Rose"),
    "ターフスタジアム": ("터프 스타디움", "Turffield Stadium"),
    "トレーニングコート": ("트레이닝 코트", "Training Court"),
    "ルミナスメイズの森": ("루미너스 메이즈 숲", "Path to the Peak"),
    "ローズタワー": ("로즈 타워", "Rose Tower"),
    "ウカッツ": ("우카츠", "Oleana"),
    "ジムトレーナー": ("체육관 트레이너", "Gym Trainer"),
    "フウロ": ("풍로", "Skyla"),
    "ポケモンごっこ": ("포켓몬 흉내", "Pokémon Breeder"),
    "エレキジェネレーター": ("일렉 제너레이터", "Electric Generator"),
    "スーパーエネルギー回収": ("슈퍼 에너지 회수", "Energy Retrieval"),
    "すごいつりざお": ("대단한 낚싯대", "Cross Switcher"),
    "ネストボール": ("네스트볼", "Nest Ball"),
    "ネモのリュック": ("네모의 배낭", "Nemona's Backpack"),
    "はげましのてがみ": ("격려의 편지", "Letter of Encouragement"),
    "岩のむねあて": ("바위의 흉갑", "Rocky Helmet"),
    "まけんきハチマキ": ("오기 머리띠", "Choice Band"),
    "勇気のおまもり": ("용기의 부적", "Bravery Charm"),
    "オモダカ": ("게타", "Geeta"),
    "クラベル": ("클라벨", "Clavell"),
    "ナンジャモ": ("모란", "Iono"),
    "ネルケ": ("넬케", "Tulip"),
    "パルデアの学生": ("팔데아의 학생", "Student of Paldea"),
    "ペパー": ("페퍼", "Arven"),
    "ボタン": ("버튼", "Penny"),
    "タウンデパート": ("타운 백화점", "Town Store"),
    "ボウルタウン": ("보울 타운", "Mesagoza"),
    "ポケモンリーグ本部": ("포켓몬리그 본부", "Pokémon League Headquarters"),
    "レッスンスタジオ": ("레슨 스튜디오", "Artazon"),
    "ネモ": ("네모", "Nemona"),
    "グルーシャ": ("그루샤", "Grusha"),
    "ピーニャ": ("피냐", "Atticus"),
    "災いの雪山": ("재앙의 설산", "Frosted Mountain"),
    "エネルギーコイン": ("에너지 코인", "Energy Coin"),
    "古びたふたの化石": ("낡은 뚜껑의 화석", "Antique Cover Fossil"),
    "ポケギア3.0": ("포켓기어 3.0", "Pokégear 3.0"),
    "Nの筋書き": ("N의 각본", "N's Plan"),
    "マコモ": ("마코모", "Roxanne"),
    "エネルギー回収": ("에너지 회수", "Energy Retrieval"),
    "古びたはねの化石": ("낡은 날개의 화석", "Antique Feather Fossil"),
    "ブレイブバングル": ("브레이브 뱅글", "Brave Bangle"),
    "クラウン": ("크라운", "Crown"),
    "チェレン": ("체렌", "Cheren"),
    "トウコ": ("토우코", "Hilda"),
    "ガラスのラッパ": ("유리 나팔", "Glass Trumpet"),
    "古びたねっこの化石": ("낡은 뿌리의 화석", "Antique Root Fossil"),
    "ウタンのみ": ("우탄열매", "Charti Berry"),
    "オッカのみ": ("옷카열매", "Occa Berry"),
    "きらめく結晶": ("반짝이는 결정", "Sparkling Crystal"),
    "重力玉": ("중력 구슬", "Gravity Gem"),
    "デラックスボム": ("디럭스 봄", "Deluxe Bomb"),
    "アカマツ": ("아카마츠", "Cyrano"),
    "タロ": ("타로", "Lacey"),
    "ハイダイ": ("하이다이", "Drayton"),
    "ブライア": ("브라이어", "Briar"),
    "偉大な大樹": ("위대한 거목", "Grand Tree"),
    "ゼロの大空洞": ("제로의 대공동", "Area Zero Underdepths"),
    "ドローンロトム": ("드론 로토무", "Rotom Phone"),
    "望遠スコープ": ("망원 스코프", "Telescope"),
    "メモリーカプセル": ("메모리 캡슐", "Memory Capsule"),
    "サイトウ": ("사이토", "Bea"),
    "ダンデ": ("단데", "Leon"),
    "リーグスタッフ": ("리그 스태프", "League Staff"),
    "ルリナ": ("루리나", "Nessa"),
    "キルクス温泉": ("키르쿠스 온천", "Circhester Baths"),
    "シュートスタジアム": ("슈트 스타디움", "Spikemuth Gym"),
    "せいなるはい": ("성스러운 재", "Sacred Ash"),
    "ペパーのサンドウィッチ": ("페퍼의 샌드위치", "Arven's Sandwich"),
    "シロナのパワーウエイト": ("난천의 파워 웨이트", "Cynthia's Power Weight"),
    "MCの盛り上げ": ("MC의 분위기 띄우기", "Contest Spectacular"),
    "ヒビキの冒険": ("히비키의 모험", "Ethan's Adventure"),
    "おとりよせボックス": ("주문 박스", "Order Pad"),
    "覚醒のドラム": ("각성의 드럼", "Awakening Drum"),
    "緊急ボード": ("긴급 보드", "Rescue Board"),
    "マキシマムベルト": ("맥시멈 벨트", "Maximum Belt"),
    "探検家の先導": ("탐험가의 선도", "Explorer's Guidance"),
    "ビワ": ("비와", "Eri"),
    "マツバの確信": ("마츠바의 확신", "Will's Confidence"),
    "危険な密林": ("위험한 밀림", "Dangerous Jungle"),
    "ぐんぐんシェイク": ("쑥쑥 셰이크", "Growth Shake"),
    "ドリームボール": ("드림볼", "Dream Ball"),
    "エレメンタルバッジ": ("엘리멘탈 뱃지", "Elemental Badge"),
    "スノーリーフバッジ": ("스노리프 뱃지", "Snow Leaf Badge"),
    "月と太陽のバッジ": ("달과 태양의 뱃지", "Moon & Sun Badge"),
    "リボンバッジ": ("리본 뱃지", "Ribbon Badge"),
    "アロマなおねえさん": ("아로마 아가씨", "Aroma Lady"),
    "マクワ": ("마쿠와", "Melony"),
    "ファッションモール": ("패션 몰", "Fashion Mall"),
    "当たりつきアイス": ("당첨 아이스", "Lucky Ice Cream"),
    "スーパーボール": ("슈퍼볼", "Great Ball"),
    "トイキャッチャー": ("토이 캐처", "Toy Catcher"),
    "ゴムのグローブ": ("고무 장갑", "Rubber Gloves"),
    "れいかいのお面": ("영계의 가면", "Reaper Cloth"),
    "れんげきの巻物 飛竜の巻": ("연격의 두루마리 비룡의 권", "Rapid Strike Scroll"),
    "サナ": ("사나", "Shauna"),
    "スクールボーイ": ("스쿨보이", "Schoolboy"),
    "ヒガナの決意": ("히가나의 결의", "Zinnia's Resolve"),
    "嵐の山脈": ("폭풍의 산맥", "Stormy Mountains"),
    "推理セット": ("추리 세트", "Detective Kit"),
    "スクランブルスイッチ": ("스크램블 스위치", "Scramble Switch"),
    "のんびりじゃらし": ("느긋한 장난감", "Lazy Cat Toy"),
    "ミラクルインカム": ("미라클 인컴", "Miracle Income"),
    "希望のアミュレット": ("희망의 아뮬렛", "Hope Amulet"),
    "ナモのみ": ("나모열매", "Colbur Berry"),
    "リリバのみ": ("리리바열매", "Rindo Berry"),
    "シアノ": ("시아노", "Carmine"),
    "シトロンの機転": ("시트론의 기민", "Clemont's Quick Wit"),
    "ミカンのまなざし": ("밀감의 눈빛", "Jasmine's Gaze"),
    "エキサイトスタジアム": ("익사이트 스타디움", "Exciting Stadium"),
    "グラビティーマウンテン": ("그래비티 마운틴", "Gravity Mountain"),
    "アンフェアスタンプ": ("언페어 스탬프", "Unfair Stamp"),
    "ハイパーアロマ": ("하이퍼 아로마", "Hyper Aroma"),
    "ラブラブボール": ("러브러브볼", "Love Ball"),
    "サバイブギプス": ("서바이브 깁스", "Survive Cast"),
    "ラッキーメット": ("럭키 헬멧", "Lucky Helmet"),
    "管理人": ("관리인", "Caretaker"),
    "ゴヨウ": ("고요우", "Goyo"),
    "サザレ": ("사자레", "Sazare"),
    "スイレンのお世話": ("수련의 보살핌", "Lana's Aid"),
    "公民館": ("공민관", "Community Center"),
    "おとどけドローン": ("배달 드론", "Delivery Drone"),
    "サワロ": ("사와로", "Sawaro"),
    "災いの荒野": ("재앙의 황야", "Calamitous Wasteland"),
    "つりざおMAX": ("낚싯대 MAX", "Fishing Rod MAX"),
    "テラスタルオーブ": ("테라스탈 오브", "Tera Orb"),
    "トレジャーガジェット": ("트레저 가젯", "Treasure Gadget"),
    "ハバンのみ": ("하반열매", "Haban Berry"),
    "アオキの手際": ("제이드의 솜씨", "Kieran's Skill"),
    "ネリネ": ("네리네", "Neri"),
    "パルデアの仲間たち": ("팔데아의 동료들", "Friends in Paldea"),
    "月明かりの丘": ("달빛 언덕", "Moonlit Hill"),
    "オルティガ": ("오르티가", "Ortig"),
    "コルサ": ("콜사", "Korrina"),
    "シュウメイ": ("슈메이", "Shumei"),
    "タイム": ("타임", "Tyme"),
    "レホール": ("레홀", "Rhyme"),
    "パトロールキャップ": ("패트롤 캡", "Patrol Cap"),
    "リベンジパンチ": ("리벤지 펀치", "Revenge Punch"),
    "ポピー": ("포피", "Poppy"),
    "ライム": ("라임", "Rika"),
    "サンダーマウンテンprismstar": ("썬더마운틴◇", "Thunder Mountain ◇"),
}

# Owner / form prefixes: JP → (KO, EN)
PREFIXES = [
    ("ロケット団の", "로켓단의 ", "Team Rocket's "),
    ("リーリエの", "릴리에의 ", "Lillie's "),
    ("ナンジャモの", "모란의 ", "Iono's "),
    ("ホップの", "호프의 ", "Hop's "),
    ("ヒビキの", "히비키의 ", "Ethan's "),
    ("シロナの", "난천의 ", "Cynthia's "),
    ("ペパーの", "페퍼의 ", "Arven's "),
    ("Nの", "N의 ", "N's "),
    ("アローラ ", "알로라 ", "Alolan "),
    ("アローラ", "알로라 ", "Alolan "),
    ("ガラル ", "가라르 ", "Galarian "),
    ("ガラル", "가라르 ", "Galarian "),
    ("パルデア ", "팔데아 ", "Paldean "),
    ("パルデア", "팔데아 ", "Paldean "),
    ("ブラック", "블랙", "Black "),
    ("ホワイト", "화이트", "White "),
]


def has_jp(text: str) -> bool:
    return bool(JP_RE.search(text or ""))


def http_json(url: str):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_species(lang: str) -> list[str]:
    return http_json(f"https://raw.githubusercontent.com/sindresorhus/pokemon/master/data/{lang}.json")


def build_ja_index(ja_names: list[str]) -> dict[str, int]:
    return {name: i + 1 for i, name in enumerate(ja_names)}


def resolve_via_dex(jp_name: str, ja_index: dict[str, int], ko_names: list[str], en_names: list[str]):
    work = jp_name
    ko_prefix = ""
    en_prefix = ""
    for jp_p, ko_p, en_p in PREFIXES:
        if work.startswith(jp_p):
            work = work[len(jp_p) :]
            ko_prefix = ko_p
            en_prefix = en_p
            break

    base, suffix, mega = split_suffix(work)
    # strip regional leftover spaces
    base = base.strip()
    dex = ja_index.get(base)
    if not dex:
        # try without spaces
        dex = ja_index.get(base.replace(" ", ""))
    if not dex:
        return None
    ko = ko_names[dex - 1] + suffix
    en = en_names[dex - 1] + suffix
    if mega:
        ko = f"메가 {ko}"
        en = f"Mega {en}"
    return ko_prefix + ko, en_prefix + en


def resolve_name(jp_name: str, ja_index, ko_names, en_names):
    if jp_name in EXTRA_MAP:
        return EXTRA_MAP[jp_name]
    if jp_name in TRAINER_KO:
        return TRAINER_KO[jp_name], jp_name  # EN unknown → keep for now, fix EN separately
    # TRAINER_KO only KO — still useful
    auto = resolve_via_dex(jp_name, ja_index, ko_names, en_names)
    if auto:
        return auto
    # prism star cleanup
    cleaned = jp_name.replace("prismstar", "◇")
    if cleaned in TRAINER_KO:
        return TRAINER_KO[cleaned], cleaned
    if cleaned in EXTRA_MAP:
        return EXTRA_MAP[cleaned]
    return None


def main() -> int:
    print("Loading species lists…")
    ko_names = load_species("ko")
    en_names = load_species("en")
    ja_names = load_species("ja")
    ja_index = build_ja_index(ja_names)

    catalog_path = DATA / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    fixed = 0
    missing: dict[str, int] = {}

    for card in catalog:
        ja = card.get("nameJa") or ""
        ko = card.get("nameKo") or ""
        en = card.get("nameEn") or ""
        if not (has_jp(ko) or has_jp(en)):
            continue

        mapped = resolve_name(ja, ja_index, ko_names, en_names)
        if not mapped:
            mapped = resolve_name(ko, ja_index, ko_names, en_names)
        if not mapped:
            key = ja if has_jp(ja) else ko
            missing[key] = missing.get(key, 0) + 1
            continue

        new_ko, new_en = mapped
        # If EN still Japanese, try dex again for EN only
        if has_jp(new_en):
            auto = resolve_via_dex(ja, ja_index, ko_names, en_names)
            if auto:
                new_en = auto[1]
            elif ja in EXTRA_MAP:
                new_en = EXTRA_MAP[ja][1]

        changed = False
        if has_jp(ko) or ko == ja:
            card["nameKo"] = new_ko
            changed = True
        if has_jp(en) or en == ja or has_jp(card.get("nameEn") or ""):
            if not has_jp(new_en):
                card["nameEn"] = new_en
                changed = True
            elif new_en != en and not has_jp(new_en):
                card["nameEn"] = new_en
                changed = True
        if changed:
            fixed += 1

    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packs = json.loads((DATA / "packs.json").read_text(encoding="utf-8"))
    live = json.loads((DATA / "live" / "pop-price.json").read_text(encoding="utf-8"))
    write_data_bundle(DATA, packs, catalog, live)

    still = sorted({c["nameKo"] for c in catalog if has_jp(c.get("nameKo") or "")})
    print(json.dumps({"fixed": fixed, "still_jp_nameKo": len(still), "missing": len(missing)}, ensure_ascii=False, indent=2))
    if still:
        print("remaining:", still[:80])
        print("… total remaining unique", len(still))
    if missing:
        print("unmapped sample:", list(missing.items())[:30])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
