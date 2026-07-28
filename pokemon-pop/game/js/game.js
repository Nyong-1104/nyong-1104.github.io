(function () {
  const { MAP_W, MAP_H, TILE, createPatrit14Grid, isSolid, isBreakable, isHard, SEAT_SPAWNS } =
    window.PatritMap;

  const TILE_SIZE = 48;
  const STAT_MIN = 1;
  const STAT_MAX = 10;
  const BLAST_TTL = 0.42;
  const SNAPSHOT_MS = 50;
  const STUN_TIME = 5;
  const INVULN_TIME = 1;
  const SCORE_KILL = 100;
  const SCORE_SAVE = 50;
  const SCORE_WIN = 200;

  const ASSET = {
    floor: "assets/tiles/floor.png",
    soft: "assets/tiles/soft.png",
    push: "assets/tiles/push.png",
    hard: "assets/tiles/hard.png",
    ship: "assets/tiles/ship.png",
    pillar: "assets/tiles/pillar.png",
    bomb: "assets/tiles/bomb.png",
    blast: "assets/tiles/blast.png",
    itemBalloon: "assets/tiles/item-balloon.png",
    itemFire: "assets/tiles/item-fire.png",
    itemSpeed: "assets/tiles/item-speed.png",
    itemNeedle: "assets/tiles/item-needle.png",
    charFront: "assets/character/front.png",
    charBack: "assets/character/back.png",
    charLeft: "assets/character/left.png",
    charRight: "assets/character/right.png",
  };

  const imgs = {};
  let loaded = 0;
  const keys = Object.keys(ASSET);

  const canvas = document.getElementById("game-canvas");
  const ctx = canvas.getContext("2d");
  const hudBalloon = document.getElementById("stat-balloon");
  const hudFire = document.getElementById("stat-fire");
  const hudSpeed = document.getElementById("stat-speed");
  const hudScore = document.getElementById("stat-score");
  const hudNeedle = document.getElementById("stat-needle");
  const overlay = document.getElementById("game-overlay");
  const overlayTitle = document.getElementById("overlay-title");
  const overlayScore = document.getElementById("overlay-score");
  const overlayBtn = document.getElementById("overlay-btn");
  const overlayMenu = document.getElementById("overlay-menu");
  const overlaySave = document.getElementById("overlay-save");
  const rankModeNote = document.getElementById("rank-mode-note");
  const rankOverlay = document.getElementById("rank-overlay");
  const rankList = document.getElementById("rank-list");
  const rankListMode = document.getElementById("rank-list-mode");
  const rankClose = document.getElementById("rank-close");
  const btnRank = document.getElementById("btn-rank");
  const soloActions = document.getElementById("solo-actions");

  canvas.width = MAP_W * TILE_SIZE;
  canvas.height = MAP_H * TILE_SIZE;

  let mode = "menu";
  let grid;
  let items;
  let bombs;
  let blasts;
  let players;
  let localSeat = 0;
  let isHost = true;
  let remoteInputs = {};
  let stats;
  let running = false;
  let lastTs = 0;
  let pendingResult = null;
  let savedThisRound = false;
  let snapAcc = 0;
  let multiEnded = false;
  let soloBotCount = 3;
  let mySocketId = null;

  function bombKey(x, y) {
    return `${x},${y}`;
  }

  function loadImages(done) {
    keys.forEach((k) => {
      const img = new Image();
      img.onload = img.onerror = () => {
        loaded += 1;
        if (loaded === keys.length) done();
      };
      img.src = ASSET[k];
      imgs[k] = img;
    });
  }

  function localPlayer() {
    return players.find((p) => p.seat === localSeat) || players[0];
  }

  function calcScore(p, won) {
    const pl = p || localPlayer();
    if (!pl) return 0;
    return pl.kills * SCORE_KILL + pl.saves * SCORE_SAVE + (won ? SCORE_WIN : 0);
  }

  function syncHud() {
    const p = localPlayer();
    if (!p) return;
    hudBalloon.textContent = String(p.maxBalloon);
    hudFire.textContent = String(p.fire);
    hudSpeed.textContent = String(p.speed);
    hudNeedle.textContent = String(p.needles);
    hudScore.textContent = String(p.kills);
  }

  function aliveFightingCount() {
    return players.filter((p) => p.alive).length;
  }

  function countBreakables() {
    let n = 0;
    for (let y = 0; y < MAP_H; y += 1) {
      for (let x = 0; x < MAP_W; x += 1) {
        if (isBreakable(grid[y][x])) n += 1;
      }
    }
    return n;
  }

  function clearSpawnTiles(seatsUsed) {
    seatsUsed.forEach((seat) => {
      const sp = SEAT_SPAWNS[seat];
      if (!sp) return;
      const { x, y } = sp;
      if (inBounds(x, y) && isBreakable(grid[y][x])) grid[y][x] = TILE.EMPTY;
      [
        [1, 0],
        [-1, 0],
        [0, 1],
        [0, -1],
      ].forEach(([dx, dy]) => {
        const nx = x + dx;
        const ny = y + dy;
        if (inBounds(nx, ny) && isBreakable(grid[ny][nx])) grid[ny][nx] = TILE.EMPTY;
      });
    });
  }

  function makePlayer(seat, name, isBot) {
    const spawn = SEAT_SPAWNS[seat] || SEAT_SPAWNS[0];
    return {
      seat,
      name: name || `P${seat + 1}`,
      isBot: Boolean(isBot),
      x: spawn.x + 0.5,
      y: spawn.y + 0.5,
      dir: "front",
      alive: true,
      stunned: false,
      stunTimer: 0,
      invuln: 0,
      fire: STAT_MIN,
      speed: STAT_MIN,
      maxBalloon: STAT_MIN,
      needles: 0,
      kills: 0,
      saves: 0,
      lastHitBy: null,
      softPass: new Set(),
      _bot: null,
    };
  }

  function resetSolo(botCount) {
    mode = "solo";
    isHost = true;
    localSeat = 0;
    soloBotCount = Math.max(0, Math.min(7, Number(botCount) || 0));
    grid = createPatrit14Grid();
    const seats = [];
    for (let i = 0; i <= soloBotCount; i += 1) seats.push(i);
    clearSpawnTiles(seats);
    items = [];
    bombs = [];
    blasts = [];
    players = [makePlayer(0, (window.BnbAccount.getSession() || {}).nickname || "Player", false)];
    for (let i = 1; i <= soloBotCount; i += 1) {
      players.push(makePlayer(i, `Bot${i}`, true));
    }
    stats = { timeSec: 0 };
    pendingResult = null;
    savedThisRound = false;
    multiEnded = false;
    remoteInputs = {};
    running = true;
    overlay.hidden = true;
    soloActions.hidden = false;
    rankModeNote.textContent = window.BnbRanking.modeLabel();
    syncHud();
  }

  function startMulti(roomState) {
    mode = "multi";
    multiEnded = false;
    const sock = window.BnbNet.getSocket();
    mySocketId = sock ? sock.id : null;
    isHost = roomState.hostId === mySocketId;
    const me = (roomState.seats || []).find((p) => p && p.id === mySocketId);
    localSeat = me ? me.seat : 0;

    grid = createPatrit14Grid();
    const used = [];
    players = (roomState.seats || [])
      .map((p, seat) => {
        if (!p) return null;
        used.push(seat);
        return makePlayer(seat, p.name, false);
      })
      .filter(Boolean);
    clearSpawnTiles(used);
    items = [];
    bombs = [];
    blasts = [];
    stats = { timeSec: 0 };
    pendingResult = null;
    remoteInputs = {};
    running = true;
    overlay.hidden = true;
    soloActions.hidden = true;
    syncHud();
  }

  function returnToMenu() {
    mode = "menu";
    running = false;
    overlay.hidden = true;
  }

  function cellOf(px, py) {
    return { cx: Math.floor(px), cy: Math.floor(py) };
  }

  function inBounds(cx, cy) {
    return cx >= 0 && cy >= 0 && cx < MAP_W && cy < MAP_H;
  }

  function overlapsBombCell(cx, cy, px, py) {
    const pad = 0.28;
    return px + pad > cx && px - pad < cx + 1 && py + pad > cy && py - pad < cy + 1;
  }

  function refreshSoftPass(p) {
    p.softPass.forEach((key) => {
      const [x, y] = key.split(",").map(Number);
      if (!overlapsBombCell(x, y, p.x, p.y)) p.softPass.delete(key);
    });
  }

  function blockedCell(p, cx, cy) {
    if (!inBounds(cx, cy)) return true;
    if (isSolid(grid[cy][cx])) return true;
    const key = bombKey(cx, cy);
    if (bombs.some((b) => b.x === cx && b.y === cy) && !p.softPass.has(key)) return true;
    return false;
  }

  function tryMove(p, dx, dy, dt) {
    if (p.stunned) return;
    const base = 2.2 + p.speed * 0.55;
    const step = base * dt;
    let nx = p.x;
    let ny = p.y;
    const pad = 0.28;

    if (dx !== 0) {
      nx = p.x + dx * step;
      const cells = [
        cellOf(nx - pad, p.y - pad),
        cellOf(nx + pad, p.y - pad),
        cellOf(nx - pad, p.y + pad),
        cellOf(nx + pad, p.y + pad),
      ];
      if (cells.some((c) => blockedCell(p, c.cx, c.cy))) nx = p.x;
    }
    if (dy !== 0) {
      ny = p.y + dy * step;
      const cells = [
        cellOf(p.x - pad, ny - pad),
        cellOf(p.x + pad, ny - pad),
        cellOf(p.x - pad, ny + pad),
        cellOf(p.x + pad, ny + pad),
      ];
      if (cells.some((c) => blockedCell(p, c.cx, c.cy))) ny = p.y;
    }

    p.x = Math.max(0.28, Math.min(MAP_W - 0.28, nx));
    p.y = Math.max(0.28, Math.min(MAP_H - 0.28, ny));
    refreshSoftPass(p);
  }

  function placeBomb(p) {
    if (!p.alive || p.stunned) return;
    const { cx, cy } = cellOf(p.x, p.y);
    if (!inBounds(cx, cy) || isSolid(grid[cy][cx])) return;
    if (bombs.some((b) => b.x === cx && b.y === cy)) return;
    const active = bombs.filter((b) => b.owner === p.seat).length;
    if (active >= p.maxBalloon) return;
    bombs.push({ x: cx, y: cy, owner: p.seat, fuse: 2.4, range: p.fire });
    p.softPass.add(bombKey(cx, cy));
  }

  function tryRevive(p) {
    if (!p.alive || !p.stunned || p.needles <= 0) return false;
    p.needles -= 1;
    p.stunned = false;
    p.stunTimer = 0;
    p.invuln = INVULN_TIME;
    p.lastHitBy = null;
    syncHud();
    return true;
  }

  function creditKill(killerSeat, victimSeat) {
    if (killerSeat == null || killerSeat === victimSeat) return;
    const killer = players.find((p) => p.seat === killerSeat);
    if (killer) killer.kills += 1;
  }

  function killPlayer(victim, killerSeat) {
    if (!victim.alive) return;
    victim.alive = false;
    victim.stunned = false;
    victim.stunTimer = 0;
    creditKill(killerSeat != null ? killerSeat : victim.lastHitBy, victim.seat);
    syncHud();
    if (mode === "solo") checkSoloEnd();
    if (mode === "multi") checkMultiWin();
  }

  function stunPlayer(p, ownerSeat) {
    if (!p.alive || p.invuln > 0) return;
    if (p.stunned) {
      killPlayer(p, ownerSeat != null ? ownerSeat : p.lastHitBy);
      return;
    }
    p.stunned = true;
    p.stunTimer = STUN_TIME;
    p.lastHitBy = ownerSeat;
  }

  function spawnItem(cx, cy) {
    // Items (including needle) only drop from broken blocks.
    if (Math.random() > 0.58) return;
    const roll = Math.random();
    let type = "balloon";
    if (roll < 0.22) type = "needle";
    else if (roll < 0.48) type = "fire";
    else if (roll < 0.74) type = "speed";
    items.push({ x: cx, y: cy, type });
  }

  function addBlast(cx, cy, owner) {
    const existing = blasts.find((b) => b.x === cx && b.y === cy);
    if (existing) {
      existing.ttl = Math.max(existing.ttl, BLAST_TTL);
      if (existing.owner == null) existing.owner = owner;
      return;
    }
    blasts.push({ x: cx, y: cy, ttl: BLAST_TTL, owner });
  }

  function breakSoftBlock(cx, cy) {
    grid[cy][cx] = TILE.EMPTY;
    spawnItem(cx, cy);
  }

  function beginExplosion(bomb) {
    addBlast(bomb.x, bomb.y, bomb.owner);
    [
      [1, 0],
      [-1, 0],
      [0, 1],
      [0, -1],
    ].forEach(([dx, dy]) => {
      for (let i = 1; i <= bomb.range; i += 1) {
        const cx = bomb.x + dx * i;
        const cy = bomb.y + dy * i;
        if (!inBounds(cx, cy) || isHard(grid[cy][cx])) break;
        if (isBreakable(grid[cy][cx])) {
          breakSoftBlock(cx, cy);
          break;
        }
        addBlast(cx, cy, bomb.owner);
        const hit = bombs.findIndex((b) => b.x === cx && b.y === cy);
        if (hit >= 0) {
          const chained = bombs.splice(hit, 1)[0];
          beginExplosion(chained);
        }
      }
    });
  }

  function pickItems(p) {
    if (!p.alive) return;
    const { cx, cy } = cellOf(p.x, p.y);
    for (let i = items.length - 1; i >= 0; i -= 1) {
      const it = items[i];
      if (it.x !== cx || it.y !== cy) continue;
      if (it.type === "balloon") p.maxBalloon = Math.min(STAT_MAX, p.maxBalloon + 1);
      else if (it.type === "fire") p.fire = Math.min(STAT_MAX, p.fire + 1);
      else if (it.type === "speed") p.speed = Math.min(STAT_MAX, p.speed + 1);
      else if (it.type === "needle") {
        p.needles = Math.min(5, p.needles + 1);
        if (p.stunned) tryRevive(p);
      }
      items.splice(i, 1);
      syncHud();
    }
  }

  function checkSoloEnd() {
    if (mode !== "solo" || pendingResult) return;
    const me = localPlayer();
    if (!me) return;
    if (!me.alive) {
      endSolo(false);
      return;
    }
    const enemiesAlive = players.some((p) => p.seat !== localSeat && p.alive);
    if (!enemiesAlive) endSolo(true);
  }

  function endSolo(won) {
    if (pendingResult || mode !== "solo") return;
    running = false;
    const me = localPlayer();
    pendingResult = {
      score: calcScore(me, won),
      kills: me ? me.kills : 0,
      saves: me ? me.saves : 0,
      timeSec: stats.timeSec,
      won: Boolean(won),
    };
    overlay.hidden = false;
    soloActions.hidden = false;
    overlayMenu.hidden = false;
    overlayTitle.textContent = won ? "승리!" : "패배…";
    overlayScore.innerHTML = `점수 <strong>${pendingResult.score}</strong><br>킬 ${pendingResult.kills} · 생존 ${Math.floor(pendingResult.timeSec)}초`;
    rankModeNote.textContent = "점수 = 킬×100 (+승리 보너스 200) · 계정 전적에도 기록됩니다";
    overlaySave.disabled = false;
    overlaySave.textContent = "랭킹에 저장";
    overlayBtn.textContent = "다시 하기";

    window.BnbAccount.recordMatch({
      mode: "solo",
      won: Boolean(won),
      kills: pendingResult.kills,
      saves: pendingResult.saves,
      score: pendingResult.score,
      timeSec: pendingResult.timeSec,
      bots: soloBotCount,
    });
  }

  function endMulti(winnerSeat) {
    if (multiEnded) return;
    multiEnded = true;
    running = false;
    const winner = players.find((p) => p.seat === winnerSeat);
    const payload = {
      winnerSeat,
      winnerName: winner ? winner.name : null,
      draw: winnerSeat == null,
    };
    if (isHost) window.BnbNet.sendEnd(payload);
    showMultiResult(payload);
  }

  function showMultiResult(payload) {
    overlay.hidden = false;
    soloActions.hidden = true;
    overlayMenu.hidden = true;
    if (payload.draw) {
      overlayTitle.textContent = "무승부!";
      overlayScore.textContent = "생존자가 없어요.";
    } else {
      overlayTitle.textContent = "경기 종료";
      overlayScore.innerHTML = `우승 <strong>${escapeHtml(payload.winnerName || "?")}</strong>`;
    }
    rankModeNote.textContent = "로비로 돌아가 다시 레디할 수 있어요.";
    overlayBtn.textContent = "로비로";
  }

  function onMultiEnd(payload) {
    showMultiResult(payload);
    setTimeout(() => {
      overlay.hidden = true;
      running = false;
      mode = "lobby";
      window.BnbLobby.showLobby();
    }, 2200);
  }

  function checkMultiWin() {
    if (mode !== "multi" || multiEnded) return;
    const alive = players.filter((p) => p.alive);
    if (alive.length <= 1) endMulti(alive.length === 1 ? alive[0].seat : null);
  }

  function hurtPlayers() {
    players.forEach((p) => {
      if (!p.alive || p.invuln > 0) return;
      const { cx, cy } = cellOf(p.x, p.y);
      const hit = blasts.find((b) => b.x === cx && b.y === cy);
      if (hit) stunPlayer(p, hit.owner);
    });
  }

  function tickStun(dt) {
    players.forEach((p) => {
      if (!p.alive) return;
      if (p.invuln > 0) p.invuln = Math.max(0, p.invuln - dt);
      if (p.stunned) {
        p.stunTimer -= dt;
        if (p.stunTimer <= 0) killPlayer(p, p.lastHitBy);
      }
    });
  }

  function readInputFor(seat) {
    if (seat === localSeat) return window.GameInput.poll();
    return (
      remoteInputs[seat] || {
        up: false,
        down: false,
        left: false,
        right: false,
        bomb: false,
        item: false,
      }
    );
  }

  function applyInput(p, input, dt) {
    if (!p.alive) return;
    if (input.item) tryRevive(p);
    if (p.stunned) return;
    let dx = 0;
    let dy = 0;
    if (input.left) dx -= 1;
    if (input.right) dx += 1;
    if (input.up) dy -= 1;
    if (input.down) dy += 1;
    if (dx && dy) {
      dx *= 0.707;
      dy *= 0.707;
    }
    if (dx || dy) {
      if (Math.abs(dx) > Math.abs(dy)) p.dir = dx < 0 ? "left" : "right";
      else p.dir = dy < 0 ? "back" : "front";
      tryMove(p, dx, dy, dt);
    }
    if (input.bomb) placeBomb(p);
  }

  function botWorld(dt) {
    return {
      dt,
      MAP_W,
      MAP_H,
      grid,
      bombs,
      blasts,
      items,
      players,
      isSolid,
      isBreakable,
    };
  }

  function buildSnapshot() {
    return {
      t: Date.now(),
      grid: grid.map((row) => row.slice()),
      items: items.map((it) => ({ ...it })),
      bombs: bombs.map((b) => ({ ...b })),
      blasts: blasts.map((b) => ({ ...b })),
      players: players.map((p) => ({
        seat: p.seat,
        name: p.name,
        x: p.x,
        y: p.y,
        dir: p.dir,
        alive: p.alive,
        stunned: p.stunned,
        stunTimer: p.stunTimer,
        invuln: p.invuln,
        fire: p.fire,
        speed: p.speed,
        maxBalloon: p.maxBalloon,
        needles: p.needles,
        kills: p.kills,
        saves: p.saves,
      })),
      stats: { ...stats },
    };
  }

  function applySnapshot(snap) {
    if (!snap || isHost) return;
    grid = snap.grid;
    items = snap.items || [];
    bombs = (snap.bombs || []).map((b) => ({ ...b }));
    blasts = (snap.blasts || []).map((b) => ({ ...b }));
    stats = snap.stats || stats;
    const bySeat = new Map((snap.players || []).map((p) => [p.seat, p]));
    players.forEach((p) => {
      const s = bySeat.get(p.seat);
      if (!s) return;
      Object.assign(p, {
        x: s.x,
        y: s.y,
        dir: s.dir,
        alive: s.alive,
        stunned: s.stunned,
        stunTimer: s.stunTimer,
        invuln: s.invuln,
        fire: s.fire,
        speed: s.speed,
        maxBalloon: s.maxBalloon,
        needles: s.needles,
        kills: s.kills,
        saves: s.saves,
      });
    });
    syncHud();
  }

  function update(dt) {
    if (mode === "menu" || mode === "lobby") return;
    if (!running) return;

    if (mode === "multi" && !isHost) {
      window.BnbNet.sendInput(window.GameInput.poll());
      syncHud();
      return;
    }

    stats.timeSec += dt;
    const localInput = window.GameInput.poll();

    players.forEach((p) => {
      let input;
      if (p.isBot) input = window.BnbBots.think(p, botWorld(dt));
      else if (p.seat === localSeat) input = localInput;
      else input = readInputFor(p.seat);

      applyInput(p, input, dt);
      if (!p.isBot && p.seat !== localSeat && remoteInputs[p.seat]) {
        remoteInputs[p.seat] = { ...remoteInputs[p.seat], bomb: false, item: false };
      }
      pickItems(p);
    });

    for (let i = bombs.length - 1; i >= 0; i -= 1) {
      bombs[i].fuse -= dt;
      if (bombs[i].fuse <= 0) beginExplosion(bombs.splice(i, 1)[0]);
    }
    for (let i = blasts.length - 1; i >= 0; i -= 1) {
      blasts[i].ttl -= dt;
      if (blasts[i].ttl <= 0) blasts.splice(i, 1);
    }

    hurtPlayers();
    tickStun(dt);
    if (mode === "solo") checkSoloEnd();
    syncHud();

    if (mode === "multi" && isHost) {
      snapAcc += dt * 1000;
      if (snapAcc >= SNAPSHOT_MS) {
        snapAcc = 0;
        window.BnbNet.sendState(buildSnapshot());
      }
    }
  }

  function drawTile(img, cx, cy) {
    ctx.drawImage(img, cx * TILE_SIZE, cy * TILE_SIZE, TILE_SIZE, TILE_SIZE);
  }

  function draw() {
    if (!grid) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let y = 0; y < MAP_H; y += 1) {
      for (let x = 0; x < MAP_W; x += 1) {
        drawTile(imgs.floor, x, y);
        const t = grid[y][x];
        if (t === TILE.SOFT) drawTile(imgs.soft, x, y);
        else if (t === TILE.PUSH) drawTile(imgs.push, x, y);
        else if (t === TILE.PILLAR) drawTile(imgs.pillar, x, y);
        else if (t === TILE.SHIP) drawTile(imgs.ship, x, y);
      }
    }

    items.forEach((it) => {
      let img = imgs.itemBalloon;
      if (it.type === "fire") img = imgs.itemFire;
      else if (it.type === "speed") img = imgs.itemSpeed;
      else if (it.type === "needle") img = imgs.itemNeedle;
      drawTile(img, it.x, it.y);
    });

    bombs.forEach((b) => {
      const pulse = 1 + Math.sin(performance.now() / 120) * 0.06;
      const size = TILE_SIZE * pulse;
      ctx.drawImage(
        imgs.bomb,
        b.x * TILE_SIZE + (TILE_SIZE - size) / 2,
        b.y * TILE_SIZE + (TILE_SIZE - size) / 2,
        size,
        size
      );
    });
    blasts.forEach((b) => drawTile(imgs.blast, b.x, b.y));

    (players || []).forEach((p) => {
      if (!p.alive) return;
      const sprite =
        p.dir === "back"
          ? imgs.charBack
          : p.dir === "left"
            ? imgs.charLeft
            : p.dir === "right"
              ? imgs.charRight
              : imgs.charFront;
      const w = TILE_SIZE * 0.9;
      const h = TILE_SIZE * 0.9;
      const dx = p.x * TILE_SIZE - w / 2;
      const dy = p.y * TILE_SIZE - h * 0.72;
      if (p.stunned) ctx.globalAlpha = 0.55;
      else if (p.invuln > 0 && Math.floor(performance.now() / 80) % 2 === 0) ctx.globalAlpha = 0.35;
      ctx.drawImage(sprite, dx, dy, w, h);
      ctx.globalAlpha = 1;
      if (p.stunned) {
        ctx.fillStyle = "rgba(255, 220, 80, 0.85)";
        ctx.font = "bold 11px Pretendard, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(`기절 ${Math.ceil(p.stunTimer)}`, p.x * TILE_SIZE, dy - 4);
      }
      if (p.seat === localSeat) {
        ctx.fillStyle = "rgba(61,155,233,0.9)";
        ctx.beginPath();
        ctx.arc(p.x * TILE_SIZE, dy - 2, 4, 0, Math.PI * 2);
        ctx.fill();
      } else if (p.isBot) {
        ctx.fillStyle = "rgba(255,120,120,0.9)";
        ctx.beginPath();
        ctx.arc(p.x * TILE_SIZE, dy - 2, 3, 0, Math.PI * 2);
        ctx.fill();
      }
    });
  }

  function frame(ts) {
    const dt = Math.min(0.05, (ts - lastTs) / 1000 || 0);
    lastTs = ts;
    update(dt);
    draw();
    requestAnimationFrame(frame);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function renderRankList() {
    rankListMode.textContent = window.BnbRanking.modeLabel();
    const entries = await window.BnbRanking.list();
    if (!entries.length) {
      rankList.innerHTML =
        "<li><span class='rank-pos'>-</span><span>아직 기록이 없어요</span><span></span></li>";
      return;
    }
    rankList.innerHTML = entries
      .map((e, i) => {
        const win = e.won ? " · 승" : "";
        return `<li>
          <span class="rank-pos">${i + 1}</span>
          <span>${escapeHtml(e.name)}</span>
          <span class="rank-score">${e.score}</span>
          <span class="rank-meta">킬 ${e.kills || 0} · 세이브 ${e.saves || 0} · ${Math.floor(e.timeSec || 0)}초${win}</span>
        </li>`;
      })
      .join("");
  }

  overlayBtn.addEventListener("click", () => {
    if (mode === "solo") resetSolo(soloBotCount);
    else {
      overlay.hidden = true;
      window.BnbLobby.showLobby();
    }
  });

  overlayMenu.addEventListener("click", () => {
    overlay.hidden = true;
    returnToMenu();
    window.BnbLobby.showMenu();
  });

  overlaySave.addEventListener("click", async () => {
    if (mode !== "solo" || !pendingResult || savedThisRound) return;
    const session = window.BnbAccount.getSession();
    const name = (session && session.nickname) || "Guest";
    overlaySave.disabled = true;
    overlaySave.textContent = "저장 중…";
    const result = await window.BnbRanking.submit({ ...pendingResult, name });
    savedThisRound = true;
    overlaySave.textContent = result.remoteOk ? "온라인 저장됨" : "랭킹 저장됨";
  });

  btnRank.addEventListener("click", async () => {
    rankOverlay.hidden = false;
    await renderRankList();
  });
  rankClose.addEventListener("click", () => {
    rankOverlay.hidden = true;
  });
  document.getElementById("btn-fullscreen").addEventListener("click", () => {
    const root = document.getElementById("game-shell");
    if (root.requestFullscreen) root.requestFullscreen().catch(() => {});
    if (screen.orientation && screen.orientation.lock) {
      screen.orientation.lock("landscape").catch(() => {});
    }
  });

  window.GameInput.bindTouchUI(document.getElementById("touch-controls"));

  window.BnbNet.on("game:input", ({ seat, input }) => {
    if (!isHost || mode !== "multi") return;
    const prev = remoteInputs[seat] || {};
    remoteInputs[seat] = {
      up: !!input.up,
      down: !!input.down,
      left: !!input.left,
      right: !!input.right,
      bomb: !!(input.bomb || prev.bomb),
      item: !!(input.item || prev.item),
    };
  });
  window.BnbNet.on("game:state", (snap) => applySnapshot(snap));

  window.BnbGame = {
    startSolo: (botCount) => resetSolo(botCount),
    startMulti,
    returnToMenu,
    onMultiEnd,
  };

  loadImages(() => {
    window.BnbLobby.bind();
    requestAnimationFrame(frame);
  });
})();
