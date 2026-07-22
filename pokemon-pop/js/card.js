(function () {
  const PT = window.PopTracker;

  function popCell(graderData, grade) {
    if (!graderData) return `<td class="pop-empty">—</td>`;
    const v = gradeValue(graderData, grade);
    if (v == null) return `<td class="pop-empty">—</td>`;
    return `<td>${Number(v).toLocaleString("en-US")}</td>`;
  }

  function sumPopColumn(pop, grade) {
    let sum = 0;
    let any = false;
    PT.GRADERS.forEach((g) => {
      const data = pop?.[g];
      if (!data) return;
      const v = gradeValue(data, grade);
      if (v == null) return;
      sum += Number(v) || 0;
      any = true;
    });
    return any ? sum : null;
  }

  function gradeHeader(col) {
    if (col === "le7") return "≤7";
    // BRG has no 9.5: 100→10, 90(+85)→9, 80→8
    const brg = { "10": "100", "9": "90", "8": "80" }[col];
    return brg ? `${col}<span class="pop-brg-hint">/${brg}</span>` : col;
  }

  function gradeValue(graderData, grade) {
    if (!graderData) return null;

    const scores = graderData.brgScores;
    if (scores && typeof scores === "object" && graderData.source === "break") {
      const num = (k) => {
        const c = Number(scores[k]);
        return Number.isFinite(c) ? c : 0;
      };
      if (grade === "10") return scores["100"] != null ? num("100") : null;
      if (grade === "9") {
        if (scores["90"] == null && scores["85"] == null) return null;
        return num("90") + num("85");
      }
      if (grade === "8") return scores["80"] != null ? num("80") : null;
      if (grade === "le7") {
        let sum = 0;
        let any = false;
        Object.keys(scores).forEach((k) => {
          if (k === "-1" || k === "100" || k === "90" || k === "85" || k === "80") return;
          const c = Number(scores[k]);
          if (!Number.isFinite(c)) return;
          sum += c;
          any = true;
        });
        return any ? sum : graderData.le7 ?? 0;
      }
    }

    if (grade === "9") {
      // Legacy BRG dumps mapped 90 → 9.5; fold into 9 for display.
      const v9 = graderData["9"];
      const v95 = graderData["9.5"];
      if (v9 == null && v95 == null) return null;
      return (Number(v9) || 0) + (Number(v95) || 0);
    }

    if (grade === "le7" && graderData.le7 == null) {
      if (graderData.total != null) {
        const high = ["10", "9", "8"]
          .map((g) => gradeValue(graderData, g))
          .filter((v) => v != null)
          .reduce((a, b) => a + Number(b), 0);
        return Math.max(0, Number(graderData.total) - high);
      }
      return null;
    }

    return graderData[grade] ?? null;
  }

  function graderHasData(graderData) {
    if (!graderData || typeof graderData !== "object") return false;
    return PT.GRADE_COLS.some((col) => gradeValue(graderData, col) != null);
  }

  function renderPop(variant) {
    const thead = document.querySelector("#pop-table thead tr");
    thead.innerHTML =
      `<th>${PT.t("popGrader")}</th>` +
      PT.GRADE_COLS.map((g) => `<th>${gradeHeader(g)}</th>`).join("");

    const tbody = document.querySelector("#pop-table tbody");
    const pop = variant?.pop;
    if (!pop) {
      tbody.innerHTML = `<tr><td colspan="${PT.GRADE_COLS.length + 1}" class="pop-empty pop-empty--message">${PT.t("popEmpty")}</td></tr>`;
      return;
    }

    const activeGraders = PT.GRADERS.filter((g) => graderHasData(pop[g]));
    if (!activeGraders.length) {
      tbody.innerHTML = `<tr><td colspan="${PT.GRADE_COLS.length + 1}" class="pop-empty pop-empty--message">${PT.t("popEmptyBrg")}</td></tr>`;
      return;
    }

    const rows = activeGraders.map((g) => {
      const data = pop[g] ?? null;
      const live = data && (data.source === "break" || data.source === "gemrate");
      return `<tr${live ? ' class="pop-live-row"' : ""}>
        <td>${g}${live ? ' <span class="pop-live-tag">live</span>' : ""}</td>
        ${PT.GRADE_COLS.map((col) => popCell(data, col)).join("")}
      </tr>`;
    });

    if (activeGraders.length > 1) {
      const totals = PT.GRADE_COLS.map((col) => {
        const v = sumPopColumn(pop, col);
        if (v == null) return `<td class="pop-empty">—</td>`;
        return `<td>${v.toLocaleString("en-US")}</td>`;
      });
      rows.push(
        `<tr class="pop-total-row"><td>${PT.t("popTotalRow")}</td>${totals.join("")}</tr>`
      );
    }

    tbody.innerHTML = rows.join("");
  }

  function renderPrice(variant, lang) {
    const gradesEl = document.getElementById("price-grades");
    const metaEl = document.getElementById("price-meta");
    const emptyGrades = PT.PRICE_GRADES.map(
      (g) =>
        `<div class="price-grade"><span class="price-grade__label">PSA ${g}</span><span class="price-grade__value">—</span></div>`
    ).join("");

    if (!variant?.price || !PT.isLivePrice(variant.price)) {
      gradesEl.innerHTML = emptyGrades;
      const why =
        variant?.price?.source === "seed" || !variant?.price
          ? PT.t("pricePendingEbay")
          : PT.t("noData");
      metaEl.textContent = `${PT.langLabel(lang)} · ${why}`;
      return;
    }

    const price = variant.price;
    const currency = price.currency || "USD";
    gradesEl.innerHTML = PT.PRICE_GRADES.map((g) => {
      const amount = PT.priceAmountForGrade(price, g);
      return `<div class="price-grade">
        <span class="price-grade__label">PSA ${g}</span>
        <span class="price-grade__value">${PT.formatMoney(amount, currency)}</span>
      </div>`;
    }).join("");

    const priceWhen = price.asOf || variant.updatedAt;
    metaEl.textContent = `eBay · ${PT.langLabel(lang)} · ${PT.formatUpdatedDisplay(priceWhen)}`;
  }

  function renderEmptyState(lang) {
    renderPrice(null, lang);
    const tbody = document.querySelector("#pop-table tbody");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="${PT.GRADE_COLS.length + 1}" class="pop-empty pop-empty--message">${PT.t("notCollected")}</td></tr>`;
    }
  }

  PT.mountLangSwitcher(document.querySelector(".site-nav"));

  const id = PT.qs("id");
  const packs = PT.getPacks();
  const cards = PT.getCards();
  const card = cards.find((c) => c.id === id) || cards[0];

  if (!card) {
    document.getElementById("detail").innerHTML =
      `<p class="empty-state">${PT.t("emptyCard")}</p>`;
    return;
  }

  const pack = packs.find((p) => p.id === card.packId);
  const displayName = PT.cardName(card);
  document.title = `${displayName} · PokePop`;

  const back = document.getElementById("nav-back");
  if (back && pack) {
    const packLabel = PT.packName(pack);
    back.href = `./set.html?pack=${encodeURIComponent(pack.id)}`;
    back.textContent = `← ${packLabel}`;
    back.title = packLabel;
  }

  const priceLabel = document.querySelector(".price-panel__label");
  if (priceLabel) priceLabel.textContent = PT.t("priceLabel");
  const ebayLinkEl = document.getElementById("price-ebay-link");
  function paintEbayLink(lang) {
    if (!ebayLinkEl) return;
    const href = PT.ebaySearchUrl(card, pack, lang);
    ebayLinkEl.innerHTML = `<a href="${href}" target="_blank" rel="noopener noreferrer">${PT.t(
      "ebayPriceLink"
    )}</a>`;
  }
  const popTitle = document.querySelector(".section-title");
  if (popTitle) popTitle.textContent = PT.t("popTitle");
  const footnote = document.querySelectorAll(".footnote")[1];
  if (footnote) footnote.textContent = PT.t("footnote");

  const visual = document.getElementById("detail-visual");
  const packLangs = pack?.languages?.length ? pack.languages : ["jp", "kr"];
  const cardEditions = Array.isArray(card.editions) && card.editions.length
    ? card.editions
    : packLangs;
  const tabLangs = packLangs.filter((lang) => cardEditions.indexOf(lang) !== -1);
  const editionLangs = tabLangs.length ? tabLangs : cardEditions;
  // Card detail defaults to Japanese when available for this card
  let activeLang =
    editionLangs.indexOf("jp") !== -1 ? "jp" : editionLangs[0] || packLangs[0];
  paintEbayLink(activeLang);

  const holo = PT.createHoloCardEl({
    image: PT.cardImageForEdition(card, activeLang),
    name: displayName,
    holoStyle: card.holoStyle,
  });
  visual.appendChild(holo);
  PT.mountHoloCard(holo);

  document.getElementById("card-name").textContent = displayName;
  const subEl = document.getElementById("card-sub");
  subEl.innerHTML = `
    <span></span>
    <span></span>
    <span class="${PT.typeBadgeClass(card.type)}"></span>
    <span class="badge"></span>
  `;
  const subSpans = subEl.querySelectorAll(":scope > span");
  subSpans[0].textContent = card.nameEn || "";
  subSpans[1].textContent = card.number;
  subSpans[2].textContent = PT.typeLabel(card.type);
  subSpans[3].textContent = card.rarity;
  if (pack) {
    const packLink = document.createElement("a");
    packLink.className = "badge badge--pack";
    packLink.href = `./set.html?pack=${encodeURIComponent(pack.id)}`;
    packLink.title = PT.packName(pack);
    packLink.textContent = PT.packName(pack);
    subEl.appendChild(packLink);
  }

  const tabs = document.getElementById("lang-tabs");

  function getUpdatedText() {
    const variant = card.variants?.[activeLang];
    if (!variant) return `${PT.langLabel(activeLang)} · ${PT.t("notCollected")}`;
    const ts = variant.updatedAt || PT.getSiteUpdatedAt();
    return `${PT.t("snapshotPrefix")} ${PT.formatUpdatedDisplay(ts)} (${PT.langLabel(activeLang)})`;
  }

  const repaintUpdated = PT.bindRelativeTime(document.getElementById("updated"), getUpdatedText);

  function renderVariant(lang) {
    activeLang = lang;
    paintEbayLink(lang);
    document.querySelectorAll(".lang-tab").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.lang === lang);
    });

    PT.setHoloCardImage(holo, PT.cardImageForEdition(card, lang), displayName);

    const imageNote = document.getElementById("image-lang-note");
    if (imageNote) {
      if (PT.hasEditionImage(card, lang)) {
        imageNote.hidden = true;
        imageNote.textContent = "";
      } else {
        imageNote.hidden = false;
        imageNote.textContent = PT.t("imageFallback");
      }
    }

    const variant = card.variants?.[lang];
    if (!variant) {
      renderEmptyState(lang);
      repaintUpdated();
      return;
    }

    renderPrice(variant, lang);
    renderPop(variant);
    repaintUpdated();
  }

  if (tabs) {
    tabs.innerHTML = editionLangs
      .map(
        (lang) =>
          `<button type="button" class="lang-tab${lang === activeLang ? " is-active" : ""}" data-lang="${lang}" role="tab">${PT.langTabLabel(lang)}</button>`
      )
      .join("");
    tabs.addEventListener("click", (e) => {
      const btn = e.target.closest(".lang-tab");
      if (!btn) return;
      renderVariant(btn.dataset.lang);
    });
  }

  renderVariant(activeLang);
})();
