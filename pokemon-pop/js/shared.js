/** Shared helpers for Pokemon POP Tracker */
window.PopTracker = window.PopTracker || {};

(function (PT) {
  PT.GRADERS = ["BRG", "PSA", "BGS", "CGC", "TAG", "ACE", "AGS"];
  PT.GRADE_COLS = ["10", "9", "8", "le7"];
  PT.PRICE_GRADES = ["10", "9", "8"];
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
      return `${PT.t("updatedPrefix")} ${PT.formatUpdatedDisplay(ts)}`;
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
    return PT.editionLabel ? PT.editionLabel(lang) : String(lang || "").toUpperCase();
  };

  PT.langTabLabel = function (lang) {
    return PT.langLabel(lang);
  };

  PT.priceAmountForGrade = function (price, grade) {
    if (!price || price.source === "seed") return null;
    if (price.grades && price.grades[grade] != null) return Number(price.grades[grade]);
    if (grade === "10" && price.amount != null) return Number(price.amount);
    return null;
  };

  PT.priceRangeForGrade = function (price, grade) {
    if (!price || price.source === "seed") return null;
    const avg = PT.priceAmountForGrade(price, grade);
    if (avg == null) return null;
    const r = (price.range && price.range[grade]) || null;
    const min = r && r.min != null ? Number(r.min) : avg;
    const max = r && r.max != null ? Number(r.max) : avg;
    const samples = (price.sampleSize && price.sampleSize[grade]) || 0;
    return { min: min, max: max, avg: avg, samples: samples };
  };

  PT.isLivePrice = function (price) {
    if (!price || price.source === "seed") return false;
    return PT.PRICE_GRADES.some(function (g) {
      return PT.priceAmountForGrade(price, g) != null;
    });
  };

  PT.priceAmountForLang = function (card, lang) {
    return PT.priceAmountForGrade(card.variants?.[lang]?.price, "10");
  };

  PT.bestPriceAmount = function (card, preferredLang) {
    if (preferredLang) {
      const n = PT.priceAmountForLang(card, preferredLang);
      if (n != null) return n;
    }
    const amounts = PT.LANG_ORDER.map((lang) => PT.priceAmountForLang(card, lang)).filter(
      (n) => n != null
    );
    if (!amounts.length) return 0;
    return Math.max.apply(null, amounts);
  };

  PT.tierLabel = function (tier) {
    if (tier === "A") return "Tier A";
    if (tier === "B") return "Tier B";
    if (tier === "C") return "Tier C";
    return tier || "";
  };

  PT.formatMoney = function (amount, currency) {
    if (amount == null) return "—";
    const n = Number(amount);
    if (currency === "USD" || !currency) return `$${n.toLocaleString("en-US")}`;
    if (currency === "KRW") return `₩${n.toLocaleString("ko-KR")}`;
    return `${n.toLocaleString()} ${currency}`;
  };

  PT.formatPrice = function (price) {
    if (!PT.isLivePrice(price)) return "—";
    return PT.formatMoney(PT.priceAmountForGrade(price, "10"), price?.currency);
  };

  PT.typeBadgeClass = function (type) {
    return `badge badge--${type || "default"}`;
  };

  PT.qs = function (name) {
    return new URLSearchParams(window.location.search).get(name);
  };
})(window.PopTracker);
