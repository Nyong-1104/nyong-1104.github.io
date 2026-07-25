/** Pixel sprite that follows the mouse (fine pointer only) + click burst particles. */
(function () {
  var FOLLOWERS = [
    {
      src: "./assets/cursor-follower-bulbasaur.png",
      burst: "./assets/cursor-burst-leaf.png",
    },
    {
      src: "./assets/cursor-follower-pokeball.png",
      burst: "./assets/cursor-burst-ball.png",
    },
    {
      src: "./assets/cursor-follower-charmander.png",
      burst: "./assets/cursor-burst-fire.png",
    },
    {
      src: "./assets/cursor-follower-squirtle.png",
      burst: "./assets/cursor-burst-water.png",
    },
    {
      src: "./assets/cursor-follower-pikachu.png",
      burst: "./assets/cursor-burst-lightning.png",
      evolveSrc: "./assets/cursor-follower-raichu.png",
      evolveHoldMs: 3000,
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
  var RAICHU_BURST_SCALE = 1.95;
  var SHORT_CLICK_MS = 400;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!window.matchMedia("(pointer: fine)").matches) return;

  var pick = FOLLOWERS[Math.floor(Math.random() * FOLLOWERS.length)];
  var burstSrc = pick.burst;
  var canEvolve = !!pick.evolveSrc;
  var evolved = false;

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
    var raichuBurst = evolved;
    for (var i = 0; i < count; i++) {
      var p = document.createElement("img");
      p.className = raichuBurst
        ? "cursor-burst cursor-burst--raichu"
        : "cursor-burst";
      p.alt = "";
      p.draggable = false;
      p.src = burstSrc;
      var size = SIZE_MIN + Math.random() * (SIZE_MAX - SIZE_MIN);
      if (raichuBurst) size *= RAICHU_BURST_SCALE;
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

  /* --- Pikachu → Raichu hold-to-evolve --- */
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

  function evolveToRaichu(cx, cy) {
    if (evolved || !canEvolve) return;
    evolved = true;
    stopChargeFlash();
    img.src = pick.evolveSrc;
    img.classList.add("is-evolved");
    spawnBurst(cx, cy);
  }

  function cancelPress() {
    pressStart = 0;
    stopChargeFlash();
  }

  if (canEvolve) {
    document.addEventListener(
      "pointerdown",
      function (e) {
        if (e.button !== 0) return;
        /* After evolve, Raichu clicks still fire lightning bursts. */
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
        stopChargeFlash();
        if (evolved) return;
        if (held >= pick.evolveHoldMs) {
          evolveToRaichu(cx, cy);
          return;
        }
        /* Short click: same burst as non-Pikachu followers. */
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
      },
      { passive: true }
    );
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
