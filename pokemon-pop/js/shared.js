/** Shared helpers for Pokemon POP Tracker */
window.PopTracker = window.PopTracker || {};

(function (PT) {
  PT.GRADERS = ["PSA", "BGS", "CGC", "BRG", "TAG", "ACE", "AGS"];
  PT.GRADE_COLS = ["10", "9.5", "9", "8", "total"];
  PT.LANG_ORDER = ["jp", "kr", "en"];

  PT.getPacks = function () {
    return window.POP_PACKS || [];
  };

  PT.getCatalog = function () {
    return window.POP_CATALOG || window.POP_CARDS || [];
  };

  PT.getLive = function () {
    return window.POP_LIVE || { generatedAt: null, cards: {} };
  };

  PT.mergeCard = function (catalogCard) {
    const liveEntry = PT.getLive().cards?.[catalogCard.id] || {};
    const variants = {};
    PT.LANG_ORDER.forEach((lang) => {
      if (liveEntry[lang]) variants[lang] = liveEntry[lang];
    });
    return Object.assign({}, catalogCard, { variants: variants });
  };

  PT.getCards = function () {
    return PT.getCatalog().map(PT.mergeCard);
  };

  PT.langLabel = function (lang) {
    if (lang === "kr") return "한글판";
    if (lang === "jp") return "일본판";
    if (lang === "en") return "영문판";
    return String(lang || "").toUpperCase();
  };

  PT.langTabLabel = function (lang) {
    return PT.langLabel(lang).replace("판", "");
  };

  PT.tierLabel = function (tier) {
    if (tier === "A") return "Tier A · POP+가격";
    if (tier === "B") return "Tier B · 가격";
    if (tier === "C") return "Tier C · 카탈로그만";
    return tier || "";
  };

  PT.bestPriceAmount = function (card) {
    const amounts = PT.LANG_ORDER.map((lang) => card.variants?.[lang]?.price?.amount).filter(
      (n) => n != null
    );
    if (!amounts.length) return 0;
    return Math.max.apply(null, amounts);
  };

  PT.formatPrice = function (price) {
    if (!price || price.amount == null) return "—";
    const n = Number(price.amount);
    if (price.currency === "USD") return `$${n.toLocaleString("en-US")}`;
    if (price.currency === "KRW") return `₩${n.toLocaleString("ko-KR")}`;
    return `${n.toLocaleString()} ${price.currency}`;
  };

  PT.typeBadgeClass = function (type) {
    return `badge badge--${type || "default"}`;
  };

  PT.qs = function (name) {
    return new URLSearchParams(window.location.search).get(name);
  };
})(window.PopTracker);
