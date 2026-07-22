(function () {
  const PT = window.PopTracker;
  const INCOMPLETE_CARD_CAP = 20;
  const TAB_STORAGE_KEY = "pokepop-pack-group";

  function packCardCount(pack) {
    return (pack && pack.cardIds && pack.cardIds.length) || 0;
  }

  function packIncomplete(pack) {
    if (pack && (pack.listComplete || pack.complete)) return false;
    if (pack && pack.expectedCards != null) {
      return packCardCount(pack) < Number(pack.expectedCards);
    }
    return packCardCount(pack) < INCOMPLETE_CARD_CAP;
  }

  function packGroup(pack) {
    const g = String((pack && pack.listGroup) || "booster").toLowerCase();
    return g === "promo" ? "promo" : "booster";
  }

  function sortPacks(list) {
    return list.slice().sort(function (a, b) {
      const aStub = packIncomplete(a) ? 1 : 0;
      const bStub = packIncomplete(b) ? 1 : 0;
      if (aStub !== bStub) return aStub - bStub;
      const ya = Number(a.releaseYear) || 0;
      const yb = Number(b.releaseYear) || 0;
      if (yb !== ya) return yb - ya;
      return String(a.id || "").localeCompare(String(b.id || ""));
    });
  }

  const allPacks = sortPacks(
    PT.getPacks().filter(function (pack) {
      return !(pack && pack.listHidden);
    })
  );
  const cards = PT.getCards();
  const grid = document.getElementById("pack-grid");
  const searchPanel = document.getElementById("search-panel");
  const searchGrid = document.getElementById("search-grid");
  const searchTitle = document.getElementById("search-panel-title");
  const searchClear = document.getElementById("search-clear");
  const packsHead = document.getElementById("packs-section-head");
  const packsTitle = document.getElementById("packs-section-title");
  const packsSection = document.getElementById("packs-section");
  const hero = document.querySelector(".hero-block");
  const tabRoot = document.getElementById("pack-tabs");
  const packById = {};
  PT.getPacks().forEach(function (pack) {
    packById[pack.id] = pack;
  });

  let activeGroup = "booster";
  try {
    const saved = localStorage.getItem(TAB_STORAGE_KEY);
    if (saved === "promo" || saved === "booster") activeGroup = saved;
  } catch (e) {
    /* ignore */
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function normalize(value) {
    let s = String(value || "");
    if (typeof s.normalize === "function") s = s.normalize("NFC");
    return s
      .toLowerCase()
      .replace(/\s+/g, "")
      .replace(/[()（）[\]【】]/g, "");
  }

  const searchIndex = cards.map(function (card) {
    return {
      card: card,
      hay: normalize(
        [card.nameKo, card.nameEn, card.nameJa, card.number, card.id].filter(Boolean).join(" ")
      ),
    };
  });

  function searchCards(query) {
    const q = normalize(query);
    if (!q) return [];
    const hits = [];
    for (let i = 0; i < searchIndex.length; i++) {
      if (searchIndex[i].hay.indexOf(q) !== -1) hits.push(searchIndex[i].card);
    }
    return hits;
  }

  function setPacksSectionMode(searching) {
    if (packsHead) packsHead.hidden = !searching;
    if (packsTitle) packsTitle.textContent = PT.t("packsSectionTitle");
  }

  function showPacksOnly() {
    if (searchPanel) searchPanel.hidden = true;
    if (searchGrid) searchGrid.innerHTML = "";
    if (hero) hero.hidden = false;
    if (grid) grid.hidden = false;
    if (tabRoot) tabRoot.hidden = false;
    if (packsSection) packsSection.hidden = false;
    setPacksSectionMode(false);
  }

  function showSearchResults(query) {
    const q = String(query || "").trim();
    if (!q) {
      showPacksOnly();
      return;
    }
    if (!searchPanel || !searchGrid) {
      console.warn("[PokePop] search panel missing");
      return;
    }

    if (hero) hero.hidden = true;
    if (grid) grid.hidden = true;
    if (tabRoot) tabRoot.hidden = true;
    setPacksSectionMode(true);

    const hits = searchCards(q);
    searchPanel.hidden = false;
    const countLabel = String(PT.t("searchCount") || "{n}").replace("{n}", String(hits.length));
    if (searchTitle) {
      searchTitle.textContent = `${PT.t("searchTitle")} · “${q}” · ${countLabel}`;
    }
    if (searchClear) searchClear.textContent = PT.t("searchClear");

    searchGrid.innerHTML = "";
    if (!hits.length) {
      searchGrid.innerHTML = `<p class="empty-state">${escapeHtml(PT.t("searchEmpty"))}</p>`;
      return;
    }

    const frag = document.createDocumentFragment();
    hits.forEach(function (card) {
      try {
        const pack = packById[card.packId] || PT.getPacks().find((p) => p.id === card.packId);
        const a = document.createElement("a");
        a.className = "card-link";
        a.href = `./card.html?id=${encodeURIComponent(card.id)}`;
        const holo = PT.createHoloCardEl({
          image: PT.cardImageForEdition(card, "jp") || card.image || "",
          name: PT.cardName(card),
          holoStyle: card.holoStyle || "holo",
          compact: true,
        });
        const meta = document.createElement("div");
        meta.className = "card-meta";
        meta.innerHTML = `
          <div class="card-meta__name">${escapeHtml(PT.cardName(card))}</div>
          <div class="card-meta__sub">
            <span>${escapeHtml(card.number || "")}</span>
            <span>${escapeHtml(card.rarity || "")}</span>
          </div>
          <div class="card-meta__sub">${escapeHtml(PT.t("searchPack"))}: ${escapeHtml(
          pack ? PT.packName(pack) : card.packId || ""
        )}</div>
        `;
        a.appendChild(holo);
        a.appendChild(meta);
        frag.appendChild(a);
        PT.mountHoloCard(holo);
      } catch (err) {
        console.warn("[PokePop] search render failed", card && card.id, err);
      }
    });
    searchGrid.appendChild(frag);
  }

  function mountPokemonSearch() {
    const input = document.getElementById("pokemon-search");
    if (!input) {
      console.warn("[PokePop] search input missing");
      return;
    }
    input.placeholder = PT.t("searchPlaceholder");
    input.setAttribute("enterkeyhint", "search");

    const params = new URLSearchParams(window.location.search);
    const initial = params.get("q");
    if (initial) {
      input.value = initial;
      showSearchResults(initial);
    }

    let timer = null;
    function run(q) {
      const url = new URL(window.location.href);
      if (q) url.searchParams.set("q", q);
      else url.searchParams.delete("q");
      history.replaceState(null, "", url);
      showSearchResults(q);
    }

    input.addEventListener("input", function () {
      const q = input.value.trim();
      clearTimeout(timer);
      timer = setTimeout(function () {
        run(q);
      }, 180);
    });
    input.addEventListener("search", function () {
      run(input.value.trim());
    });
    input.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter") {
        ev.preventDefault();
        const q = input.value.trim();
        run(q);
        if (q) {
          const hits = searchCards(q);
          if (hits.length === 1) {
            const first = searchGrid && searchGrid.querySelector(".card-link");
            if (first) first.click();
          } else {
            searchPanel && searchPanel.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        }
      }
    });
    if (searchClear) {
      searchClear.addEventListener("click", function () {
        input.value = "";
        run("");
        input.focus();
      });
    }
  }

  function syncTabUi() {
    if (!tabRoot) return;
    let pill = tabRoot.querySelector(".pack-tabs__pill");
    if (!pill) {
      pill = document.createElement("span");
      pill.className = "pack-tabs__pill";
      pill.setAttribute("aria-hidden", "true");
      tabRoot.insertBefore(pill, tabRoot.firstChild);
    }
    const buttons = tabRoot.querySelectorAll(".pack-tabs__btn");
    let activeBtn = null;
    buttons.forEach(function (btn) {
      const group = btn.getAttribute("data-pack-group");
      const on = group === activeGroup;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
      if (group === "booster") btn.textContent = PT.t("tabBoosters");
      if (group === "promo") btn.textContent = PT.t("tabPromos");
      if (on) activeBtn = btn;
    });
    if (activeBtn) {
      const rootBox = tabRoot.getBoundingClientRect();
      const btnBox = activeBtn.getBoundingClientRect();
      const left = btnBox.left - rootBox.left;
      pill.style.width = `${btnBox.width}px`;
      pill.style.transform = `translateX(${left}px)`;
    }
  }

  function animateTabPill(fromBtn, toBtn) {
    if (!tabRoot || !toBtn) {
      syncTabUi();
      return;
    }
    let pill = tabRoot.querySelector(".pack-tabs__pill");
    if (!pill) {
      syncTabUi();
      return;
    }
    const rootBox = tabRoot.getBoundingClientRect();
    const toBox = toBtn.getBoundingClientRect();
    const left = toBox.left - rootBox.left;
    pill.classList.add("is-moving");
    pill.style.width = `${toBox.width}px`;
    pill.style.transform = `translateX(${left}px)`;
    const done = function () {
      pill.classList.remove("is-moving");
      pill.removeEventListener("transitionend", done);
    };
    pill.addEventListener("transitionend", done);
  }

  function renderPackGrid() {
    if (!grid) return;
    const packs = allPacks.filter(function (pack) {
      return packGroup(pack) === activeGroup;
    });
    grid.innerHTML = "";
    grid.classList.add("pack-grid--boosters");

    if (!packs.length) {
      grid.innerHTML = `<p class="empty-state">${escapeHtml(PT.t("emptyPackGroup"))}</p>`;
      return;
    }

    packs.forEach((pack) => {
      const displayName = PT.packName(pack);
      const longName = displayName.length > 28;
      const a = document.createElement("a");
      a.className = "pack-entry";
      a.href = `./set.html?pack=${encodeURIComponent(pack.id)}`;

      const holo = PT.createHoloCardEl({
        image: pack.packImage,
        name: displayName,
        holoStyle: "pack",
        compact: false,
      });
      holo.classList.add("holo-card--pack");

      const meta = document.createElement("div");
      meta.className = "pack-entry__meta";
      const emptyNote = packIncomplete(pack)
        ? `<p class="pack-entry__blurb pack-entry__blurb--warn">${PT.t("packNoCardsYet")}</p>`
        : `<p class="pack-entry__blurb">${PT.packBlurb(pack)}</p>`;
      meta.innerHTML = `
        <div class="pack-entry__code">${pack.code} · ${pack.releaseYear}</div>
        <div class="pack-entry__name${longName ? " pack-entry__name--long" : ""}">${displayName}</div>
        ${emptyNote}
        <span class="pack-entry__cta">${PT.t("open")}</span>
      `;

      a.appendChild(holo);
      a.appendChild(meta);
      grid.appendChild(a);
      PT.mountHoloCard(holo);
    });
  }

  function setActiveGroup(group, opts) {
    const next = group === "promo" ? "promo" : "booster";
    const prev = activeGroup;
    activeGroup = next;
    try {
      localStorage.setItem(TAB_STORAGE_KEY, activeGroup);
    } catch (e) {
      /* ignore */
    }
    const buttons = tabRoot ? tabRoot.querySelectorAll(".pack-tabs__btn") : [];
    let fromBtn = null;
    let toBtn = null;
    buttons.forEach(function (btn) {
      const g = btn.getAttribute("data-pack-group");
      if (g === prev) fromBtn = btn;
      if (g === next) toBtn = btn;
      btn.classList.toggle("is-active", g === next);
      btn.setAttribute("aria-selected", g === next ? "true" : "false");
    });
    if (opts && opts.animate) animateTabPill(fromBtn, toBtn);
    else syncTabUi();
    renderPackGrid();
  }

  function mountTabs() {
    if (!tabRoot) return;
    syncTabUi();
    requestAnimationFrame(syncTabUi);
    window.addEventListener("resize", syncTabUi);
    tabRoot.addEventListener("click", function (ev) {
      const btn = ev.target.closest(".pack-tabs__btn");
      if (!btn) return;
      const group = btn.getAttribute("data-pack-group");
      if (group === activeGroup) return;
      setActiveGroup(group, { animate: true });
    });
  }

  PT.mountLangSwitcher(document.querySelector(".site-nav"));
  mountPokemonSearch();
  mountTabs();

  if (!grid) return;

  if (!allPacks.length || !cards.length) {
    grid.innerHTML = `<p class="empty-state">${PT.t("emptyData")}</p>`;
    return;
  }

  const heroText = document.querySelector(".hero-block p");
  if (heroText) heroText.textContent = PT.t("siteTagline");
  const credit = document.querySelector(".credit");
  if (credit) credit.textContent = PT.t("credit");

  renderPackGrid();
  PT.mountSiteUpdated(document.getElementById("site-updated"));
})();
