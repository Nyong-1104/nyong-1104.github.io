(function () {
  const PT = window.PopTracker;
  const packs = PT.getPacks().slice().sort(function (a, b) {
    const aEmpty = !(a.cardIds && a.cardIds.length) ? 1 : 0;
    const bEmpty = !(b.cardIds && b.cardIds.length) ? 1 : 0;
    if (aEmpty !== bEmpty) return aEmpty - bEmpty;
    const ya = Number(a.releaseYear) || 0;
    const yb = Number(b.releaseYear) || 0;
    if (yb !== ya) return yb - ya;
    return String(a.id || "").localeCompare(String(b.id || ""));
  });
  const cards = PT.getCards();
  const grid = document.getElementById("pack-grid");
  const searchPanel = document.getElementById("search-panel");
  const searchGrid = document.getElementById("search-grid");
  const searchTitle = document.getElementById("search-panel-title");
  const searchClear = document.getElementById("search-clear");
  const packsHead = document.getElementById("packs-section-head");
  const packsTitle = document.getElementById("packs-section-title");
  const hero = document.querySelector(".hero-block");
  const packById = {};
  packs.forEach(function (pack) {
    packById[pack.id] = pack;
  });

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

    // Keep pack list visible below search results
    if (hero) hero.hidden = false;
    if (grid) grid.hidden = false;
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
        const pack = packById[card.packId];
        const a = document.createElement("a");
        a.className = "card-link";
        a.href = `./card.html?id=${encodeURIComponent(card.id)}`;
        a.setAttribute("tabindex", "0");

        const name = PT.cardName(card) || card.nameKo || card.nameEn || card.id;
        const img =
          PT.cardImageForEdition(card, "jp") ||
          (card.images && (card.images.jp || card.images.kr || card.images.en)) ||
          card.image ||
          "";

        const holo = PT.createHoloCardEl({
          image: img,
          name: name,
          holoStyle: card.holoStyle || "reverse",
          compact: true,
        });

        const meta = document.createElement("div");
        meta.className = "card-meta";
        const packLabel = pack ? PT.packName(pack) : card.packId || "";
        meta.innerHTML = `
          <div class="card-meta__name">${escapeHtml(name)}</div>
          <div class="card-meta__sub">${escapeHtml(card.number || "")} · ${escapeHtml(
          PT.t("searchPack")
        )}: ${escapeHtml(packLabel)}</div>
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
    const initial = params.get("q") || "";
    if (initial) {
      input.value = initial;
      showSearchResults(initial);
    }

    let timer = null;
    function apply(value, pushUrl) {
      const q = String(value || "").trim();
      showSearchResults(q);
      if (pushUrl) {
        const url = new URL(window.location.href);
        if (q) url.searchParams.set("q", q);
        else url.searchParams.delete("q");
        window.history.replaceState({}, "", url);
      }
    }

    function schedule() {
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        apply(input.value, true);
      }, 120);
    }

    input.addEventListener("input", schedule);
    input.addEventListener("compositionend", function () {
      window.clearTimeout(timer);
      apply(input.value, true);
    });
    input.addEventListener("search", function () {
      apply(input.value, true);
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        window.clearTimeout(timer);
        const q = String(input.value || "").trim();
        apply(q, true);
        const hits = searchCards(q);
        if (hits.length === 1) {
          window.location.href = `./card.html?id=${encodeURIComponent(hits[0].id)}`;
        } else if (hits.length > 1) {
          const first = searchGrid && searchGrid.querySelector(".card-link");
          if (first) first.focus();
          searchPanel && searchPanel.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
      if (e.key === "Escape") {
        input.value = "";
        apply("", true);
        input.blur();
      }
    });
    if (searchClear) {
      searchClear.addEventListener("click", function () {
        input.value = "";
        apply("", true);
        input.focus();
      });
    }
  }

  PT.mountLangSwitcher(document.querySelector(".site-nav"));
  mountPokemonSearch();

  if (!grid) return;

  if (!packs.length || !cards.length) {
    grid.innerHTML = `<p class="empty-state">${PT.t("emptyData")}</p>`;
    return;
  }

  const heroText = document.querySelector(".hero-block p");
  if (heroText) heroText.textContent = PT.t("siteTagline");
  const credit = document.querySelector(".credit");
  if (credit) credit.textContent = PT.t("credit");

  grid.classList.add("pack-grid--boosters");

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
    const emptyNote = !(pack.cardIds && pack.cardIds.length)
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

  PT.mountSiteUpdated(document.getElementById("site-updated"));
})();
