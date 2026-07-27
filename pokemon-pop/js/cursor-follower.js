/** Pixel sprite that follows the mouse (fine pointer only) + click burst particles. */
(function () {
  var FOLLOWERS = [
    {
      src: "./assets/cursor-follower-bulbasaur.png",
      burst: "./assets/cursor-burst-leaf.png",
      evolveHoldMs: 3000,
      evolveOutcomes: [
        {
          src: "./assets/cursor-follower-venusaur.png",
          burst: "./assets/cursor-burst-leaf.png",
          burstFlash: true,
          evolvedXl: true,
          /* Hold A / click: spinning leaf circle every 0.5s. */
          leafSpin: true,
        },
      ],
    },
    {
      src: "./assets/cursor-follower-pokeball.png",
      burst: "./assets/cursor-burst-ball.png",
      evolveHoldMs: 3000,
      evolveOutcomes: [
        {
          src: "./assets/cursor-follower-masterball.png",
          burst: "./assets/cursor-burst-masterball.png",
          /* Hold A / click: fire Master Ball left; catch HTML on hit. */
          masterCatch: true,
        },
      ],
    },
    {
      src: "./assets/cursor-follower-charmander.png",
      burst: "./assets/cursor-burst-fire.png",
      evolveHoldMs: 3000,
      evolveOutcomes: [
        {
          weight: 70,
          src: "./assets/cursor-follower-charizard.png",
          burstFlash: true,
          evolvedXl: true,
          burst: "./assets/cursor-burst-fire.png",
          breathFire: true,
          breathRangeScale: 0.66,
        },
        {
          weight: 30,
          src: "./assets/cursor-follower-mega-charizard-x.png",
          burst: "./assets/cursor-burst-bluefire.png",
          burstFlash: true,
          evolvedXxl: true,
          breathFire: true,
          breathRangeScale: 1,
        },
      ],
    },
    {
      src: "./assets/cursor-follower-squirtle.png",
      burst: "./assets/cursor-burst-water.png",
      evolveHoldMs: 3000,
      evolveOutcomes: [
        {
          src: "./assets/cursor-follower-blastoise.png",
          burst: "./assets/cursor-burst-water.png",
          burstFlash: true,
          evolvedXl: true,
          /* Hold A / click: round water blobs fired ~10deg up; full range; burst on HTML hit. */
          waterBlob: true,
        },
      ],
    },
    {
      src: "./assets/cursor-follower-pikachu.png",
      burst: "./assets/cursor-burst-lightning.png",
      evolveHoldMs: 3000,
      evolveOutcomes: [
        {
          src: "./assets/cursor-follower-raichu.png",
          burst: "./assets/cursor-burst-lightning.png",
          burstFlash: true,
          /* Hold A / click: Raichu lightning bursts every 0.5s (12 fixed rays). */
          holdBurst: true,
        },
      ],
    },
  ];
  var OFFSET_X = 14;
  var OFFSET_Y = 14;
  var PARTICLE_MIN = 6;
  var PARTICLE_MAX = 12;
  var LIFE_MIN = 400;
  var LIFE_MAX = 700;
  var SPEED_MIN = 80;
  var SPEED_MAX = 220;
  var SIZE_MIN = 14;
  var SIZE_MAX = 22;
  var EVOLVED_BURST_SCALE = 1.95;
  var SHORT_CLICK_MS = 400;
  var BREATH_HOLD_MS = 1000;
  /* Raichu: fixed-direction lightning bursts while skill is held. */
  var HOLD_BURST_MS = 500;
  /* 3× denser blue-fire stream (was 40–80ms). */
  var BREATH_SPAWN_MIN = 13;
  var BREATH_SPAWN_MAX = 27;
  /* Leave mouth a bit larger; JS scale still grows them as they travel. */
  var BREATH_SIZE_MIN = 10;
  var BREATH_SIZE_MAX = 16;
  var BREATH_SCALE_START = 0.8;
  var BREATH_SCALE_END = 2.4;
  /* Distance ≈ speed × life/1000; 2× speed × 1.5× life ≈ 3× travel. */
  var BREATH_SPEED_MIN = 280;
  var BREATH_SPEED_MAX = 600;
  var BREATH_LIFE_MIN = 480;
  var BREATH_LIFE_MAX = 780;
  /* Mega X faces left — narrow cone for a focused breath stream. */
  var BREATH_ANGLE = Math.PI;
  var BREATH_CONE = 0.32;
  /* Breath particles can ignite HTML they pass through. */
  var BURN_MS = 3000;
  var BREATH_HIT_CHECK_MS = 55;
  /* Only some particles run hit tests (dense spawn). */
  var BREATH_HIT_SAMPLE = 0.45;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!window.matchMedia("(pointer: fine)").matches) return;

  function pickEvolveOutcome(outcomes) {
    if (!outcomes || !outcomes.length) return null;
    var total = 0;
    for (var i = 0; i < outcomes.length; i++) {
      total += outcomes[i].weight != null ? outcomes[i].weight : 1;
    }
    var roll = Math.random() * total;
    for (var j = 0; j < outcomes.length; j++) {
      roll -= outcomes[j].weight != null ? outcomes[j].weight : 1;
      if (roll <= 0) return outcomes[j];
    }
    return outcomes[outcomes.length - 1];
  }

  var pick = FOLLOWERS[Math.floor(Math.random() * FOLLOWERS.length)];
  var burstSrc = pick.burst;
  var canEvolve = !!(pick.evolveOutcomes && pick.evolveOutcomes.length);
  var evolved = false;
  var evolveBurstFlash = false;
  var canBreath = false;
  var canHoldBurst = false;
  var canLeafSpin = false;
  var canWaterBlob = false;
  var canMasterCatch = false;
  var breathRangeScale = 1;
  var breathing = false;
  var breathInterval = 0;
  var holdBursting = false;
  var holdBurstInterval = 0;
  var leafSpinning = false;
  var leafSpinInterval = 0;
  var waterBlobbing = false;
  var waterBlobInterval = 0;
  var masterCatching = false;
  var masterCatchInterval = 0;
  /* Skill stays on while mouse OR A has been held past BREATH_HOLD_MS. */
  var mouseBreathReady = false;
  var aKeyBreathReady = false;
  var mouseBreathTimer = 0;
  var aKeyBreathTimer = 0;
  var aKeyHeld = false;

  function hasHoldSkill() {
    return (
      canBreath ||
      canHoldBurst ||
      canLeafSpin ||
      canWaterBlob ||
      canMasterCatch
    );
  }

  function followerCenter() {
    var r = img.getBoundingClientRect();
    return {
      cx: r.left + r.width / 2,
      cy: r.top + r.height / 2,
    };
  }

  var img = document.createElement("img");
  img.className = "cursor-follower";
  img.alt = "";
  img.decoding = "async";
  img.draggable = false;
  img.src = pick.src;
  document.body.appendChild(img);

  var x = -9999;
  var y = -9999;
  var visible = false;
  var raf = 0;
  var dirty = false;

  function apply() {
    raf = 0;
    if (!dirty) return;
    dirty = false;
    img.style.transform = "translate3d(" + x + "px," + y + "px,0)";
  }

  function schedule() {
    if (!raf) raf = requestAnimationFrame(apply);
  }

  window.addEventListener(
    "mousemove",
    function (e) {
      x = e.clientX + OFFSET_X;
      y = e.clientY + OFFSET_Y;
      dirty = true;
      if (!visible) {
        visible = true;
        img.classList.add("is-visible");
      }
      schedule();
    },
    { passive: true }
  );

  function spawnBurst(cx, cy) {
    var count =
      PARTICLE_MIN +
      Math.floor(Math.random() * (PARTICLE_MAX - PARTICLE_MIN + 1));
    var bigBurst = evolved;
    var flashBurst = evolved && evolveBurstFlash;
    for (var i = 0; i < count; i++) {
      var p = document.createElement("img");
      p.className = flashBurst
        ? "cursor-burst cursor-burst--element"
        : "cursor-burst";
      p.alt = "";
      p.draggable = false;
      p.src = burstSrc;
      var size = SIZE_MIN + Math.random() * (SIZE_MAX - SIZE_MIN);
      if (bigBurst) size *= EVOLVED_BURST_SCALE;
      p.style.width = size + "px";
      p.style.height = "auto";
      p.style.left = cx - size / 2 + "px";
      p.style.top = cy - size / 2 + "px";
      document.body.appendChild(p);

      var angle = Math.random() * Math.PI * 2;
      var speed = SPEED_MIN + Math.random() * (SPEED_MAX - SPEED_MIN);
      var vx = Math.cos(angle) * speed;
      var vy = Math.sin(angle) * speed;
      var life = LIFE_MIN + Math.random() * (LIFE_MAX - LIFE_MIN);
      var rot = (Math.random() - 0.5) * 540;
      var start = performance.now();

      (function (el, vx0, vy0, life0, rot0, t0) {
        function tick(now) {
          var t = (now - t0) / life0;
          if (t >= 1) {
            if (el.parentNode) el.parentNode.removeChild(el);
            return;
          }
          var ease = 1 - (1 - t) * (1 - t);
          var dx = vx0 * (ease * (life0 / 1000));
          var dy = vy0 * (ease * (life0 / 1000));
          var opacity = 1 - t;
          var scale = 1 - t * 0.35;
          el.style.opacity = String(opacity);
          el.style.transform =
            "translate3d(" +
            dx +
            "px," +
            dy +
            "px,0) rotate(" +
            rot0 * t +
            "deg) scale(" +
            scale +
            ")";
          requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      })(p, vx, vy, life, rot, start);
    }
  }

  /* --- Charizard breath: ignite HTML under fire particles --- */
  var burningMap = new Map();
  /* --- Raichu lightning: zap HTML under lightning particles --- */
  var zappingMap = new Map();
  var ZAP_MS = 750;
  /* --- Venusaur leaves: vine chain overlay on hit HTML --- */
  var vineMap = new Map();
  var VINE_MS = 2400;
  var VINE_LEAF_COUNT = 7;
  var VINE_LEAF_SIZE_MIN = 14;
  var VINE_LEAF_SIZE_MAX = 26;
  /* --- Blastoise water: soak/shake HTML on hit --- */
  var soakingMap = new Map();
  var WATER_SHAKE_MS = 900;
  var WATER_RETURN_DELAY_MS = 1000;
  var WATER_RETURN_MS = 550;

  function isIgniteChrome(el) {
    if (!el || !el.classList) return false;
    return (
      el.classList.contains("cursor-follower") ||
      el.classList.contains("cursor-burst") ||
      el.classList.contains("breath-burn-flame") ||
      el.classList.contains("breath-burn-overlay") ||
      el.classList.contains("lightning-zap-flash") ||
      el.classList.contains("lightning-zap-overlay") ||
      el.classList.contains("venusaur-vine-overlay") ||
      el.classList.contains("venusaur-vine-leaf") ||
      el.classList.contains("venusaur-vine-stem") ||
      el.classList.contains("cursor-burst--water-blob") ||
      el.classList.contains("cursor-burst--masterball") ||
      el.classList.contains("masterball-white-burst") ||
      el.classList.contains("is-masterball-caught") ||
      el.classList.contains("nav-drawer-backdrop")
    );
  }

  function isLayoutShell(el) {
    if (!el || el.nodeType !== 1) return false;
    var tag = el.tagName;
    if (
      tag === "MAIN" ||
      tag === "HEADER" ||
      tag === "NAV" ||
      tag === "FOOTER" ||
      tag === "SECTION" ||
      tag === "ARTICLE" ||
      tag === "ASIDE"
    ) {
      return true;
    }
    if (!el.classList) return false;
    return (
      el.classList.contains("site-nav") ||
      el.classList.contains("site-header") ||
      el.classList.contains("page") ||
      el.classList.contains("hero-block") ||
      el.classList.contains("pack-grid") ||
      el.classList.contains("card-grid") ||
      el.classList.contains("packs-section") ||
      el.classList.contains("search-panel") ||
      el.classList.contains("nav-search") ||
      el.classList.contains("nav-actions")
    );
  }

  function shouldSkipIgnite(el) {
    if (!el || el.nodeType !== 1) return true;
    if (el === document.documentElement || el === document.body) return true;
    var tag = el.tagName;
    if (
      tag === "SCRIPT" ||
      tag === "STYLE" ||
      tag === "LINK" ||
      tag === "META" ||
      tag === "HEAD" ||
      tag === "HTML" ||
      tag === "BR" ||
      tag === "HR"
    ) {
      return true;
    }
    if (isIgniteChrome(el)) return true;
    if (isLayoutShell(el)) return true;
    /* Skip near-full-viewport shells so the whole page does not melt. */
    var w = el.clientWidth;
    var h = el.clientHeight;
    if (
      w >= window.innerWidth * 0.9 &&
      h >= window.innerHeight * 0.85
    ) {
      return true;
    }
    return false;
  }

  /* Prefer the deepest hit unit. Never promote to a parent wrapper. */
  function resolveIgniteTarget(el) {
    var cur = el;
    while (cur && isIgniteChrome(cur)) {
      cur = cur.parentElement;
    }
    if (!cur) return null;
    if (cur.ownerSVGElement) cur = cur.ownerSVGElement;
    if (shouldSkipIgnite(cur)) return null;
    return cur;
  }

  function syncBurnOverlay(overlay, el) {
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;
    var padX = Math.max(4, r.width * 0.06);
    var padY = Math.max(6, r.height * 0.1);
    overlay.style.left = r.left - padX + "px";
    overlay.style.top = r.top - padY + "px";
    overlay.style.width = r.width + padX * 2 + "px";
    overlay.style.height = r.height + padY * 2 + "px";
  }

  function breathBurnTone() {
    return burstSrc && burstSrc.indexOf("bluefire") !== -1 ? "blue" : "fire";
  }

  function clearBurn(el) {
    var state = burningMap.get(el);
    if (!state) return;
    if (state.timer) clearTimeout(state.timer);
    el.classList.remove(
      "is-breath-burning",
      "is-breath-burning--fire",
      "is-breath-burning--blue"
    );
    if (state.onMove) {
      window.removeEventListener("scroll", state.onMove, true);
      window.removeEventListener("resize", state.onMove);
    }
    if (state.overlay && state.overlay.parentNode) {
      state.overlay.parentNode.removeChild(state.overlay);
    }
    burningMap.delete(el);
  }

  function clearAllBurns() {
    var els = [];
    burningMap.forEach(function (_state, el) {
      els.push(el);
    });
    for (var i = 0; i < els.length; i++) clearBurn(els[i]);
  }

  function igniteElement(el) {
    if (!el) return;
    var existing = burningMap.get(el);
    if (existing) {
      clearTimeout(existing.timer);
      existing.timer = setTimeout(function () {
        clearBurn(el);
      }, BURN_MS);
      if (existing.overlay) syncBurnOverlay(existing.overlay, el);
      var tone = breathBurnTone();
      el.classList.remove("is-breath-burning--fire", "is-breath-burning--blue");
      el.classList.add("is-breath-burning", "is-breath-burning--" + tone);
      return;
    }

    /* Filter flicker on the exact hit (works on img/svg/a). */
    var tone = breathBurnTone();
    el.classList.add("is-breath-burning", "is-breath-burning--" + tone);

    /* Fixed overlay pinned to the hit box — never expands to ancestors. */
    var overlay = document.createElement("div");
    overlay.className = "breath-burn-overlay";
    overlay.setAttribute("aria-hidden", "true");
    syncBurnOverlay(overlay, el);

    var spots = [
      { left: "8%", bottom: "2%", w: 22 },
      { left: "42%", bottom: "-4%", w: 30 },
      { left: "72%", bottom: "4%", w: 20 },
    ];
    for (var i = 0; i < spots.length; i++) {
      var flame = document.createElement("img");
      flame.className = "breath-burn-flame";
      flame.alt = "";
      flame.draggable = false;
      flame.src = burstSrc;
      flame.style.width = spots[i].w + "px";
      flame.style.left = spots[i].left;
      flame.style.bottom = spots[i].bottom;
      overlay.appendChild(flame);
    }
    document.body.appendChild(overlay);

    var onMove = function () {
      if (!el.isConnected) {
        clearBurn(el);
        return;
      }
      syncBurnOverlay(overlay, el);
    };
    window.addEventListener("scroll", onMove, true);
    window.addEventListener("resize", onMove);

    var timer = setTimeout(function () {
      clearBurn(el);
    }, BURN_MS);
    burningMap.set(el, { timer: timer, overlay: overlay, onMove: onMove });
  }

  function tryIgniteAt(px, py) {
    if (px < 0 || py < 0 || px >= window.innerWidth || py >= window.innerHeight) {
      return;
    }
    var hit = document.elementFromPoint(px, py);
    var target = resolveIgniteTarget(hit);
    if (target) igniteElement(target);
  }

  function clearZap(el) {
    var state = zappingMap.get(el);
    if (!state) return;
    if (state.timer) clearTimeout(state.timer);
    if (state.onMove) {
      window.removeEventListener("scroll", state.onMove, true);
      window.removeEventListener("resize", state.onMove);
    }
    if (state.overlay && state.overlay.parentNode) {
      state.overlay.parentNode.removeChild(state.overlay);
    }
    zappingMap.delete(el);
  }

  function clearAllZaps() {
    var els = [];
    zappingMap.forEach(function (_state, el) {
      els.push(el);
    });
    for (var i = 0; i < els.length; i++) clearZap(els[i]);
  }

  function zapElement(el) {
    if (!el) return;
    var existing = zappingMap.get(el);
    if (existing) {
      clearTimeout(existing.timer);
      existing.timer = setTimeout(function () {
        clearZap(el);
      }, ZAP_MS);
      if (existing.overlay) syncBurnOverlay(existing.overlay, el);
      return;
    }

    var overlay = document.createElement("div");
    overlay.className = "lightning-zap-overlay";
    overlay.setAttribute("aria-hidden", "true");
    syncBurnOverlay(overlay, el);

    var r = el.getBoundingClientRect();
    var base = Math.max(18, Math.min(90, r.width * 0.42));
    var boltCount = 2 + Math.floor(Math.random() * 2); // 2~3

    for (var i = 0; i < boltCount; i++) {
      var bolt = document.createElement("img");
      bolt.className = "lightning-zap-flash";
      bolt.alt = "";
      bolt.draggable = false;
      bolt.src = burstSrc;

      bolt.style.width = base + Math.random() * base * 0.55 + "px";
      bolt.style.left = 45 + Math.random() * 12 + "%";
      bolt.style.top = 20 + Math.random() * 60 + "%";
      bolt.style.transform =
        "translate(-50%, -50%) rotate(" +
        (Math.random() * 50 - 25) +
        "deg)";

      overlay.appendChild(bolt);
    }
    document.body.appendChild(overlay);

    var onMove = function () {
      if (!el.isConnected) {
        clearZap(el);
        return;
      }
      syncBurnOverlay(overlay, el);
    };
    window.addEventListener("scroll", onMove, true);
    window.addEventListener("resize", onMove);

    var timer = setTimeout(function () {
      clearZap(el);
    }, ZAP_MS);
    zappingMap.set(el, { timer: timer, overlay: overlay, onMove: onMove });
  }

  function tryZapAt(px, py) {
    if (px < 0 || py < 0 || px >= window.innerWidth || py >= window.innerHeight) {
      return;
    }
    var hit = document.elementFromPoint(px, py);
    var target = resolveIgniteTarget(hit);
    if (target) zapElement(target);
  }

  /* --- Venusaur vine: attach a chain of leaves to the hit element --- */
  function clearVine(el) {
    var state = vineMap.get(el);
    if (!state) return;
    if (state.timer) clearTimeout(state.timer);
    if (state.onMove) {
      window.removeEventListener("scroll", state.onMove, true);
      window.removeEventListener("resize", state.onMove);
    }
    if (state.overlay && state.overlay.parentNode) {
      state.overlay.parentNode.removeChild(state.overlay);
    }
    vineMap.delete(el);
  }

  function clearAllVines() {
    var els = [];
    vineMap.forEach(function (_state, el) {
      els.push(el);
    });
    for (var i = 0; i < els.length; i++) clearVine(els[i]);
  }

  function syncVineOverlay(overlay, el) {
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return null;
    var padX = Math.max(4, r.width * 0.06);
    var padY = Math.max(6, r.height * 0.1);
    overlay.style.left = r.left - padX + "px";
    overlay.style.top = r.top - padY + "px";
    overlay.style.width = r.width + padX * 2 + "px";
    overlay.style.height = r.height + padY * 2 + "px";
    return { padX: padX, padY: padY, rect: r };
  }

  function vineElement(el) {
    if (!el) return;
    var existing = vineMap.get(el);
    if (existing) {
      clearTimeout(existing.timer);
      existing.timer = setTimeout(function () {
        clearVine(el);
      }, VINE_MS);
      if (existing.overlay) syncVineOverlay(existing.overlay, el);
      return;
    }

    /* Create pinned overlay: stems + multiple leaf sprites (connected chain). */
    var overlay = document.createElement("div");
    overlay.className = "venusaur-vine-overlay";
    overlay.setAttribute("aria-hidden", "true");
    document.body.appendChild(overlay);

    var sync = syncVineOverlay(overlay, el);
    if (!sync) {
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
      return;
    }
    var padX = sync.padX;
    var padY = sync.padY;
    var r = sync.rect;

    var points = [];
    /* Start/end inside the element box (in normalized coordinates). */
    var startX = 0.18 + Math.random() * 0.2;
    var startY = 0.25 + Math.random() * 0.2;
    var endX = 0.68 + Math.random() * 0.18;
    var endY = 0.65 + Math.random() * 0.2;
    for (var i = 0; i < VINE_LEAF_COUNT; i++) {
      var t = VINE_LEAF_COUNT === 1 ? 0 : i / (VINE_LEAF_COUNT - 1);
      var nx = startX + (endX - startX) * t + (Math.random() - 0.5) * 0.12;
      var ny = startY + (endY - startY) * t + (Math.random() - 0.5) * 0.14;
      if (nx < 0.08) nx = 0.08;
      if (nx > 0.92) nx = 0.92;
      if (ny < 0.08) ny = 0.08;
      if (ny > 0.92) ny = 0.92;
      points.push({
        x: nx * r.width + padX,
        y: ny * r.height + padY,
      });
    }

    /* Stem segments between consecutive leaves. */
    for (var s = 0; s < points.length - 1; s++) {
      var p1 = points[s];
      var p2 = points[s + 1];
      var dx = p2.x - p1.x;
      var dy = p2.y - p1.y;
      var dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) continue;
      var stem = document.createElement("div");
      stem.className = "venusaur-vine-stem";
      stem.style.left = p1.x + "px";
      /* Stem CSS is 3px tall; use top as segment center alignment. */
      stem.style.top = p1.y - 1.5 + "px";
      stem.style.width = dist + "px";
      stem.style.transform = "rotate(" + Math.atan2(dy, dx) + "rad)";
      overlay.appendChild(stem);
    }

    /* Leaf sprites along the stem chain. */
    for (var i2 = 0; i2 < points.length; i2++) {
      var pt = points[i2];
      var size = VINE_LEAF_SIZE_MIN + Math.random() * (VINE_LEAF_SIZE_MAX - VINE_LEAF_SIZE_MIN);
      var rot = Math.random() * 60 - 30;
      var leaf = document.createElement("img");
      leaf.className = "venusaur-vine-leaf";
      leaf.alt = "";
      leaf.draggable = false;
      leaf.src = burstSrc;
      leaf.style.width = size + "px";
      leaf.style.height = "auto";
      leaf.style.left = pt.x - size / 2 + "px";
      leaf.style.top = pt.y - size / 2 + "px";
      leaf.style.setProperty("--rot", rot + "deg");
      leaf.style.animationDelay = i2 * 0.04 + "s";
      overlay.appendChild(leaf);
    }

    var onMove = function () {
      if (!el.isConnected) {
        clearVine(el);
        return;
      }
      syncVineOverlay(overlay, el);
    };
    window.addEventListener("scroll", onMove, true);
    window.addEventListener("resize", onMove);

    var timer = setTimeout(function () {
      clearVine(el);
    }, VINE_MS);
    vineMap.set(el, { timer: timer, overlay: overlay, onMove: onMove });
  }

  function tryVineAt(px, py) {
    if (px < 0 || py < 0 || px >= window.innerWidth || py >= window.innerHeight) {
      return;
    }
    var hit = document.elementFromPoint(px, py);
    var target = resolveIgniteTarget(hit);
    if (target) vineElement(target);
  }

  function clearSoak(el) {
    var state = soakingMap.get(el);
    if (!state) return;
    if (state.shakeTimer) clearTimeout(state.shakeTimer);
    if (state.settleTimer) clearTimeout(state.settleTimer);
    if (state.returnTimer) clearTimeout(state.returnTimer);
    el.classList.remove(
      "is-water-soaked",
      "is-water-pushed",
      "is-water-returning"
    );
    el.style.translate = "";
    el.style.transition = "";
    soakingMap.delete(el);
  }

  function clearAllSoaks() {
    var els = [];
    soakingMap.forEach(function (_state, el) {
      els.push(el);
    });
    for (var i = 0; i < els.length; i++) clearSoak(els[i]);
  }

  function beginWaterReturn(el, gen) {
    var state = soakingMap.get(el);
    if (!state || state.hitGen !== gen || !el.isConnected) return;
    el.classList.remove("is-water-soaked");
    el.classList.add("is-water-returning");
    el.style.transition = "translate " + WATER_RETURN_MS / 1000 + "s ease-out";
    el.style.translate = "0px 0";
    state.returnTimer = setTimeout(function () {
      var cur = soakingMap.get(el);
      /* Abort if hit again while returning (hitGen changed). */
      if (!cur || cur.hitGen !== gen) return;
      clearSoak(el);
    }, WATER_RETURN_MS + 40);
  }

  function shakeElement(el) {
    if (!el) return;
    var state = soakingMap.get(el);
    if (!state) {
      state = {
        hitGen: 0,
        shakeTimer: 0,
        settleTimer: 0,
        returnTimer: 0,
        pushPx: 0,
      };
      soakingMap.set(el, state);
    }

    /* Any new hit cancels shake-end / 1s-settle / return — timers reset. */
    if (state.shakeTimer) clearTimeout(state.shakeTimer);
    if (state.settleTimer) clearTimeout(state.settleTimer);
    if (state.returnTimer) clearTimeout(state.returnTimer);

    if (el.classList.contains("is-water-returning")) {
      el.classList.remove("is-water-returning");
      el.style.transition = "none";
      /* Snap back to the knocked offset before adding another hit. */
      el.style.translate = -state.pushPx + "px 0";
      void el.offsetWidth;
    }

    state.hitGen += 1;
    var gen = state.hitGen;
    state.pushPx += 3;

    el.style.translate = -state.pushPx + "px 0";
    el.classList.add("is-water-pushed");
    el.classList.remove("is-water-soaked");
    void el.offsetWidth;
    el.classList.add("is-water-soaked");

    state.shakeTimer = setTimeout(function () {
      var cur = soakingMap.get(el);
      if (!cur || cur.hitGen !== gen) return;
      el.classList.remove("is-water-soaked");
      el.style.translate = -cur.pushPx + "px 0";
      /* 1s after shake stops; keeps resetting while hits continue. */
      cur.settleTimer = setTimeout(function () {
        var s = soakingMap.get(el);
        if (!s || s.hitGen !== gen) return;
        beginWaterReturn(el, gen);
      }, WATER_RETURN_DELAY_MS);
    }, WATER_SHAKE_MS);
  }

  document.addEventListener(
    "visibilitychange",
    function () {
      if (document.hidden) {
        clearAllBurns();
        clearAllZaps();
        clearAllVines();
        clearAllSoaks();
      }
    },
    { passive: true }
  );
  window.addEventListener(
    "pagehide",
    function () {
      clearAllBurns();
      clearAllZaps();
      clearAllVines();
      clearAllSoaks();
    },
    { passive: true }
  );

  /* --- Charizard breath stream (hold 1s with mouse or A) --- */
  function spawnBreathParticle() {
    /* Mouth sits near the left-center of the left-facing Charizard sprites. */
    var cx = x + 10;
    var cy = y + (img.offsetHeight || 40) * 0.42;
    var p = document.createElement("img");
    p.className = "cursor-burst cursor-burst--breath";
    p.alt = "";
    p.draggable = false;
    p.src = burstSrc;
    var size = BREATH_SIZE_MIN + Math.random() * (BREATH_SIZE_MAX - BREATH_SIZE_MIN);
    p.style.width = size + "px";
    p.style.height = "auto";
    p.style.left = cx - size / 2 + "px";
    p.style.top = cy - size / 2 + "px";
    document.body.appendChild(p);

    var angle = BREATH_ANGLE + (Math.random() - 0.5) * BREATH_CONE;
    var speedMin = BREATH_SPEED_MIN * breathRangeScale;
    var speedMax = BREATH_SPEED_MAX * breathRangeScale;
    var speed = speedMin + Math.random() * (speedMax - speedMin);
    var vx = Math.cos(angle) * speed;
    var vy = Math.sin(angle) * speed;
    var life = BREATH_LIFE_MIN + Math.random() * (BREATH_LIFE_MAX - BREATH_LIFE_MIN);
    var rot = (Math.random() - 0.5) * 360;
    var start = performance.now();
    var doHit = Math.random() < BREATH_HIT_SAMPLE;
    var lastHitAt = 0;

    (function (el, vx0, vy0, life0, rot0, t0, originX, originY, hitEnabled) {
      function tick(now) {
        var t = (now - t0) / life0;
        if (t >= 1) {
          if (el.parentNode) el.parentNode.removeChild(el);
          return;
        }
        var ease = 1 - (1 - t) * (1 - t);
        var dx = vx0 * (ease * (life0 / 1000));
        var dy = vy0 * (ease * (life0 / 1000));
        /* Grow outward, then fade to transparent. */
        var opacity = 1 - t;
        var scale =
          BREATH_SCALE_START +
          ease * (BREATH_SCALE_END - BREATH_SCALE_START);
        el.style.opacity = String(opacity);
        el.style.transform =
          "translate3d(" +
          dx +
          "px," +
          dy +
          "px,0) rotate(" +
          rot0 * t +
          "deg) scale(" +
          scale +
          ")";
        if (
          hitEnabled &&
          now - lastHitAt >= BREATH_HIT_CHECK_MS
        ) {
          lastHitAt = now;
          tryIgniteAt(originX + dx, originY + dy);
        }
        requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    })(p, vx, vy, life, rot, start, cx, cy, doHit);
  }

  function isTypingFocus(el) {
    if (!el || el === document.body || el === document.documentElement) return false;
    var tag = el.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
    if (el.isContentEditable) return true;
    return false;
  }

  /* Raichu lightning: spawn particles in fixed directions (no cone).
     Angle step is controlled by caller. Range scales by `rangeScale`
     to match Charizard breath distance tuning. */
  function spawnLightningRay(originX, originY, angle, rangeScale) {
    var p = document.createElement("img");
    p.className = "cursor-burst cursor-burst--breath";
    p.alt = "";
    p.draggable = false;
    p.src = burstSrc;

    var size = BREATH_SIZE_MIN + Math.random() * (BREATH_SIZE_MAX - BREATH_SIZE_MIN);
    p.style.width = size + "px";
    p.style.height = "auto";
    p.style.left = originX - size / 2 + "px";
    p.style.top = originY - size / 2 + "px";
    document.body.appendChild(p);

    var speedMin = BREATH_SPEED_MIN * rangeScale;
    var speedMax = BREATH_SPEED_MAX * rangeScale;
    var speed = speedMin + Math.random() * (speedMax - speedMin);
    var vx = Math.cos(angle) * speed;
    var vy = Math.sin(angle) * speed;
    var life = BREATH_LIFE_MIN + Math.random() * (BREATH_LIFE_MAX - BREATH_LIFE_MIN);
    var rot = (Math.random() - 0.5) * 360;
    var start = performance.now();

    var doHit = Math.random() < BREATH_HIT_SAMPLE;
    var lastHitAt = 0;

    (function (el, vx0, vy0, life0, rot0, t0, originX0, originY0, hitEnabled) {
      function tick(now) {
        var t = (now - t0) / life0;
        if (t >= 1) {
          if (el.parentNode) el.parentNode.removeChild(el);
          return;
        }
        var ease = 1 - (1 - t) * (1 - t);
        var dx = vx0 * (ease * (life0 / 1000));
        var dy = vy0 * (ease * (life0 / 1000));
        var opacity = 1 - t;
        var scale =
          BREATH_SCALE_START +
          ease * (BREATH_SCALE_END - BREATH_SCALE_START);
        el.style.opacity = String(opacity);
        el.style.transform =
          "translate3d(" +
          dx +
          "px," +
          dy +
          "px,0) rotate(" +
          rot0 * t +
          "deg) scale(" +
          scale +
          ")";
        if (
          hitEnabled &&
          now - lastHitAt >= BREATH_HIT_CHECK_MS
        ) {
          lastHitAt = now;
          tryZapAt(originX0 + dx, originY0 + dy);
        }
        requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    })(p, vx, vy, life, rot, start, originX, originY, doHit);
  }

  function startBreath() {
    if (breathing || !canBreath) return;
    breathing = true;
    function scheduleNext() {
      if (!breathing) return;
      spawnBreathParticle();
      /* Occasionally double-spawn for denser stream. */
      if (Math.random() < 0.45) spawnBreathParticle();
      var delay =
        BREATH_SPAWN_MIN +
        Math.random() * (BREATH_SPAWN_MAX - BREATH_SPAWN_MIN);
      breathInterval = setTimeout(scheduleNext, delay);
    }
    scheduleNext();
  }

  function stopBreathStream() {
    if (breathInterval) {
      clearTimeout(breathInterval);
      breathInterval = 0;
    }
    breathing = false;
  }

  /* Raichu: fixed-direction lightning every HOLD_BURST_MS. */
  function startHoldBurst() {
    if (holdBursting || !canHoldBurst) return;
    holdBursting = true;
    function scheduleNext() {
      if (!holdBursting) return;
      var c = followerCenter();
      /* 12 directions, 30deg spacing. */
      var step = (Math.PI * 2) / 12;
      /* Distance: 66% of Charizard breath range. */
      var rangeScale = 0.66;
      for (var i = 0; i < 12; i++) {
        spawnLightningRay(c.cx, c.cy, i * step, rangeScale);
      }
      holdBurstInterval = setTimeout(scheduleNext, HOLD_BURST_MS);
    }
    scheduleNext();
  }

  function stopHoldBurst() {
    if (holdBurstInterval) {
      clearTimeout(holdBurstInterval);
      holdBurstInterval = 0;
    }
    holdBursting = false;
  }

  /* ---- Venusaur: spinning leaf circle ---------------------------------- */
  var LEAF_COUNT = 10;
  var LEAF_SPIN_SPEED = 180;  /* px/s outward travel */
  var LEAF_LIFE = 900;        /* ms each leaf lives */
  var LEAF_SIZE = 22;
  /* Each burst, leaves start at LEAF_RADIUS px from center. */
  var LEAF_RADIUS = 28;
  var LEAF_HIT_SAMPLE = 0.32;
  var LEAF_HIT_CHECK_MS = 90;

  function spawnLeafSpinBurst() {
    var c = followerCenter();
    var cx = c.cx;
    var cy = c.cy;
    var now = performance.now();
    /* Offset the starting angle each burst so the circle looks like it's spinning. */
    var angleOffset = (now * 0.003) % (Math.PI * 2);
    for (var i = 0; i < LEAF_COUNT; i++) {
      var baseAngle = angleOffset + (Math.PI * 2 / LEAF_COUNT) * i;
      (function (angle) {
        var p = document.createElement("img");
        p.className = "cursor-burst cursor-burst--leaf";
        p.alt = "";
        p.draggable = false;
        p.src = burstSrc;
        /* Start on the circle perimeter. */
        var startX = cx + Math.cos(angle) * LEAF_RADIUS;
        var startY = cy + Math.sin(angle) * LEAF_RADIUS;
        p.style.cssText = [
          "position:fixed",
          "pointer-events:none",
          "user-select:none",
          "z-index:55",
          "width:" + LEAF_SIZE + "px",
          "height:" + LEAF_SIZE + "px",
          "left:" + startX + "px",
          "top:" + startY + "px",
          "transform-origin:50% 50%",
          "will-change:transform,opacity",
          "image-rendering:pixelated",
        ].join(";");
        document.body.appendChild(p);

        /* Spin as the leaf flies outward: 360deg over its lifetime. */
        var vx = Math.cos(angle) * LEAF_SPIN_SPEED;
        var vy = Math.sin(angle) * LEAF_SPIN_SPEED;
        var born = performance.now();
        var doVineHit = Math.random() < LEAF_HIT_SAMPLE;
        var lastVineHitAt = 0;

        function tick(now2) {
          var t = (now2 - born) / LEAF_LIFE;
          if (t >= 1) { if (p.parentNode) p.parentNode.removeChild(p); return; }
          var dx = vx * (now2 - born) / 1000;
          var dy = vy * (now2 - born) / 1000;
          var curX = startX + dx;
          var curY = startY + dy;
          var spin = t * 360;
          var opacity = t < 0.7 ? 1 : 1 - (t - 0.7) / 0.3;
          p.style.left = curX + "px";
          p.style.top  = curY + "px";
          p.style.transform = "rotate(" + spin + "deg)";
          p.style.opacity = opacity;
          if (doVineHit && now2 - lastVineHitAt >= LEAF_HIT_CHECK_MS) {
            lastVineHitAt = now2;
            tryVineAt(curX, curY);
          }
          requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      })(baseAngle);
    }
  }

  function startLeafSpin() {
    if (leafSpinning || !canLeafSpin) return;
    leafSpinning = true;
    function scheduleNext() {
      if (!leafSpinning) return;
      spawnLeafSpinBurst();
      leafSpinInterval = setTimeout(scheduleNext, HOLD_BURST_MS);
    }
    scheduleNext();
  }

  function stopLeafSpin() {
    if (leafSpinInterval) {
      clearTimeout(leafSpinInterval);
      leafSpinInterval = 0;
    }
    leafSpinning = false;
  }
  /* ---------------------------------------------------------------------- */

  /* ---- Blastoise: clustered water blob (~10deg up, full range) ---------- */
  var WATER_BLOB_MS = 420;
  /* Left + 10deg up (screen y grows down → subtract). */
  var WATER_BLOB_ANGLE = Math.PI - (10 * Math.PI) / 180;
  var WATER_BLOB_SPEED = 420;
  var WATER_BLOB_HIT_MS = 45;
  /* Skip hit tests near the cannon so the blob is visible while leaving. */
  var WATER_BLOB_ARM_MS = 220;
  var WATER_BLOB_CLUSTER = 7;
  var WATER_BLOB_CORE_SIZE = 72;

  function spawnWaterScatter(cx, cy) {
    var count = 10 + Math.floor(Math.random() * 6);
    for (var i = 0; i < count; i++) {
      var p = document.createElement("img");
      p.className = "cursor-burst";
      p.alt = "";
      p.draggable = false;
      p.src = burstSrc;
      /* 100% larger than initial scatter sizes. */
      var size = 20 + Math.random() * 32;
      p.style.width = size + "px";
      p.style.height = "auto";
      p.style.left = cx - size / 2 + "px";
      p.style.top = cy - size / 2 + "px";
      document.body.appendChild(p);

      var angle = Math.random() * Math.PI * 2;
      var speed = 140 + Math.random() * 320;
      var vx = Math.cos(angle) * speed;
      var vy = Math.sin(angle) * speed;
      var life = 360 + Math.random() * 320;
      var rot = (Math.random() - 0.5) * 480;
      var start = performance.now();

      (function (el, vx0, vy0, life0, rot0, t0) {
        function tick(now) {
          var t = (now - t0) / life0;
          if (t >= 1) {
            if (el.parentNode) el.parentNode.removeChild(el);
            return;
          }
          var ease = 1 - (1 - t) * (1 - t);
          var dx = vx0 * (ease * (life0 / 1000));
          var dy = vy0 * (ease * (life0 / 1000)) + 50 * t * t;
          el.style.opacity = String(1 - t);
          el.style.transform =
            "translate3d(" +
            dx +
            "px," +
            dy +
            "px,0) rotate(" +
            rot0 * t +
            "deg) scale(" +
            (1 - t * 0.45) +
            ")";
          requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      })(p, vx, vy, life, rot, start);
    }
  }

  function tryWaterHitAt(px, py) {
    if (px < 0 || py < 0 || px >= window.innerWidth || py >= window.innerHeight) {
      return null;
    }
    var hit = document.elementFromPoint(px, py);
    return resolveIgniteTarget(hit);
  }

  function spawnWaterBlob() {
    var c = followerCenter();
    /* Cannon sits on the left-center of left-facing Blastoise. */
    var originX = c.cx - (img.offsetWidth || 48) * 0.28;
    var originY = c.cy - (img.offsetHeight || 48) * 0.05;
    var angle = WATER_BLOB_ANGLE + (Math.random() - 0.5) * 0.06;
    var speed = WATER_BLOB_SPEED * (0.92 + Math.random() * 0.16);
    var vx = Math.cos(angle) * speed;
    var vy = Math.sin(angle) * speed;

    /* Same proven pattern as breath/lightning: fixed <img> + translate3d. */
    var pieces = [];
    var offsets = [{ ox: 0, oy: 0, size: WATER_BLOB_CORE_SIZE }];
    for (var i = 0; i < WATER_BLOB_CLUSTER; i++) {
      offsets.push({
        ox: (Math.random() - 0.5) * 36,
        oy: (Math.random() - 0.5) * 36,
        size: 28 + Math.random() * 28,
      });
    }

    for (var j = 0; j < offsets.length; j++) {
      var o = offsets[j];
      var p = document.createElement("img");
      p.className =
        "cursor-burst cursor-burst--water-blob" +
        (j === 0 ? " cursor-burst--water-core" : "");
      p.alt = "";
      p.draggable = false;
      p.src = burstSrc;
      p.style.width = o.size + "px";
      p.style.height = "auto";
      /* Anchor all pieces at origin; cluster offsets applied in transform. */
      p.style.left = originX - o.size / 2 + "px";
      p.style.top = originY - o.size / 2 + "px";
      document.body.appendChild(p);
      pieces.push({ el: p, ox: o.ox, oy: o.oy, size: o.size });
    }

    var born = performance.now();
    var lastHitAt = 0;
    var alive = true;

    function removeBlob() {
      alive = false;
      for (var k = 0; k < pieces.length; k++) {
        var el = pieces[k].el;
        if (el.parentNode) el.parentNode.removeChild(el);
      }
    }

    function tick(now) {
      if (!alive) return;
      var elapsedMs = now - born;
      var elapsed = elapsedMs / 1000;
      var dx = vx * elapsed;
      var dy = vy * elapsed;
      var curX = originX + dx;
      var curY = originY + dy;
      var spin = elapsed * 120;

      if (
        curX < -160 ||
        curY < -160 ||
        curX > window.innerWidth + 160 ||
        curY > window.innerHeight + 160
      ) {
        removeBlob();
        return;
      }

      for (var k = 0; k < pieces.length; k++) {
        var piece = pieces[k];
        piece.el.style.transform =
          "translate3d(" +
          (dx + piece.ox) +
          "px," +
          (dy + piece.oy) +
          "px,0) rotate(" +
          spin +
          "deg)";
      }

      if (
        elapsedMs >= WATER_BLOB_ARM_MS &&
        now - lastHitAt >= WATER_BLOB_HIT_MS
      ) {
        lastHitAt = now;
        var target = tryWaterHitAt(curX, curY);
        if (target) {
          spawnWaterScatter(curX, curY);
          shakeElement(target);
          removeBlob();
          return;
        }
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  function startWaterBlob() {
    if (waterBlobbing || !canWaterBlob) return;
    waterBlobbing = true;
    function scheduleNext() {
      if (!waterBlobbing) return;
      spawnWaterBlob();
      waterBlobInterval = setTimeout(scheduleNext, WATER_BLOB_MS);
    }
    scheduleNext();
  }

  function stopWaterBlob() {
    if (waterBlobInterval) {
      clearTimeout(waterBlobInterval);
      waterBlobInterval = 0;
    }
    waterBlobbing = false;
  }
  /* ---------------------------------------------------------------------- */

  /* ---- Master Ball: catch HTML on hit, miss flies away ---------------- */
  var MASTERBALL_MS = 200;
  var MASTERBALL_SIZE = 44;
  var MASTERBALL_SPEED = 460;
  var MASTERBALL_ANGLE = Math.PI; /* left */
  var MASTERBALL_ARM_MS = 140;
  var MASTERBALL_HIT_MS = 40;
  var MASTERBALL_BOUNCE_PX = 28;
  var MASTERBALL_RADIUS = MASTERBALL_SIZE / 2;
  var floorBalls = [];
  var floorRaf = 0;
  /* One ball at a time until miss vanishes or catch lands on floor. */
  var masterBallBusy = false;

  function releaseMasterBallBusy() {
    masterBallBusy = false;
    if (masterCatching) {
      if (masterCatchInterval) {
        clearTimeout(masterCatchInterval);
        masterCatchInterval = 0;
      }
      masterCatchInterval = setTimeout(function () {
        if (!masterCatching || masterBallBusy) return;
        spawnMasterBall();
      }, MASTERBALL_MS);
    }
  }

  function findPackEntry(el) {
    var cur = el;
    while (cur && cur !== document.body) {
      if (
        cur.classList &&
        cur.classList.contains("pack-entry") &&
        !cur.classList.contains("pack-entry--box")
      ) {
        return cur;
      }
      cur = cur.parentElement;
    }
    return null;
  }

  function tryMasterHitAt(px, py) {
    if (px < 0 || py < 0 || px >= window.innerWidth || py >= window.innerHeight) {
      return null;
    }
    var hit = document.elementFromPoint(px, py);
    var cur = hit;
    while (cur && isIgniteChrome(cur)) {
      cur = cur.parentElement;
    }
    if (!cur) return null;

    /* Master Ball only catches card pack tiles (holo + meta). */
    var packEntry = findPackEntry(cur);
    if (!packEntry) return null;

    var holo = packEntry.querySelector(".holo-card.holo-card--pack");
    if (!holo) holo = packEntry.querySelector(".holo-card--pack");
    var meta = packEntry.querySelector(".pack-entry__meta");
    if (!holo || !meta) return null;
    if (
      holo.classList.contains("is-masterball-caught") ||
      holo.classList.contains("is-masterball-catching") ||
      meta.classList.contains("is-masterball-caught") ||
      meta.classList.contains("is-masterball-catching")
    ) {
      return null;
    }
    return { parts: [holo, meta] };
  }

  function spawnMasterWhiteBurst(cx, cy) {
    var flash = document.createElement("div");
    flash.className = "masterball-white-burst";
    flash.setAttribute("aria-hidden", "true");
    flash.style.left = cx + "px";
    flash.style.top = cy + "px";
    document.body.appendChild(flash);
    setTimeout(function () {
      if (flash.parentNode) flash.parentNode.removeChild(flash);
    }, 450);
  }

  function ensureFloorBallLoop() {
    if (floorRaf) return;
    var last = performance.now();
    function tick(now) {
      if (!floorBalls.length) {
        floorRaf = 0;
        return;
      }
      var dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      var floorY = window.innerHeight - MASTERBALL_SIZE - 8;
      var maxX = Math.max(0, window.innerWidth - MASTERBALL_SIZE);
      var minDist = MASTERBALL_SIZE * 0.98;
      var i;
      var j;
      var pass;

      for (i = 0; i < floorBalls.length; i++) {
        var b = floorBalls[i];
        b.vy += 1800 * dt;
        b.vx *= Math.pow(0.4, dt);
        b.x += b.vx * dt;
        b.y += b.vy * dt;

        if (b.x < 0) {
          b.x = 0;
          b.vx = Math.abs(b.vx) * 0.5;
        } else if (b.x > maxX) {
          b.x = maxX;
          b.vx = -Math.abs(b.vx) * 0.5;
        }

        if (b.y >= floorY) {
          b.y = floorY;
          if (b.vy > 0) b.vy = 0;
          if (b.pendingRelease) {
            b.pendingRelease = false;
            releaseMasterBallBusy();
          }
        }
      }

      /* Several passes so packed balls settle into stacks without overlap. */
      for (pass = 0; pass < 4; pass++) {
        for (i = 0; i < floorBalls.length; i++) {
          for (j = i + 1; j < floorBalls.length; j++) {
            var a = floorBalls[i];
            var o = floorBalls[j];
            var ax = a.x + MASTERBALL_RADIUS;
            var ay = a.y + MASTERBALL_RADIUS;
            var ox = o.x + MASTERBALL_RADIUS;
            var oy = o.y + MASTERBALL_RADIUS;
            var dx = ox - ax;
            var dy = oy - ay;
            var dist = Math.sqrt(dx * dx + dy * dy) || 0.0001;
            if (dist >= minDist) continue;
            var overlap = minDist - dist;
            var nx = dx / dist;
            var ny = dy / dist;
            a.x -= nx * overlap * 0.5;
            a.y -= ny * overlap * 0.5;
            o.x += nx * overlap * 0.5;
            o.y += ny * overlap * 0.5;

            var rvx = o.vx - a.vx;
            var rvy = o.vy - a.vy;
            var velAlong = rvx * nx + rvy * ny;
            if (velAlong < 0) {
              var impulse = velAlong * 0.5;
              a.vx += impulse * nx;
              a.vy += impulse * ny;
              o.vx -= impulse * nx;
              o.vy -= impulse * ny;
            }

            if (a.x < 0) a.x = 0;
            if (o.x < 0) o.x = 0;
            if (a.x > maxX) a.x = maxX;
            if (o.x > maxX) o.x = maxX;
            if (a.y > floorY) {
              a.y = floorY;
              if (a.vy > 0) a.vy = 0;
            }
            if (o.y > floorY) {
              o.y = floorY;
              if (o.vy > 0) o.vy = 0;
            }
          }
        }
      }

      for (i = 0; i < floorBalls.length; i++) {
        var ball = floorBalls[i];
        /* Settled on another ball (stack) also unlocks the next shot. */
        if (
          ball.pendingRelease &&
          ball.vy >= 0 &&
          Math.abs(ball.vy) < 60 &&
          ball.y < floorY - 2
        ) {
          var supported = false;
          var bcx = ball.x + MASTERBALL_RADIUS;
          var bcy = ball.y + MASTERBALL_RADIUS;
          for (j = 0; j < floorBalls.length; j++) {
            if (i === j) continue;
            var other = floorBalls[j];
            var ocx = other.x + MASTERBALL_RADIUS;
            var ocy = other.y + MASTERBALL_RADIUS;
            var ddx = bcx - ocx;
            var ddy = bcy - ocy;
            var d = Math.sqrt(ddx * ddx + ddy * ddy);
            if (d < minDist + 2 && bcy < ocy) {
              supported = true;
              break;
            }
          }
          if (supported) {
            ball.pendingRelease = false;
            releaseMasterBallBusy();
          }
        }
        ball.rot += ball.vx * dt * 2.2;
        ball.el.style.left = ball.x + "px";
        ball.el.style.top = ball.y + "px";
        ball.el.style.transform = "rotate(" + ball.rot + "deg)";
      }
      floorRaf = requestAnimationFrame(tick);
    }
    floorRaf = requestAnimationFrame(tick);
  }

  function dropMasterBallToFloor(ball, x, y, caught) {
    ball.classList.remove("is-masterball-whitened", "is-masterball-vibrating");
    ball.classList.add("is-masterball-floor");
    ball.style.pointerEvents = "auto";
    ball.style.cursor = "pointer";
    var entry = {
      el: ball,
      x: x,
      y: y,
      vx: (Math.random() - 0.5) * 140,
      vy: 60,
      rot: 0,
      pendingRelease: true,
      caught: caught || null,
      releasing: false,
    };
    floorBalls.push(entry);
    ball.addEventListener(
      "pointerdown",
      function (e) {
        e.stopPropagation();
      },
      true
    );
    ball.addEventListener(
      "click",
      function (e) {
        e.preventDefault();
        e.stopPropagation();
        releaseCaughtMasterBall(entry);
      },
      true
    );
    ensureFloorBallLoop();
  }

  function hideCaughtElement(el) {
    el.classList.remove("is-masterball-whitened", "is-masterball-catching");
    el.classList.add("is-masterball-caught");
    el.setAttribute("aria-hidden", "true");
    el.style.position = "";
    el.style.left = "";
    el.style.top = "";
    el.style.width = "";
    el.style.height = "";
    el.style.margin = "";
    el.style.transform = "";
    el.style.zIndex = "";
    el.style.transition = "";
    el.style.filter = "";
    el.style.opacity = "";
  }

  function snapshotCatchParts(els) {
    var parts = [];
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      var r = el.getBoundingClientRect();
      parts.push({
        el: el,
        left: r.left,
        top: r.top,
        width: r.width,
        height: r.height,
      });
    }
    return { parts: parts };
  }

  function liftCatchPart(part) {
    var el = part.el;
    var r = el.getBoundingClientRect();
    part.left = r.left;
    part.top = r.top;
    part.width = r.width;
    part.height = r.height;
    el.style.position = "fixed";
    el.style.left = r.left + "px";
    el.style.top = r.top + "px";
    el.style.width = r.width + "px";
    el.style.height = r.height + "px";
    el.style.margin = "0";
    el.style.zIndex = "58";
    el.style.transformOrigin = "50% 50%";
    el.style.transition = "none";
  }

  function restoreCaughtElement(caught, fromX, fromY, done) {
    var parts = caught && caught.parts ? caught.parts : null;
    if (!parts || !parts.length) {
      if (done) done();
      return;
    }

    var pending = parts.length;
    function oneDone() {
      pending -= 1;
      if (pending <= 0 && done) done();
    }

    for (var i = 0; i < parts.length; i++) {
      (function (part) {
        var el = part.el;
        if (!el || !el.isConnected) {
          oneDone();
          return;
        }
        el.classList.remove("is-masterball-caught");
        el.removeAttribute("aria-hidden");
        el.classList.add("is-masterball-whitened", "is-masterball-catching");
        el.style.position = "fixed";
        el.style.left = fromX - part.width * 0.08 + "px";
        el.style.top = fromY - part.height * 0.08 + "px";
        el.style.width = part.width + "px";
        el.style.height = part.height + "px";
        el.style.margin = "0";
        el.style.zIndex = "58";
        el.style.transformOrigin = "50% 50%";
        el.style.transition = "none";
        el.style.opacity = "0.2";
        el.style.transform = "scale(0.12)";
        void el.offsetWidth;

        var start = performance.now();
        var life = 480;
        function tick(now) {
          var t = Math.min(1, (now - start) / life);
          var e = 1 - (1 - t) * (1 - t);
          var x =
            fromX -
            part.width / 2 +
            (part.left - (fromX - part.width / 2)) * e;
          var y =
            fromY -
            part.height / 2 +
            (part.top - (fromY - part.height / 2)) * e;
          var scale = 0.12 + e * 0.88;
          var opacity = 0.2 + e * 0.8;
          el.style.left = x + "px";
          el.style.top = y + "px";
          el.style.transform = "scale(" + scale + ")";
          el.style.opacity = String(opacity);
          if (t >= 1) {
            el.classList.remove(
              "is-masterball-whitened",
              "is-masterball-catching"
            );
            el.style.position = "";
            el.style.left = "";
            el.style.top = "";
            el.style.width = "";
            el.style.height = "";
            el.style.margin = "";
            el.style.transform = "";
            el.style.zIndex = "";
            el.style.transition = "";
            el.style.filter = "";
            el.style.opacity = "";
            oneDone();
            return;
          }
          requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      })(parts[i]);
    }
  }

  function releaseCaughtMasterBall(entry) {
    if (!entry || entry.releasing || !entry.caught) return;
    entry.releasing = true;

    var idx = floorBalls.indexOf(entry);
    if (idx !== -1) floorBalls.splice(idx, 1);

    var ball = entry.el;
    var cx = entry.x + MASTERBALL_RADIUS;
    var cy = entry.y + MASTERBALL_RADIUS;
    ball.style.pointerEvents = "none";
    ball.style.transform = "";
    ball.classList.add("is-masterball-whitened", "is-masterball-vibrating");

    restoreCaughtElement(entry.caught, cx, cy, function () {});

    setTimeout(function () {
      ball.classList.remove("is-masterball-vibrating");
      spawnMasterWhiteBurst(cx, cy);
      ball.classList.remove("is-masterball-whitened");
      if (ball.parentNode) ball.parentNode.removeChild(ball);
    }, 520);
  }

  function runMasterCatch(ball, hitX, hitY, group) {
    var parts = group && group.parts ? group.parts.slice() : [];
    if (!parts.length) return;

    var size = MASTERBALL_SIZE;
    var bounceX = hitX + MASTERBALL_BOUNCE_PX;
    var stopX = hitX + MASTERBALL_BOUNCE_PX * 0.45;
    var stopY = hitY;
    var born = performance.now();
    var phase = "bounce";
    var suckStart = 0;
    var vibStart = 0;
    var i;

    for (i = 0; i < parts.length; i++) {
      parts[i].classList.add("is-masterball-catching");
    }

    var caughtSnapshot = snapshotCatchParts(parts);
    var liveParts = caughtSnapshot.parts;

    function placeBall(x, y, extraTransform) {
      ball.style.left = x - size / 2 + "px";
      ball.style.top = y - size / 2 + "px";
      ball.style.transform = extraTransform || "";
    }

    placeBall(hitX, hitY);

    function tick(now) {
      var t = now - born;

      if (phase === "bounce") {
        var u = Math.min(1, t / 220);
        var ease = 1 - (1 - u) * (1 - u);
        var bx = hitX + (bounceX - hitX) * ease;
        var by = hitY;
        if (u >= 1) {
          var u2 = Math.min(1, (t - 220) / 160);
          var e2 = u2 * u2;
          bx = bounceX + (stopX - bounceX) * e2;
          if (u2 >= 1) {
            phase = "whiten";
            born = now;
            placeBall(stopX, stopY);
            ball.classList.add("is-masterball-whitened");
            for (i = 0; i < parts.length; i++) {
              parts[i].classList.add("is-masterball-whitened");
            }
            requestAnimationFrame(tick);
            return;
          }
        }
        placeBall(bx, by);
        requestAnimationFrame(tick);
        return;
      }

      if (phase === "whiten") {
        if (now - born >= 180) {
          phase = "suck";
          suckStart = now;
          for (i = 0; i < liveParts.length; i++) {
            liftCatchPart(liveParts[i]);
          }
          placeBall(stopX, stopY);
        }
        requestAnimationFrame(tick);
        return;
      }

      if (phase === "suck") {
        var st = Math.min(1, (now - suckStart) / 480);
        var se = st * st;
        var scale = 1 - se * 0.92;
        var opacity = 1 - se * 0.85;
        for (i = 0; i < liveParts.length; i++) {
          var part = liveParts[i];
          var tx = part.left + (stopX - part.width / 2 - part.left) * se;
          var ty = part.top + (stopY - part.height / 2 - part.top) * se;
          part.el.style.left = tx + "px";
          part.el.style.top = ty + "px";
          part.el.style.transform = "scale(" + scale + ")";
          part.el.style.opacity = String(opacity);
        }
        placeBall(stopX, stopY);
        if (st >= 1) {
          for (i = 0; i < liveParts.length; i++) {
            hideCaughtElement(liveParts[i].el);
          }
          phase = "vibrate";
          vibStart = now;
          ball.classList.add("is-masterball-vibrating");
        }
        requestAnimationFrame(tick);
        return;
      }

      if (phase === "vibrate") {
        var vt = now - vibStart;
        if (vt >= 520) {
          ball.classList.remove(
            "is-masterball-vibrating",
            "is-masterball-whitened"
          );
          spawnMasterWhiteBurst(stopX, stopY);
          placeBall(stopX, stopY);
          dropMasterBallToFloor(
            ball,
            stopX - size / 2,
            stopY - size / 2,
            caughtSnapshot
          );
          return;
        }
        requestAnimationFrame(tick);
        return;
      }
    }
    requestAnimationFrame(tick);
  }

  function spawnMasterBall() {
    if (masterBallBusy || !canMasterCatch) return;
    masterBallBusy = true;

    var c = followerCenter();
    var originX = c.cx - (img.offsetWidth || 40) * 0.15;
    var originY = c.cy;
    var angle = MASTERBALL_ANGLE + (Math.random() - 0.5) * 0.08;
    var speed = MASTERBALL_SPEED * (0.94 + Math.random() * 0.12);
    var vx = Math.cos(angle) * speed;
    var vy = Math.sin(angle) * speed;

    var ball = document.createElement("img");
    ball.className = "cursor-burst cursor-burst--masterball";
    ball.alt = "";
    ball.draggable = false;
    ball.src = burstSrc;
    ball.style.width = MASTERBALL_SIZE + "px";
    ball.style.height = "auto";
    ball.style.left = originX - MASTERBALL_SIZE / 2 + "px";
    ball.style.top = originY - MASTERBALL_SIZE / 2 + "px";
    document.body.appendChild(ball);

    var born = performance.now();
    var lastHitAt = 0;
    var alive = true;

    function removeBall() {
      alive = false;
      if (ball.parentNode) ball.parentNode.removeChild(ball);
      releaseMasterBallBusy();
    }

    function tick(now) {
      if (!alive) return;
      var elapsedMs = now - born;
      var elapsed = elapsedMs / 1000;
      var curX = originX + vx * elapsed;
      var curY = originY + vy * elapsed;
      var spin = elapsed * 360;

      if (
        curX < -80 ||
        curY < -80 ||
        curX > window.innerWidth + 80 ||
        curY > window.innerHeight + 80
      ) {
        removeBall();
        return;
      }

      ball.style.left = curX - MASTERBALL_SIZE / 2 + "px";
      ball.style.top = curY - MASTERBALL_SIZE / 2 + "px";
      ball.style.transform = "rotate(" + spin + "deg)";

      if (
        elapsedMs >= MASTERBALL_ARM_MS &&
        now - lastHitAt >= MASTERBALL_HIT_MS
      ) {
        lastHitAt = now;
        var target = tryMasterHitAt(curX, curY);
        if (target) {
          alive = false;
          ball.style.transform = "";
          /* Busy stays true until this catch lands on the floor. */
          runMasterCatch(ball, curX, curY, target);
          return;
        }
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  function startMasterCatch() {
    if (masterCatching || !canMasterCatch) return;
    masterCatching = true;
    if (!masterBallBusy) spawnMasterBall();
  }

  function stopMasterCatch() {
    if (masterCatchInterval) {
      clearTimeout(masterCatchInterval);
      masterCatchInterval = 0;
    }
    masterCatching = false;
  }
  /* ---------------------------------------------------------------------- */

  function syncBreath() {
    if (mouseBreathReady || aKeyBreathReady) {
      if (canBreath) startBreath();
      if (canHoldBurst) startHoldBurst();
      if (canLeafSpin) startLeafSpin();
      if (canWaterBlob) startWaterBlob();
      if (canMasterCatch) startMasterCatch();
    } else {
      stopBreathStream();
      stopHoldBurst();
      stopLeafSpin();
      stopWaterBlob();
      stopMasterCatch();
    }
  }

  function clearMouseBreathHold() {
    mouseBreathReady = false;
    if (mouseBreathTimer) {
      clearTimeout(mouseBreathTimer);
      mouseBreathTimer = 0;
    }
  }

  function clearAKeyBreathHold() {
    aKeyHeld = false;
    aKeyBreathReady = false;
    if (aKeyBreathTimer) {
      clearTimeout(aKeyBreathTimer);
      aKeyBreathTimer = 0;
    }
  }

  function stopBreath() {
    clearMouseBreathHold();
    clearAKeyBreathHold();
    stopBreathStream();
    stopHoldBurst();
    stopLeafSpin();
    stopWaterBlob();
    stopMasterCatch();
  }

  function isBreathAKey(e) {
    return e.code === "KeyA" || e.key === "a" || e.key === "A";
  }

  /* --- Hold-to-evolve (weighted outcomes: e.g. Charmander / Charizard / Mega X) --- */
  var pressStart = 0;
  var pressX = 0;
  var pressY = 0;
  var charging = false;
  var chargeTimer = 0;

  function startChargeFlash() {
    if (charging || evolved || !canEvolve) return;
    charging = true;
    img.classList.add("is-charging");
  }

  function stopChargeFlash() {
    if (!charging) return;
    charging = false;
    img.classList.remove("is-charging");
    if (chargeTimer) {
      clearTimeout(chargeTimer);
      chargeTimer = 0;
    }
  }

  function evolveFollower(cx, cy) {
    if (evolved || !canEvolve) return;
    var outcome = pickEvolveOutcome(pick.evolveOutcomes);
    if (!outcome || !outcome.src) return;
    evolved = true;
    stopChargeFlash();
    img.src = outcome.src;
    img.classList.add("is-evolved");
    if (outcome.evolvedXxl) img.classList.add("is-evolved-xxl");
    else if (outcome.evolvedXl) img.classList.add("is-evolved-xl");
    if (outcome.burst) burstSrc = outcome.burst;
    evolveBurstFlash = !!outcome.burstFlash;
    canBreath = !!outcome.breathFire;
    canHoldBurst = !!outcome.holdBurst;
    canLeafSpin = !!outcome.leafSpin;
    canWaterBlob = !!outcome.waterBlob;
    canMasterCatch = !!outcome.masterCatch;
    breathRangeScale = outcome.breathRangeScale != null ? outcome.breathRangeScale : 1;
    spawnBurst(cx, cy);
  }

  function cancelPress() {
    pressStart = 0;
    stopChargeFlash();
    clearMouseBreathHold();
    syncBreath();
  }

  if (canEvolve) {
    document.addEventListener(
      "pointerdown",
      function (e) {
        if (e.button !== 0) return;
        /* Evolved skill forms: hold 1s -> breath stream or radial burst. */
        if (evolved && hasHoldSkill()) {
          pressStart = performance.now();
          clearMouseBreathHold();
          syncBreath();
          mouseBreathTimer = setTimeout(function () {
            mouseBreathTimer = 0;
            if (pressStart) {
              mouseBreathReady = true;
              syncBreath();
            }
          }, BREATH_HOLD_MS);
          return;
        }
        /* Other evolved forms: click burst only. */
        if (evolved) {
          spawnBurst(e.clientX, e.clientY);
          return;
        }
        pressStart = performance.now();
        pressX = e.clientX;
        pressY = e.clientY;
        /* White glow only after full hold — signals ready to evolve. */
        chargeTimer = setTimeout(function () {
          chargeTimer = 0;
          if (pressStart && !evolved) startChargeFlash();
        }, pick.evolveHoldMs);
      },
      { passive: true }
    );

    document.addEventListener(
      "pointerup",
      function (e) {
        if (e.button !== 0 || !pressStart) return;
        var held = performance.now() - pressStart;
        var cx = e.clientX;
        var cy = e.clientY;
        pressStart = 0;

        /* Skill forms: release mouse; skill continues if A is still past 1s. */
        if (evolved && hasHoldSkill()) {
          var wasMouseBreath = mouseBreathReady;
          clearMouseBreathHold();
          syncBreath();
          if (!wasMouseBreath && !aKeyBreathReady && held < SHORT_CLICK_MS) {
            spawnBurst(cx, cy);
          }
          return;
        }

        stopChargeFlash();
        if (evolved) return;
        if (held >= pick.evolveHoldMs) {
          evolveFollower(cx, cy);
          return;
        }
        /* Short click: pre-evolve burst (leaf / fire / lightning / ball). */
        if (held < SHORT_CLICK_MS) spawnBurst(cx, cy);
      },
      { passive: true }
    );

    document.addEventListener(
      "pointercancel",
      function () {
        cancelPress();
      },
      { passive: true }
    );

    window.addEventListener(
      "blur",
      function () {
        cancelPress();
        clearAKeyBreathHold();
        syncBreath();
      },
      { passive: true }
    );

    /* Skill forms: hold A >=1s -> breath / radial burst; ignored while typing. */
    document.addEventListener("keydown", function (e) {
      if (!evolved || !hasHoldSkill() || !isBreathAKey(e) || e.repeat) return;
      if (isTypingFocus(e.target) || isTypingFocus(document.activeElement)) return;
      if (aKeyHeld) return;
      aKeyHeld = true;
      aKeyBreathReady = false;
      aKeyBreathTimer = setTimeout(function () {
        aKeyBreathTimer = 0;
        if (aKeyHeld) {
          aKeyBreathReady = true;
          syncBreath();
        }
      }, BREATH_HOLD_MS);
    });

    document.addEventListener("keyup", function (e) {
      if (!isBreathAKey(e)) return;
      clearAKeyBreathHold();
      syncBreath();
    });
  } else {
    document.addEventListener(
      "pointerdown",
      function (e) {
        if (e.button !== 0) return;
        spawnBurst(e.clientX, e.clientY);
      },
      { passive: true }
    );
  }
})();
