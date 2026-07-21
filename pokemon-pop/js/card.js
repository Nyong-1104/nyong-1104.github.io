(function () {
  const PT = window.PopTracker;

  function popCell(graderData, grade) {
    if (!graderData) return `<td class="pop-empty">—</td>`;
    const v = graderData[grade];
    if (v == null) return `<td class="pop-empty">—</td>`;
    return `<td>${Number(v).toLocaleString("en-US")}</td>`;
  }

  const id = PT.qs("id");
  const packs = PT.getPacks();
  const cards = PT.getCards();
  const card = cards.find((c) => c.id === id) || cards[0];

  if (!card) {
    document.getElementById("detail").innerHTML =
      `<p class="empty-state">카드를 찾을 수 없습니다.</p>`;
    return;
  }

  const pack = packs.find((p) => p.id === card.packId);
  document.title = `${card.nameKo} · PokePop`;

  const back = document.getElementById("nav-back");
  if (back && pack) {
    back.href = `./set.html?pack=${encodeURIComponent(pack.id)}`;
    back.textContent = `← ${pack.nameKo}`;
  }

  const visual = document.getElementById("detail-visual");
  const holo = PT.createHoloCardEl({
    image: card.image,
    name: card.nameKo,
    holoStyle: card.holoStyle,
  });
  visual.appendChild(holo);
  PT.mountHoloCard(holo);

  document.getElementById("card-name").textContent = card.nameKo;
  document.getElementById("card-sub").innerHTML = `
    <span>${card.nameEn}</span>
    <span>${card.number}</span>
    <span class="${PT.typeBadgeClass(card.type)}">${card.typeKo}</span>
    <span class="badge">${card.rarity}</span>
    ${pack ? `<a class="badge" href="./set.html?pack=${pack.id}">${pack.nameKo}</a>` : ""}
  `;

  document.getElementById("price-value").textContent = PT.formatPrice(card.price);
  document.getElementById("price-meta").textContent =
    `${card.price?.source || "PSA"} ${card.price?.grade || "10"} · 기준일 ${card.price?.asOf || card.updatedAt || "—"}`;

  const thead = document.querySelector("#pop-table thead tr");
  thead.innerHTML =
    `<th>그레이딩</th>` +
    PT.GRADE_COLS.map((g) => `<th>${g === "total" ? "Total" : g}</th>`).join("");

  const tbody = document.querySelector("#pop-table tbody");
  tbody.innerHTML = PT.GRADERS.map((g) => {
    const data = card.pop?.[g] ?? null;
    return `<tr>
      <td>${g}</td>
      ${PT.GRADE_COLS.map((col) => popCell(data, col)).join("")}
    </tr>`;
  }).join("");

  document.getElementById("updated").textContent =
    `POP/가격 스냅샷: ${card.updatedAt || "—"} (수동 시드 · 주기 갱신 예정)`;
})();
