window.POP_OPEN_RATES = window.POP_OPEN_RATES || {};
window.POP_OPEN_RATES["sv2a-151"] = {
  "packId": "sv2a-151",
  "cardsPerPack": 7,
  "packsPerBox": 20,
  "note": "TEMP DEBUG: force one each of R, RR, MSB, AR, SR, SAR, UR. Restore production rates after rarity-effect QA.",
  "slots": [
    { "id": "n1", "label": "R", "table": "force_r" },
    { "id": "n2", "label": "RR", "table": "force_rr" },
    { "id": "n3", "label": "MSB", "table": "force_msb" },
    { "id": "n4", "label": "AR", "table": "force_ar" },
    { "id": "rev", "label": "SR", "table": "force_sr" },
    { "id": "rare", "label": "SAR", "table": "force_sar" },
    { "id": "hit", "label": "UR", "table": "force_ur" }
  ],
  "tables": {
    "force_r": [{ "pool": "R", "w": 100 }],
    "force_rr": [{ "pool": "RR", "w": 100 }],
    "force_msb": [{ "pool": "MSB", "w": 100 }],
    "force_ar": [{ "pool": "AR", "w": 100 }],
    "force_sr": [{ "pool": "SR", "w": 100 }],
    "force_sar": [{ "pool": "SAR", "w": 100 }],
    "force_ur": [{ "pool": "UR", "w": 100 }]
  }
};
