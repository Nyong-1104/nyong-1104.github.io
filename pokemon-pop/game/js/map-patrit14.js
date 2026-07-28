/**
 * Patrit 14–style layout (15×13).
 * Soft/push/ship/pillar placeholders kept until art is ready.
 * Trees (hard): B2, N2, B12, N12, G7, H7, I7
 *
 * . empty | S soft | P pushable soft | H pillar | G ship (hard) | T tree (hard)
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
    TREE: 5,
  };

  // Columns A–O (0–14), rows 1–13 (0–12)
  const TREE_CELLS = [
    [1, 1], // B2
    [13, 1], // N2
    [1, 11], // B12
    [13, 11], // N12
    [6, 6], // G7
    [7, 6], // H7
    [8, 6], // I7
  ];

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
    T: TILE.TREE,
  };

  function createPatrit14Grid() {
    if (RAW.length !== MAP_H || RAW.some((row) => row.length !== MAP_W)) {
      throw new Error("Patrit14 map size must be 15×13");
    }
    const grid = RAW.map((row) => [...row].map((ch) => CHAR_TO_TILE[ch]));
    TREE_CELLS.forEach(([x, y]) => {
      if (y >= 0 && y < MAP_H && x >= 0 && x < MAP_W) grid[y][x] = TILE.TREE;
    });
    return grid;
  }

  function isSolid(tile) {
    return (
      tile === TILE.SOFT ||
      tile === TILE.PUSH ||
      tile === TILE.PILLAR ||
      tile === TILE.SHIP ||
      tile === TILE.TREE
    );
  }

  function isBreakable(tile) {
    return tile === TILE.SOFT || tile === TILE.PUSH;
  }

  function isHard(tile) {
    return tile === TILE.PILLAR || tile === TILE.SHIP || tile === TILE.TREE;
  }

  global.PatritMap = {
    MAP_W,
    MAP_H,
    TILE,
    TREE_CELLS,
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
