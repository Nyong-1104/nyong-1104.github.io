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

  PT.getSiteUpdatedAt = function () {
    const live = PT.getLive();
    const lastRun = window.POP_LAST_RUN || {};
    return live.generatedAt || lastRun.ranAt || null;
  };

  PT.parseSnapshotTime = function (value) {
    if (!value) return null;
    const str = String(value);
    if (/^\d{4}-\d{2}-\d{2}$/.test(str)) {
      return new Date(str + "T00:00:00+09:00");
    }
    const d = new Date(str);
    return isNaN(d.getTime()) ? null : d;
  };

  PT.formatTimeAgo = function (value) {
    const then = PT.parseSnapshotTime(value);
    if (!then) return "—";
    const sec = Math.round((then.getTime() - Date.now()) / 1000);
    const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
    const abs = Math.abs(sec);
    if (abs < 45) return rtf.format(sec, "second");
    const min = Math.round(sec / 60);
    if (Math.abs(min) < 60) return rtf.format(min, "minute");
    const hr = Math.round(sec / 3600);
    if (Math.abs(hr) < 24) return rtf.format(hr, "hour");
    const day = Math.round(sec / 86400);
    if (Math.abs(day) < 30) return rtf.format(day, "day");
    const month = Math.round(sec / (86400 * 30));
    if (Math.abs(month) < 12) return rtf.format(month, "month");
    return rtf.format(Math.round(sec / (86400 * 365)), "year");
  };

  PT.formatLocalDateTime = function (value) {
    const d = PT.parseSnapshotTime(value);
    if (!d) return "";
    return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  };

  /** Relative + viewer-local absolute time, e.g. "3 hours ago · Jul 21, 2026, 4:25 PM" */
  PT.formatUpdatedDisplay = function (value) {
    const ago = PT.formatTimeAgo(value);
    const local = PT.formatLocalDateTime(value);
    if (!local || ago === "—") return ago;
    return `${ago} · ${local}`;
  };

  PT.bindRelativeTime = function (el, getText) {
    if (!el) return function () {};
    function paint() {
      el.textContent = typeof getText === "function" ? getText() : getText;
    }
    paint();
    window.setInterval(paint, 60000);
    return paint;
  };

  PT.mountSiteUpdated = function (el) {
    if (!el) return;
    const ts = PT.getSiteUpdatedAt();
    if (!ts) {
      el.textContent = "";
      el.hidden = true;
      return;
    }
    el.hidden = false;
    PT.bindRelativeTime(el, function () {
      return `데이터 갱신: ${PT.formatUpdatedDisplay(ts)}`;
    });
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
