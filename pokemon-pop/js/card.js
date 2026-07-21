(function () {
  const PT = window.PopTracker;

  function popCell(graderData, grade) {
    if (!graderData) return `<td class="pop-empty">—</td>`;
    const v = graderData[grade];
    if (v == null) return `<td class="pop-empty">—</td>`;
    return `<td>${Number(v).toLocaleString("en-US")}</td>`;
  }

  function sumPopColumn(pop, grade) {
    let sum = 0;
    let any = false;
    PT.GRADERS.forEach((g) => {
      const data = pop?.[g];
      if (!data || data[grade] == null) return;
      sum += Number(data[grade]) || 0;
      any = true;
    });
    return any ? sum : null;
  }

  function gradeHeader(col) {
    if (col === "total") return "Total";
    const brg = { "10": "100", "9.5": "90", "9": "85", "8": "80" }[col];
    return brg ? `${col}<span class="pop-brg-hint">/${brg}</span>` : col;
  }

  function renderPop(variant) {
    const thead = document.querySelector("#pop-table thead tr");
    thead.innerHTML =
      `<th>${PT.t("popGrader")}</th>` +
      PT.GRADE_COLS.map((g) => `<th>${gradeHeader(g)}</th>`).join("");

    const tbody = document.querySelector("#pop-table tbody");
    if (!variant?.pop) {
      tbody.innerHTML = `<tr><td colspan="${PT.GRADE_COLS.length + 1}" class="pop-empty pop-empty--message">${PT.t("popEmpty")}</td></tr>`;
      return;
    }

    const rows = PT.GRADERS.map((g) => {
      const data = variant.pop[g] ?? null;
      const live = data && data.source === "break";
      return `<tr${live ? ' class="pop-live-row"' : ""}>
        <td>${g}${live ? ' <span class="pop-live-tag">live</span>' : ""}</td>
        ${PT.GRADE_COLS.map((col) => popCell(data, col)).join("")}
      </tr>`;
    });

    const totals = PT.GRADE_COLS.map((col) => {
      const v = sumPopColumn(variant.pop, col);
      if (v == null) return `<td class="pop-empty">—</td>`;
      return `<td>${v.toLocaleString("en-US")}</td>`;
    });
    rows.push(
      `<tr class="pop-total-row"><td>${PT.t("popTotalRow")}</td>${totals.join("")}</tr>`
    );

    tbody.innerHTML = rows.join("");
  }

  function renderPrice(variant, lang) {
    const gradesEl = document.getElementById("price-grades");
    const metaEl = document.getElementById("price-meta");
    if (!variant?.price) {
      gradesEl.innerHTML = PT.PRICE_GRADES.map(
        (g) =>
          `<div class="price-grade"><span class="price-grade__label">PSA ${g}</span><span class="price-grade__value">—</span></div>`
      ).join("");
      metaEl.textContent = `${PT.langLabel(lang)} · ${PT.t("noData")}`;
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
    const source = price.source === "eBay" ? "eBay" : price.source === "seed" ? "seed" : price.source || "—";
    metaEl.textContent = `${source} · ${PT.langLabel(lang)} · ${PT.formatUpdatedDisplay(priceWhen)}`;
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
    back.href = `./set.html?pack=${encodeURIComponent(pack.id)}`;
    back.textContent = `← ${PT.packName(pack)}`;
  }

  const priceLabel = document.querySelector(".price-panel__label");
  if (priceLabel) priceLabel.textContent = PT.t("priceLabel");
  const ebayLinkEl = document.getElementById("price-ebay-link");
  const psaLinkEl = document.getElementById("psa-set-pop-link");
  function paintEbayLink(lang) {
    if (!ebayLinkEl) return;
    const href = PT.ebaySearchUrl(card, pack, lang);
    ebayLinkEl.innerHTML = `<a href="${href}" target="_blank" rel="noopener noreferrer">${PT.t(
      "ebayPriceLink"
    )}</a>`;
  }
  function paintPsaSetLink(lang) {
    if (!psaLinkEl) return;
    const link = PT.psaSetPopLink(pack, lang);
    if (!link) {
      psaLinkEl.innerHTML = "";
      return;
    }
    const label = link.exact ? PT.t("psaSetPopLink") : PT.t("psaSetPopSearch");
    psaLinkEl.innerHTML = `<a href="${link.href}" target="_blank" rel="noopener noreferrer">${label}</a>`;
  }
  const popTitle = document.querySelector(".section-title");
  if (popTitle) popTitle.textContent = PT.t("popTitle");
  const footnote = document.querySelectorAll(".footnote")[1];
  if (footnote) footnote.textContent = PT.t("footnote");

  const visual = document.getElementById("detail-visual");
  const packLangs = pack?.languages?.length ? pack.languages : ["jp", "kr"];
  // Card detail defaults to Japanese edition
  let activeLang = packLangs.indexOf("jp") !== -1 ? "jp" : packLangs[0];
  paintEbayLink(activeLang);
  paintPsaSetLink(activeLang);

  const holo = PT.createHoloCardEl({
    image: PT.cardImageForEdition(card, activeLang),
    name: displayName,
    holoStyle: card.holoStyle,
  });
  visual.appendChild(holo);
  PT.mountHoloCard(holo);

  document.getElementById("card-name").textContent = displayName;
  document.getElementById("card-sub").innerHTML = `
    <span>${card.nameEn || ""}</span>
    <span>${card.number}</span>
    <span class="${PT.typeBadgeClass(card.type)}">${PT.typeLabel(card.type)}</span>
    <span class="badge">${card.rarity}</span>
    ${pack ? `<a class="badge" href="./set.html?pack=${pack.id}">${PT.packName(pack)}</a>` : ""}
  `;

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
    paintPsaSetLink(lang);
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
    tabs.innerHTML = packLangs
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
