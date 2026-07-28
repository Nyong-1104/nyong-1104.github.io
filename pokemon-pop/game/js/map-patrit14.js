/**
 * Patrit 14–style layout (15×13).
 * Approximation of national map: soft fill (~138), pushables, center ship + 4 pillars.
 * Tile/character art under assets/ are dummies — replace later with same filenames.
 *
 * . empty | S soft | P pushable soft | H pillar | G ship (hard)
 */
(function (global) {
  const MAP_W = 15;
  const MAP_H = 13;

  const TILE = {
    EMPTY: 0,
    SOFT: 1,
    PUSH: 2,
    PILLAR: 3,
    SHIP: 4,
  };

  const RAW = [
    "..SS.SPPSPS.SS.",
    ".SPSSSSSSSSSPS.",
    "S.SSSSSSSSSSS.S",
    "SSP.SSH.HSS.PSS",
    "SPSSSSS.SSSSSPS",
    "SS.SS..GGG..SS.",
    "SP.SS.GGGGG.S.P",
    "SS.SS..GGG..SS.",
    "SPSSSSS.SSSSSPS",
    "SSP.SSH.HSS.PSS",
    "S.SSSSSSSSSSS.S",
    ".SPSSSSSSSSSPS.",
    "..SS.SPPSPS.SS.",
  ];

  const CHAR_TO_TILE = {
    ".": TILE.EMPTY,
    S: TILE.SOFT,
    P: TILE.PUSH,
    H: TILE.PILLAR,
    G: TILE.SHIP,
  };

  function createPatrit14Grid() {
    if (RAW.length !== MAP_H || RAW.some((row) => row.length !== MAP_W)) {
      throw new Error("Patrit14 map size must be 15×13");
    }
    return RAW.map((row) => [...row].map((ch) => CHAR_TO_TILE[ch]));
  }

  function isSolid(tile) {
    return (
      tile === TILE.SOFT ||
      tile === TILE.PUSH ||
      tile === TILE.PILLAR ||
      tile === TILE.SHIP
    );
  }

  function isBreakable(tile) {
    return tile === TILE.SOFT || tile === TILE.PUSH;
  }

  function isHard(tile) {
    return tile === TILE.PILLAR || tile === TILE.SHIP;
  }

  global.PatritMap = {
    MAP_W,
    MAP_H,
    TILE,
    createPatrit14Grid,
    isSolid,
    isBreakable,
    isHard,
    PLAYER_SPAWN: { x: 0, y: 0 },
    SEAT_SPAWNS: [
      { x: 0, y: 0 },
      { x: 7, y: 0 },
      { x: 14, y: 0 },
      { x: 0, y: 6 },
      { x: 14, y: 6 },
      { x: 0, y: 12 },
      { x: 7, y: 12 },
      { x: 14, y: 12 },
    ],
  };
})(window);
