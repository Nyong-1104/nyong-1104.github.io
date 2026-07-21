(function () {
  const PT = window.PopTracker;
  const RARITY_RANK = { SAR: 5, SIR: 5, RR: 4, SR: 4, R: 3, U: 2, C: 1 };

  function sortCards(list, mode) {
    const arr = list.slice();
    switch (mode) {
      case "price-desc":
        return arr.sort((a, b) => (b.price?.amount || 0) - (a.price?.amount || 0));
      case "price-asc":
        return arr.sort((a, b) => (a.price?.amount || 0) - (b.price?.amount || 0));
      case "type":
        return arr.sort((a, b) => (a.typeKo || "").localeCompare(b.typeKo || "", "ko"));
      case "rarity":
        return arr.sort(
          (a, b) => (RARITY_RANK[b.rarity] || 0) - (RARITY_RANK[a.rarity] || 0)
        );
      case "name":
        return arr.sort((a, b) => a.nameKo.localeCompare(b.nameKo, "ko"));
      default:
        return arr;
    }
  }

  function filterCards(list, lang, type) {
    return list.filter((c) => {
      if (lang && lang !== "all" && c.language !== lang) return false;
      if (type && type !== "all" && c.type !== type) return false;
      return true;
    });
  }

  const packId = PT.qs("pack");
  const packs = PT.getPacks();
  const cards = PT.getCards();
  const grid = document.getElementById("card-grid");

  if (!grid) return;

  const pack = packs.find((p) => p.id === packId) || packs[0];
  if (!pack) {
    grid.innerHTML = `<p class="empty-state">팩을 찾을 수 없습니다.</p>`;
    return;
  }

  document.title = `${pack.nameKo || pack.nameEn} · PokePop`;
  document.getElementById("set-title").textContent = pack.nameKo || pack.nameEn;
  document.getElementById("set-blurb").textContent = pack.blurb;

  const packCards = cards.filter((c) => c.packId === pack.id);
  const typeSelect = document.getElementById("filter-type");
  const types = [];
  packCards.forEach((c) => {
    if (types.indexOf(c.type) === -1) types.push(c.type);
  });
  types.forEach((t) => {
    const card = packCards.find((c) => c.type === t);
    const opt = document.createElement("option");
    opt.value = t;
    opt.textContent = card?.typeKo || t;
    typeSelect.appendChild(opt);
  });

  const sortSelect = document.getElementById("sort-by");
  const langSelect = document.getElementById("filter-lang");

  function render() {
    const filtered = filterCards(packCards, langSelect.value, typeSelect.value);
    const sorted = sortCards(filtered, sortSelect.value);
    grid.innerHTML = "";

    if (!sorted.length) {
      grid.innerHTML = `<p class="empty-state">조건에 맞는 카드가 없습니다.</p>`;
      return;
    }

    sorted.forEach((card) => {
      const a = document.createElement("a");
      a.className = "card-link";
      a.href = `./card.html?id=${encodeURIComponent(card.id)}`;

      const holo = PT.createHoloCardEl({
        image: card.image,
        name: card.nameKo,
        holoStyle: card.holoStyle,
        compact: true,
      });
      a.appendChild(holo);

      const meta = document.createElement("div");
      meta.className = "card-meta";
      meta.innerHTML = `
        <div class="card-meta__name">${card.nameKo}</div>
        <div class="card-meta__sub">
          <span class="${PT.typeBadgeClass(card.type)}">${card.typeKo}</span>
          <span>${card.rarity}</span>
          <span>${PT.formatPrice(card.price)}</span>
        </div>
      `;
      a.appendChild(meta);
      grid.appendChild(a);
      PT.mountHoloCard(holo);
    });
  }

  sortSelect.addEventListener("change", render);
  langSelect.addEventListener("change", render);
  typeSelect.addEventListener("change", render);
  render();
})();
