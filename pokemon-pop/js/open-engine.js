/**
 * Pack-open draw engine — weighted slots from open-rates JSON.
 */
window.PopTracker = window.PopTracker || {};

(function (PT) {
  function rarityKey(card) {
    return String(card.rarity || "").toUpperCase();
  }

  function buildPools(cards, packId) {
    const packCards = cards.filter(function (c) {
      return c.packId === packId;
    });
    const pools = {
      C: [],
      U: [],
      R: [],
      RR: [],
      AR: [],
      SR: [],
      SAR: [],
      UR: [],
      MB: [],
      MSB: [],
    };
    const byId = {};
    packCards.forEach(function (c) {
      const r = rarityKey(c);
      if (pools[r]) pools[r].push(c);
      if (c && c.id) byId[c.id] = c;
    });
    pools._all = packCards;
    pools._byId = byId;
    return pools;
  }

  function pickWeighted(entries) {
    let total = 0;
    for (let i = 0; i < entries.length; i++) total += Math.max(0, entries[i].w || 0);
    if (total <= 0) return null;
    let roll = Math.random() * total;
    for (let i = 0; i < entries.length; i++) {
      roll -= Math.max(0, entries[i].w || 0);
      if (roll <= 0) return entries[i];
    }
    return entries[entries.length - 1];
  }

  function pickFromPool(pool, usedIds) {
    if (!pool || !pool.length) return null;
    const available = pool.filter(function (c) {
      return !usedIds.has(c.id);
    });
    const list = available.length ? available : pool;
    return list[Math.floor(Math.random() * list.length)] || null;
  }

  /**
   * @param {object} rates open-rates JSON
   * @param {object[]} cards catalog cards
   * @returns {{slotId:string,label:string,card:object}[]}
   */
  PT.drawPackFromRates = function (rates, cards) {
    if (!rates || !rates.slots || !rates.tables) return [];
    const pools = buildPools(cards, rates.packId);
    const used = new Set();
    const results = [];

    rates.slots.forEach(function (slot) {
      const table = rates.tables[slot.table] || [];
      let card = null;
      for (let attempt = 0; attempt < 8 && !card; attempt++) {
        const entry = pickWeighted(table);
        if (!entry) break;
        if (entry.cardId) {
          const specific = pools._byId && pools._byId[entry.cardId];
          if (specific && !used.has(specific.id)) card = specific;
        } else {
          card = pickFromPool(pools[entry.pool], used);
        }
      }
      if (!card) {
        // fallback: any unused pack card, then any
        const all = pools._all || [];
        card = pickFromPool(all, used) || all[0] || null;
      }
      if (card) used.add(card.id);
      results.push({
        slotId: slot.id,
        label: slot.label || slot.id,
        card: card,
      });
    });

    return results;
  };

  PT.loadOpenRates = function (packId) {
    const embedded =
      (window.POP_OPEN_RATES && window.POP_OPEN_RATES[packId]) || null;
    if (embedded) return Promise.resolve(embedded);
    return fetch("./data/open-rates/" + encodeURIComponent(packId) + ".json", {
      cache: "no-store",
    }).then(function (res) {
      if (!res.ok) throw new Error("rates " + res.status);
      return res.json();
    });
  };
})(window.PopTracker);
