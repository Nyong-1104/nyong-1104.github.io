(function () {
  const PT = window.PopTracker;
  const packs = PT.getPacks();
  const cards = PT.getCards();
  const grid = document.getElementById("pack-grid");

  if (!grid) return;

  if (!packs.length || !cards.length) {
    grid.innerHTML = `<p class="empty-state">데이터를 불러오지 못했습니다. 페이지를 새로고침 해주세요.</p>`;
    return;
  }

  grid.classList.add("pack-grid--boosters");

  packs.forEach((pack) => {
    const displayName = pack.nameKo || pack.nameEn;
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
    meta.innerHTML = `
      <div class="pack-entry__code">${pack.code} · ${pack.releaseYear}</div>
      <div class="pack-entry__name${longName ? " pack-entry__name--long" : ""}">${displayName}</div>
      <p class="pack-entry__blurb">${pack.blurb}</p>
      <span class="pack-entry__cta">OPEN →</span>
    `;

    a.appendChild(holo);
    a.appendChild(meta);
    grid.appendChild(a);
    PT.mountHoloCard(holo);
  });

  PT.mountSiteUpdated(document.getElementById("site-updated"));
})();
