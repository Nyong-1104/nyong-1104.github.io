(function () {
  const PT = window.PopTracker;

  function popCell(graderData, grade) {
    if (!graderData) return `<td class="pop-empty">—</td>`;
    const v = graderData[grade];
    if (v == null) return `<td class="pop-empty">—</td>`;
    return `<td>${Number(v).toLocaleString("en-US")}</td>`;
  }

  function renderPop(variant) {
    const thead = document.querySelector("#pop-table thead tr");
    thead.innerHTML =
      `<th>그레이딩</th>` +
      PT.GRADE_COLS.map((g) => `<th>${g === "total" ? "Total" : g}</th>`).join("");

    const tbody = document.querySelector("#pop-table tbody");
    if (!variant?.pop) {
      tbody.innerHTML = `<tr><td colspan="${PT.GRADE_COLS.length + 1}" class="pop-empty pop-empty--message">POP 데이터 없음 (Tier B는 가격만 수집)</td></tr>`;
      return;
    }

    tbody.innerHTML = PT.GRADERS.map((g) => {
      const data = variant.pop[g] ?? null;
      return `<tr>
        <td>${g}</td>
        ${PT.GRADE_COLS.map((col) => popCell(data, col)).join("")}
      </tr>`;
    }).join("");
  }

  function renderEmptyState(card, lang) {
    document.getElementById("price-value").textContent = "—";
    document.getElementById("price-meta").textContent = `${PT.langLabel(lang)} · 데이터 없음`;
    const tbody = document.querySelector("#pop-table tbody");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="${PT.GRADE_COLS.length + 1}" class="pop-empty pop-empty--message">아직 수집되지 않았습니다.</td></tr>`;
    }
  }

  function renderTierC() {
    document.getElementById("price-value").textContent = "—";
    document.getElementById("price-meta").textContent = PT.tierLabel(card.tier);
    const tbody = document.querySelector("#pop-table tbody");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="${PT.GRADE_COLS.length + 1}" class="pop-empty pop-empty--message">Tier C 카드는 POP/가격 수집 대상이 아닙니다.</td></tr>`;
    }
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
    <span class="badge badge--tier badge--tier-${(card.tier || "c").toLowerCase()}">${PT.tierLabel(card.tier)}</span>
    ${pack ? `<a class="badge" href="./set.html?pack=${pack.id}">${pack.nameKo}</a>` : ""}
  `;

  const tabs = document.getElementById("lang-tabs");
  const packLangs = pack?.languages?.length ? pack.languages : ["jp", "kr"];
  let activeLang = packLangs[0];

  function getUpdatedText() {
    if (card.tier === "C") return "카탈로그 정보만 제공됩니다.";
    const variant = card.variants?.[activeLang];
    if (!variant) return `${PT.langLabel(activeLang)} · 아직 수집되지 않았습니다.`;
    const ts = variant.updatedAt || PT.getSiteUpdatedAt();
    return `POP/가격 스냅샷: ${PT.formatUpdatedDisplay(ts)} (${PT.langLabel(activeLang)} · ${PT.tierLabel(card.tier)})`;
  }

  const repaintUpdated = PT.bindRelativeTime(document.getElementById("updated"), getUpdatedText);

  function renderVariant(lang) {
    activeLang = lang;
    document.querySelectorAll(".lang-tab").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.lang === lang);
    });

    if (card.tier === "C") {
      renderTierC();
      repaintUpdated();
      return;
    }

    const variant = card.variants?.[lang];
    if (!variant) {
      renderEmptyState(card, lang);
      repaintUpdated();
      return;
    }

    const priceWhen = variant.price?.asOf || variant.updatedAt;
    document.getElementById("price-value").textContent = PT.formatPrice(variant.price);
    document.getElementById("price-meta").textContent =
      `${variant.price?.source || "PSA"} ${variant.price?.grade || "10"} · ${PT.langLabel(lang)} · ${PT.formatUpdatedDisplay(priceWhen)}`;
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
