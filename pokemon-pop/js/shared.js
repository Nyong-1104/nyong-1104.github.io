/** Shared helpers for Pokemon POP Tracker */
window.PopTracker = window.PopTracker || {};

(function (PT) {
  PT.GRADERS = ["PSA", "BGS", "CGC", "BRG", "TAG", "ACE", "AGS"];
  PT.GRADE_COLS = ["10", "9.5", "9", "8", "total"];

  PT.getPacks = function () {
    return window.POP_PACKS || [];
  };

  PT.getCards = function () {
    return window.POP_CARDS || [];
  };

  PT.langLabel = function (lang) {
    return lang === "kr" ? "한판" : lang === "jp" ? "일판" : String(lang || "").toUpperCase();
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
