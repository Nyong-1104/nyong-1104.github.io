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
          burstFlash: true,
          evolvedXl: true,
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
        },
        {
          weight: 30,
          src: "./assets/cursor-follower-mega-charizard-x.png",
          burst: "./assets/cursor-burst-bluefire.png",
          burstFlash: true,
          evolvedXxl: true,
          breathFire: true,
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
          burstFlash: true,
          evolvedXl: true,
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
          burstFlash: true,
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
  var breathing = false;
  var breathInterval = 0;
  /* Breath stays on while mouse OR A has been held past BREATH_HOLD_MS. */
  var mouseBreathReady = false;
  var aKeyBreathReady = false;
  var mouseBreathTimer = 0;
  var aKeyBreathTimer = 0;
  var aKeyHeld = false;

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

  /* --- Mega Charizard X hold-breath (blue fire stream after 1s hold) --- */
  function spawnBreathParticle() {
    /* Mouth sits near the left-center of the left-facing Mega X sprite. */
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
    var speed = BREATH_SPEED_MIN + Math.random() * (BREATH_SPEED_MAX - BREATH_SPEED_MIN);
    var vx = Math.cos(angle) * speed;
    var vy = Math.sin(angle) * speed;
    var life = BREATH_LIFE_MIN + Math.random() * (BREATH_LIFE_MAX - BREATH_LIFE_MIN);
    var rot = (Math.random() - 0.5) * 360;
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
        requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    })(p, vx, vy, life, rot, start);
  }

  function isTypingFocus(el) {
    if (!el || el === document.body || el === document.documentElement) return false;
    var tag = el.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
    if (el.isContentEditable) return true;
    return false;
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

  function syncBreath() {
    if (mouseBreathReady || aKeyBreathReady) startBreath();
    else stopBreathStream();
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
        /* Mega X: hold 1s → continuous blue-fire breath (no evolve charge). */
        if (evolved && canBreath) {
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

        /* Mega X: release mouse; breath continues if A is still past 1s. */
        if (evolved && canBreath) {
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

    /* Mega X: hold A ≥1s → same breath; ignored while typing in form fields. */
    document.addEventListener("keydown", function (e) {
      if (!evolved || !canBreath || !isBreathAKey(e) || e.repeat) return;
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
