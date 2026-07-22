/** UI i18n for PokePop (ko / en / ja) */
window.PopTracker = window.PopTracker || {};

(function (PT) {
  const STORAGE_KEY = "pokepop-ui-lang";

  PT.UI_LANGS = ["ko", "en", "ja"];

  const STR = {
    ko: {
      siteTagline: "포켓몬카드팩을 골라 그레이딩 POP과 eBay 시세를 한번에 확인할 수 있어요.",
      open: "OPEN →",
      backPacks: "← 팩 목록",
      sort: "정렬",
      type: "속성",
      language: "언어",
      all: "전체",
      sortNumber: "번호순",
      sortPriceDesc: "가격 높은순",
      sortPriceAsc: "가격 낮은순",
      sortType: "속성순",
      sortRarity: "등급(희귀도)순",
      sortName: "이름순",
      emptyPack: "팩을 찾을 수 없습니다.",
      emptyCards: "조건에 맞는 카드가 없습니다.",
      emptyData: "데이터를 불러오지 못했습니다. 페이지를 새로고침 해주세요.",
      emptyCard: "카드를 찾을 수 없습니다.",
      priceLabel: "eBay 시세 (PSA)",
      pricePendingEbay: "eBay 시세 대기 (시드 가격은 표시하지 않음)",
      popTitle: "POP REPORT",
      popGrader: "그레이딩",
      popTotalRow: "전체 합계",
      popEmpty: "POP 데이터 없음",
      notCollected: "아직 수집되지 않았습니다.",
      noData: "데이터 없음",
      imageFallback: "해당 언어 카드 이미지가 없어 다른 판본 이미지를 표시합니다.",
      updatedPrefix: "데이터 갱신:",
      snapshotPrefix: "POP/가격 스냅샷:",
      footnote:
        "BRG는 break.co.kr 실POP(열: 10=BRG100 · 9.5=BRG90 · 9=BRG85 · 8=BRG80). PSA·BGS·CGC 등은 아직 미연동. 가격은 eBay API 연동 시에만 표시됩니다.",
      credit:
        "Holo effect adapted from simeydotme/pokemon-cards-css (GPL-3.0). Card images via Pokémon card sources. BRG POP는 매시간 자동 갱신. eBay 시세는 GitHub Secrets(EBAY_CLIENT_ID/SECRET) 등록 후 수집됩니다.",
      setFallback: "세트",
      editionJp: "JP",
      editionKr: "KR",
      editionEn: "EN",
      uiKo: "KR",
      uiEn: "EN",
      uiJa: "JP",
      searchPlaceholder: "포켓몬 이름 검색",
      searchEmpty: "검색 결과가 없습니다.",
      searchPack: "팩",
      searchTitle: "검색 결과",
      searchClear: "검색 닫기",
      searchCount: "{n}장",
      packsSectionTitle: "팩 목록",
      packNoCardsYet: "카드 목록 준비 중 (JP 데이터 소스에 세트 미등록)",
      ebayPriceLink: "eBay에서 검색 →",
      psaSetPopLink: "PSA 세트 POP →",
      psaSetPopSearch: "PSA에서 세트 검색 →",
      emptyPackCards:
        "이 팩은 아직 카드 데이터가 없습니다. JP 카드 DB에 세트가 등록되면 추가됩니다.",
    },
    en: {
      siteTagline: "Browse packs and check grading POP counts with eBay PSA asking prices.",
      open: "OPEN →",
      backPacks: "← Packs",
      sort: "Sort",
      type: "Type",
      language: "Language",
      all: "All",
      sortNumber: "Number",
      sortPriceDesc: "Price: high to low",
      sortPriceAsc: "Price: low to high",
      sortType: "Type",
      sortRarity: "Rarity",
      sortName: "Name",
      emptyPack: "Pack not found.",
      emptyCards: "No cards match these filters.",
      emptyData: "Could not load data. Please refresh.",
      emptyCard: "Card not found.",
      priceLabel: "eBay Price (PSA)",
      pricePendingEbay: "Waiting for eBay (seed placeholders hidden)",
      popTitle: "POP REPORT",
      popGrader: "Grader",
      popTotalRow: "All graders",
      popEmpty: "No POP data",
      notCollected: "Not collected yet.",
      noData: "No data",
      imageFallback: "No card art for this language — showing another edition.",
      updatedPrefix: "Updated:",
      snapshotPrefix: "POP/price snapshot:",
      footnote:
        "BRG is live from break.co.kr (cols: 10=BRG100 · 9.5=BRG90 · 9=BRG85 · 8=BRG80). PSA/BGS/CGC are not wired yet. Prices appear only after eBay API credentials are set.",
      credit:
        "Holo effect adapted from simeydotme/pokemon-cards-css (GPL-3.0). Card images via Pokémon card sources. BRG POP refreshes hourly. eBay prices require GitHub Secrets EBAY_CLIENT_ID / EBAY_CLIENT_SECRET.",
      setFallback: "Set",
      editionJp: "JP",
      editionKr: "KR",
      editionEn: "EN",
      uiKo: "KR",
      uiEn: "EN",
      uiJa: "JP",
      searchPlaceholder: "Search Pokémon name",
      searchEmpty: "No results.",
      searchPack: "Pack",
      searchTitle: "Search results",
      searchClear: "Clear search",
      searchCount: "{n} cards",
      packsSectionTitle: "Packs",
      packNoCardsYet: "Card list pending (set not in JP data source yet)",
      ebayPriceLink: "Search on eBay →",
      psaSetPopLink: "PSA set POP →",
      psaSetPopSearch: "Search set on PSA →",
      emptyPackCards:
        "No card data for this pack yet. It will appear once the set is in the JP card database.",
    },
    ja: {
      siteTagline: "パックを選んでグレーディングPOPとeBay相場をまとめて確認できます。",
      open: "OPEN →",
      backPacks: "← パック一覧",
      sort: "並び替え",
      type: "タイプ",
      language: "言語",
      all: "すべて",
      sortNumber: "番号順",
      sortPriceDesc: "価格が高い順",
      sortPriceAsc: "価格が安い順",
      sortType: "タイプ順",
      sortRarity: "レアリティ順",
      sortName: "名前順",
      emptyPack: "パックが見つかりません。",
      emptyCards: "条件に合うカードがありません。",
      emptyData: "データを読み込めませんでした。再読み込みしてください。",
      emptyCard: "カードが見つかりません。",
      priceLabel: "eBay相場 (PSA)",
      pricePendingEbay: "eBay相場待ち（シード価格は非表示）",
      popTitle: "POP REPORT",
      popGrader: "グレーディング",
      popTotalRow: "全社合計",
      popEmpty: "POPデータなし",
      notCollected: "まだ収集されていません。",
      noData: "データなし",
      imageFallback: "この言語のカード画像がないため、別バージョンを表示しています。",
      updatedPrefix: "データ更新:",
      snapshotPrefix: "POP/価格スナップショット:",
      footnote:
        "BRGはbreak.co.krの実POP（列: 10=BRG100 · 9.5=BRG90 · 9=BRG85 · 8=BRG80）。PSA・BGS・CGCは未連携。価格はeBay API設定後のみ表示されます。",
      credit:
        "Holo effect adapted from simeydotme/pokemon-cards-css (GPL-3.0). Card images via Pokémon card sources. BRG POPは毎時自動更新。eBay相場はGitHub Secrets（EBAY_CLIENT_ID/SECRET）登録後に収集されます。",
      setFallback: "セット",
      editionJp: "JP",
      editionKr: "KR",
      editionEn: "EN",
      uiKo: "KR",
      uiEn: "EN",
      uiJa: "JP",
      searchPlaceholder: "ポケモン名で検索",
      searchEmpty: "結果がありません。",
      searchPack: "パック",
      searchTitle: "検索結果",
      searchClear: "検索を閉じる",
      searchCount: "{n}枚",
      packsSectionTitle: "パック一覧",
      packNoCardsYet: "カード一覧準備中（JPデータソース未登録）",
      ebayPriceLink: "eBayで検索 →",
      psaSetPopLink: "PSAセットPOP →",
      psaSetPopSearch: "PSAでセット検索 →",
      emptyPackCards:
        "このパックのカードデータはまだありません。JPカードDBにセットが追加されると反映されます。",
    },
  };

  const TYPE_LABELS = {
    ko: {
      grass: "풀",
      fire: "불",
      water: "물",
      lightning: "번개",
      psychic: "초",
      fighting: "격투",
      darkness: "악",
      metal: "강철",
      fairy: "페어리",
      dragon: "드래곤",
      colorless: "무색",
      trainer: "트레이너",
    },
    en: {
      grass: "Grass",
      fire: "Fire",
      water: "Water",
      lightning: "Lightning",
      psychic: "Psychic",
      fighting: "Fighting",
      darkness: "Darkness",
      metal: "Metal",
      fairy: "Fairy",
      dragon: "Dragon",
      colorless: "Colorless",
      trainer: "Trainer",
    },
    ja: {
      grass: "草",
      fire: "炎",
      water: "水",
      lightning: "雷",
      psychic: "超",
      fighting: "闘",
      darkness: "悪",
      metal: "鋼",
      fairy: "フェアリー",
      dragon: "ドラゴン",
      colorless: "無色",
      trainer: "トレーナー",
    },
  };

  PT.getUiLang = function () {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (PT.UI_LANGS.indexOf(saved) !== -1) return saved;
    return "ko";
  };

  PT.setUiLang = function (lang) {
    if (PT.UI_LANGS.indexOf(lang) === -1) lang = "ko";
    localStorage.setItem(STORAGE_KEY, lang);
    document.documentElement.lang = lang === "ja" ? "ja" : lang;
    return lang;
  };

  PT.t = function (key) {
    const lang = PT.getUiLang();
    return (STR[lang] && STR[lang][key]) || STR.ko[key] || key;
  };

  PT.typeLabel = function (type) {
    const lang = PT.getUiLang();
    return (TYPE_LABELS[lang] && TYPE_LABELS[lang][type]) || type || "";
  };

  PT.packName = function (pack) {
    if (!pack) return "";
    const lang = PT.getUiLang();
    if (lang === "en") return pack.nameEn || pack.nameKo || pack.nameJa || "";
    if (lang === "ja") return pack.nameJa || pack.nameKo || pack.nameEn || "";
    return pack.nameKo || pack.nameEn || pack.nameJa || "";
  };

  PT.packBlurb = function (pack) {
    if (!pack) return "";
    const lang = PT.getUiLang();
    if (lang === "en") return pack.blurbEn || pack.blurb || "";
    if (lang === "ja") return pack.blurbJa || pack.blurb || "";
    return pack.blurb || pack.blurbEn || "";
  };

  PT.cardName = function (card) {
    if (!card) return "";
    const lang = PT.getUiLang();
    if (lang === "en") return card.nameEn || card.nameKo || card.nameJa || "";
    if (lang === "ja") return card.nameJa || card.nameKo || card.nameEn || "";
    return card.nameKo || card.nameEn || card.nameJa || "";
  };

  /** Edition language (jp/kr/en) → localized label */
  PT.editionLabel = function (edition) {
    if (edition === "jp") return PT.t("editionJp");
    if (edition === "kr") return PT.t("editionKr");
    if (edition === "en") return PT.t("editionEn");
    return String(edition || "").toUpperCase();
  };

  PT.cardImageForEdition = function (card, edition) {
    if (!card) return "";
    const images = card.images || {};
    if (edition && images[edition]) return images[edition];
    // Honest fallback: prefer matching edition, then jp, then any available
    const order =
      edition === "en"
        ? ["en", "jp", "kr"]
        : edition === "kr"
          ? ["kr", "jp", "en"]
          : ["jp", "en", "kr"];
    for (let i = 0; i < order.length; i++) {
      if (images[order[i]]) return images[order[i]];
    }
    return card.image || "";
  };

  PT.hasEditionImage = function (card, edition) {
    return !!(card && card.images && card.images[edition]);
  };

  PT.mountLangSwitcher = function (nav) {
    if (!nav) return;
    const hostParent = nav.querySelector(".nav-actions") || nav;
    let host = nav.querySelector(".nav-lang");
    if (!host) {
      host = document.createElement("div");
      host.className = "nav-lang";
      host.setAttribute("role", "group");
      host.setAttribute("aria-label", "Language");
      hostParent.appendChild(host);
    }
    const active = PT.getUiLang();
    host.innerHTML = [
      { id: "ko", label: PT.t("uiKo") },
      { id: "en", label: PT.t("uiEn") },
      { id: "ja", label: PT.t("uiJa") },
    ]
      .map(
        (item) =>
          `<button type="button" class="nav-lang__btn${item.id === active ? " is-active" : ""}" data-ui-lang="${item.id}">${item.label}</button>`
      )
      .join("");
    host.onclick = function (e) {
      const btn = e.target.closest("[data-ui-lang]");
      if (!btn) return;
      PT.setUiLang(btn.dataset.uiLang);
      window.location.reload();
    };
  };

  // Apply saved lang on load
  PT.setUiLang(PT.getUiLang());
  PT.ebaySearchUrl = function (card, pack, lang) {
    const parts = [
      card && (card.nameEn || card.nameJa || card.nameKo),
      card && String(card.number || "").split("/")[0],
      pack && (pack.nameShort || pack.code),
      "Pokemon",
      "PSA",
      lang === "jp" ? "Japanese" : lang === "kr" ? "Korean" : lang === "en" ? "English" : "",
    ].filter(Boolean);
    const q = parts.join(" ");
    return `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(q)}&_sacat=183454`;
  };

  PT.getPsaSets = function () {
    return window.POP_PSA_SETS || {};
  };

  /** Exact PSA set POP URL if mapped; otherwise a PSA search URL for that set. */
  PT.psaSetPopLink = function (pack, lang) {
    if (!pack) return null;
    const row = PT.getPsaSets()[pack.id] || {};
    const exact =
      row[lang] ||
      (lang !== "jp" && row.jp) ||
      (lang !== "en" && row.en) ||
      null;
    if (exact) {
      return { href: exact, exact: true };
    }
    const year = pack.releaseYear || "";
    const code = String(pack.code || "").toUpperCase();
    const langWord =
      lang === "jp" ? "Japanese" : lang === "kr" ? "Korean" : lang === "en" ? "" : "";
    const q = [year, "Pokemon", langWord, code, pack.nameEn || pack.nameShort || ""]
      .filter(Boolean)
      .join(" ");
    return {
      href: `https://www.psacard.com/pop/search?search=${encodeURIComponent(q)}`,
      exact: false,
    };
  };
})(window.PopTracker);
