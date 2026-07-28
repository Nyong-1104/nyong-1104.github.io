/**
 * Simple solo bots. Returns one-frame input for a bot player.
 */
(function (global) {
  const DIRS = [
    { up: true, down: false, left: false, right: false, dx: 0, dy: -1 },
    { up: false, down: true, left: false, right: false, dx: 0, dy: 1 },
    { up: false, down: false, left: true, right: false, dx: -1, dy: 0 },
    { up: false, down: false, left: false, right: true, dx: 1, dy: 0 },
  ];

  function cell(p) {
    return { cx: Math.floor(p.x), cy: Math.floor(p.y) };
  }

  function inBlast(world, cx, cy) {
    return world.blasts.some((b) => b.x === cx && b.y === cy);
  }

  function dangerSoon(world, cx, cy) {
    if (inBlast(world, cx, cy)) return true;
    return world.bombs.some((b) => {
      if (b.fuse > 1.2) return false;
      if (b.x === cx && b.y === cy) return true;
      if (b.x === cx && Math.abs(b.y - cy) <= b.range) {
        // rough line-of-sight ignore soft for flee
        return true;
      }
      if (b.y === cy && Math.abs(b.x - cx) <= b.range) return true;
      return false;
    });
  }

  function canStep(world, cx, cy) {
    if (cx < 0 || cy < 0 || cx >= world.MAP_W || cy >= world.MAP_H) return false;
    const t = world.grid[cy][cx];
    if (world.isSolid(t)) return false;
    if (world.bombs.some((b) => b.x === cx && b.y === cy)) return false;
    return true;
  }

  function think(p, world) {
    const none = { up: false, down: false, left: false, right: false, bomb: false, item: false };
    if (!p.alive) return none;

    if (p.stunned) {
      return { ...none, item: p.needles > 0 };
    }

    const { cx, cy } = cell(p);
    if (!p._bot) {
      p._bot = { dir: (Math.random() * 4) | 0, thinkIn: 0, bombCd: 1 + Math.random() * 2 };
    }
    const bot = p._bot;
    bot.thinkIn -= world.dt;
    bot.bombCd -= world.dt;

    // Flee danger
    if (dangerSoon(world, cx, cy)) {
      let best = null;
      DIRS.forEach((d, i) => {
        const nx = cx + d.dx;
        const ny = cy + d.dy;
        if (!canStep(world, nx, ny)) return;
        if (dangerSoon(world, nx, ny)) return;
        best = i;
      });
      if (best != null) bot.dir = best;
    } else if (bot.thinkIn <= 0) {
      bot.thinkIn = 0.35 + Math.random() * 0.7;
      // Bias toward nearest living human / item
      let target = null;
      let bestDist = 1e9;
      world.items.forEach((it) => {
        const d = Math.abs(it.x - cx) + Math.abs(it.y - cy);
        if (d < bestDist) {
          bestDist = d;
          target = { x: it.x, y: it.y };
        }
      });
      world.players.forEach((o) => {
        if (o.seat === p.seat || !o.alive || o.stunned) return;
        const d = Math.abs(o.x - cx) + Math.abs(o.y - cy);
        if (d < bestDist) {
          bestDist = d;
          target = { x: Math.floor(o.x), y: Math.floor(o.y) };
        }
      });

      const options = DIRS.map((d, i) => ({ i, ok: canStep(world, cx + d.dx, cy + d.dy) })).filter(
        (o) => o.ok
      );
      if (options.length) {
        if (target && Math.random() < 0.7) {
          options.sort((a, b) => {
            const da = DIRS[a.i];
            const db = DIRS[b.i];
            const sa =
              Math.abs(cx + da.dx - target.x) + Math.abs(cy + da.dy - target.y);
            const sb =
              Math.abs(cx + db.dx - target.x) + Math.abs(cy + db.dy - target.y);
            return sa - sb;
          });
          bot.dir = options[0].i;
        } else {
          bot.dir = options[(Math.random() * options.length) | 0].i;
        }
      }
    }

    const move = DIRS[bot.dir] || DIRS[0];
    let bomb = false;
    if (bot.bombCd <= 0 && Math.random() < 0.035) {
      // Prefer bombing near soft block or enemy
      const nearSoft = DIRS.some((d) => {
        const t = world.grid[cy + d.dy] && world.grid[cy + d.dy][cx + d.dx];
        return world.isBreakable(t);
      });
      const nearEnemy = world.players.some((o) => {
        if (o.seat === p.seat || !o.alive) return false;
        return Math.abs(o.x - p.x) + Math.abs(o.y - p.y) < 3.5;
      });
      if (nearSoft || nearEnemy || Math.random() < 0.15) {
        bomb = true;
        bot.bombCd = 1.6 + Math.random() * 2.2;
      }
    }

    return {
      up: move.up,
      down: move.down,
      left: move.left,
      right: move.right,
      bomb,
      item: false,
    };
  }

  global.BnbBots = { think };
})(window);
