window.POP_OPEN_RATES = window.POP_OPEN_RATES || {};
window.POP_OPEN_RATES["pokekyun"] = {
  "packId": "pokekyun",
  "cardsPerPack": 4,
  "packsPerBox": 20,
  "note": "JP CP3 is 4 cards/pack. Simulator rates (not official). Hit slot = 25% RR; cp3-010 2%, cp3-007 3%, other RR share 20%. Special: 0.1% God Pack (4x cp3-010), 0.5% Cute Dedenne Pack (4x cp3-012).",
  "slots": [
    { "id": "n1", "label": "1장", "table": "slot1" },
    { "id": "n2", "label": "2장", "table": "slot2" },
    { "id": "n3", "label": "3장", "table": "slot3" },
    { "id": "hit", "label": "4장", "table": "hit_slot" }
  ],
  "tables": {
    "slot1": [
      { "pool": "C", "w": 100 }
    ],
    "slot2": [
      { "pool": "C", "w": 85 },
      { "pool": "U", "w": 15 }
    ],
    "slot3": [
      { "pool": "U", "w": 90 },
      { "pool": "C", "w": 10 }
    ],
    "hit_slot": [
      { "cardId": "cp3-010", "w": 2 },
      { "cardId": "cp3-007", "w": 3 },
      { "cardId": "cp3-006", "w": 4 },
      { "cardId": "cp3-019", "w": 4 },
      { "cardId": "cp3-020", "w": 4 },
      { "cardId": "cp3-025", "w": 4 },
      { "cardId": "cp3-026", "w": 4 },
      { "pool": "U", "w": 75 }
    ]
  }
};
