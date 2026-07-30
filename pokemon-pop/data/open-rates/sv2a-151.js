window.POP_OPEN_RATES = window.POP_OPEN_RATES || {};
window.POP_OPEN_RATES["sv2a-151"] = {
  "packId": "sv2a-151",
  "cardsPerPack": 7,
  "packsPerBox": 20,
  "note": "Community box-rate calibration (not official). Targets ~AR 0.15, RR 0.25, SR 0.05, SAR 0.012, UR 0.003, MSB 0.05, MB 0.80 per pack.",
  "slots": [
    { "id": "n1", "label": "노멀1", "table": "common_mix" },
    { "id": "n2", "label": "노멀2", "table": "common_mix" },
    { "id": "n3", "label": "노멀3", "table": "common_mix" },
    { "id": "n4", "label": "노멀4", "table": "common_mix" },
    { "id": "rev", "label": "리버스", "table": "reverse_slot" },
    { "id": "rare", "label": "레어", "table": "rare_slot" },
    { "id": "hit", "label": "히트", "table": "hit_slot" }
  ],
  "tables": {
    "common_mix": [
      { "pool": "C", "w": 55 },
      { "pool": "U", "w": 35 },
      { "pool": "R", "w": 10 }
    ],
    "reverse_slot": [
      { "pool": "MB", "w": 80 },
      { "pool": "C", "w": 12 },
      { "pool": "U", "w": 8 }
    ],
    "rare_slot": [
      { "pool": "R", "w": 85 },
      { "pool": "RR", "w": 15 }
    ],
    "hit_slot": [
      { "pool": "R", "w": 550 },
      { "pool": "AR", "w": 150 },
      { "pool": "RR", "w": 100 },
      { "pool": "MB", "w": 85 },
      { "pool": "SR", "w": 50 },
      { "pool": "MSB", "w": 50 },
      { "pool": "SAR", "w": 12 },
      { "pool": "UR", "w": 3 }
    ]
  }
};
