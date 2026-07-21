(function () {
  const PT = window.PopTracker;
  const RARITY_RANK = { SAR: 5, SIR: 5, HR: 5, UR: 4, SR: 4, RRR: 4, RR: 4, PRISM: 3, R: 3, AR: 3, U: 2, C: 1 };

  function sortCards(list, mode, editionLang) {
    const arr = list.slice();
    switch (mode) {
      case "price-desc":
        return arr.sort(
          (a, b) => PT.bestPriceAmount(b, editionLang) - PT.bestPriceAmount(a, editionLang)
        );
      case "price-asc":
        return arr.sort(
          (a, b) => PT.bestPriceAmount(a, editionLang) - PT.bestPriceAmount(b, editionLang)
        );
      case "type":
        return arr.sort((a, b) =>
          PT.typeLabel(a.type).localeCompare(PT.typeLabel(b.type), PT.getUiLang())
        );
      case "rarity":
        return arr.sort(
          (a, b) => (RARITY_RANK[b.rarity] || 0) - (RARITY_RANK[a.rarity] || 0)
        );
      case "name":
        return arr.sort((a, b) =>
          PT.cardName(a).localeCompare(PT.cardName(b), PT.getUiLang())
        );
      case "number":
        return arr.sort((a, b) => {
          const na = parseInt(String(a.number || "").split("/")[0], 10) || 0;
          const nb = parseInt(String(b.number || "").split("/")[0], 10) || 0;
          return na - nb;
        });
      default:
        return arr;
    }
  }

  function filterCards(list, type) {
    return list.filter((c) => {
      if (type && type !== "all" && c.type !== type) return false;
      return true;
    });
  }

  function listPriceLabel(card, editionLang) {
    const amount = PT.bestPriceAmount(card, editionLang);
    if (amount > 0) return PT.formatMoney(amount, "USD");
    return "—";
  }

  PT.mountLangSwitcher(document.querySelector(".site-nav"));

  const packId = PT.qs("pack");
  const packs = PT.getPacks();
  const cards = PT.getCards();
  const grid = document.getElementById("card-grid");

  if (!grid) return;

  const pack = packs.find((p) => p.id === packId) || packs[0];
  if (!pack) {
    grid.innerHTML = `<p class="empty-state">${PT.t("emptyPack")}</p>`;
    return;
  }

  document.title = `${PT.packName(pack)} · PokePop`;
  document.getElementById("set-title").textContent = PT.packName(pack);
  document.getElementById("set-blurb").textContent = PT.packBlurb(pack);

  const psaEl = document.getElementById("set-psa-link");
  if (psaEl) {
    const preferred =
      (pack.languages || []).indexOf("jp") !== -1
        ? "jp"
        : (pack.languages || [])[0] || "jp";
    const link = PT.psaSetPopLink(pack, preferred);
    if (link) {
      const label = link.exact ? PT.t("psaSetPopLink") : PT.t("psaSetPopSearch");
      psaEl.innerHTML = `<a href="${link.href}" target="_blank" rel="noopener noreferrer">${label}</a>`;
    }
  }

  const back = document.querySelector(".nav-back");
  if (back) back.textContent = PT.t("backPacks");

  const packCards = cards.filter((c) => c.packId === pack.id);
  if (!packCards.length) {
    grid.innerHTML = `<p class="empty-state">${PT.t("emptyPackCards")}</p>`;
    document.getElementById("set-blurb").textContent =
      PT.packBlurb(pack) || PT.t("emptyPackCards");
    PT.mountSiteUpdated(document.getElementById("site-updated"));
    return;
  }

  const typeSelect = document.getElementById("filter-type");
  const langSelect = document.getElementById("filter-lang");
  const sortSelect = document.getElementById("sort-by");

  document.querySelector('label[for="sort-by"]').textContent = PT.t("sort");
  document.querySelector('label[for="filter-type"]').textContent = PT.t("type");
  document.querySelector('label[for="filter-lang"]').textContent = PT.t("language");

  sortSelect.options[0].textContent = PT.t("sortNumber");
  sortSelect.options[1].textContent = PT.t("sortPriceDesc");
  sortSelect.options[2].textContent = PT.t("sortPriceAsc");
  sortSelect.options[3].textContent = PT.t("sortType");
  sortSelect.options[4].textContent = PT.t("sortRarity");
  sortSelect.options[5].textContent = PT.t("sortName");

  typeSelect.innerHTML = `<option value="all">${PT.t("all")}</option>`;
  const types = [];
  packCards.forEach((c) => {
    if (types.indexOf(c.type) === -1) types.push(c.type);
  });
  types.forEach((t) => {
    const opt = document.createElement("option");
    opt.value = t;
    opt.textContent = PT.typeLabel(t);
    typeSelect.appendChild(opt);
  });

  const packLangs = pack.languages?.length ? pack.languages : ["jp"];
  langSelect.innerHTML = packLangs
    .map((lang) => `<option value="${lang}">${PT.langLabel(lang)}</option>`)
    .join("");

  // Card list defaults to Japanese edition (UI language stays separate)
  langSelect.value = packLangs.indexOf("jp") !== -1 ? "jp" : packLangs[0];
  function render() {
    const editionLang = langSelect.value || packLangs[0];
    const filtered = filterCards(packCards, typeSelect.value);
    const sorted = sortCards(filtered, sortSelect.value, editionLang);
    grid.innerHTML = "";

    if (!sorted.length) {
      grid.innerHTML = `<p class="empty-state">${PT.t("emptyCards")}</p>`;
      return;
    }

    sorted.forEach((card) => {
      const a = document.createElement("a");
      a.className = "card-link";
      a.href = `./card.html?id=${encodeURIComponent(card.id)}`;

      const holo = PT.createHoloCardEl({
        image: PT.cardImageForEdition(card, editionLang),
        name: PT.cardName(card),
        holoStyle: card.holoStyle,
        compact: true,
      });
      a.appendChild(holo);

      const meta = document.createElement("div");
      meta.className = "card-meta";
      meta.innerHTML = `
        <div class="card-meta__name">${PT.cardName(card)}</div>
        <div class="card-meta__sub">
          <span class="${PT.typeBadgeClass(card.type)}">${PT.typeLabel(card.type)}</span>
          <span>${card.rarity}</span>
          <span>${card.number}</span>
          <span>${listPriceLabel(card, editionLang)}</span>
        </div>
      `;
      a.appendChild(meta);
      grid.appendChild(a);
      PT.mountHoloCard(holo);
    });
  }

  PT.mountSiteUpdated(document.getElementById("site-updated"));

  sortSelect.addEventListener("change", render);
  typeSelect.addEventListener("change", render);
  langSelect.addEventListener("change", render);
  render();
})();
