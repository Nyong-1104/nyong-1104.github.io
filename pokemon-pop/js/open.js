/**
 * Pack-open tester — freehand tear path, then flip 1-of-25 promo card.
 */
(function () {
  const PT = window.PopTracker;
  const PACK_ID = "s8a-p-25th-anniversary";

  /**
   * Tearable range — fractions of pack height/width (0~1).
   * Tune here; CSS hit-area follows via applyTearConfig().
   *
   *  yMin/yMax : vertical band you can draw in
   *  ratio     : default sealed cut line (between yMin~yMax)
   *  edgeLeft/Right : stroke must reach both sides to open
   */
  const TEAR = {
    ratio: 0.21,
    yMin: 0.17,
    yMax: 0.26,
    edgeLeft: 0.05,
    edgeRight: 0.95,
    minPoints: 10,
    sampleDist: 0.01,
  };

  const packEl = document.getElementById("pack");
  const packInner = document.getElementById("pack-inner");
  const tearZone = document.getElementById("tear-zone");
  const tearPolyTop = document.getElementById("tear-poly-top");
  const tearPolyBody = document.getElementById("tear-poly-body");
  const tearStroke = document.getElementById("tear-stroke");
  const openFxSeam = document.getElementById("open-fx-seam-path");
  const openFxFanFill = document.getElementById("open-fx-fan-fill");
  const openFxFanRays = document.getElementById("open-fx-fan-rays");
  const openFxAbovePoly = document.getElementById("open-fx-above-poly");
  const hintEl = document.getElementById("open-hint");
  const openInfo = document.getElementById("open-info");
  const cardRise = document.getElementById("card-rise");
  const revealBtn = document.getElementById("reveal-card");
  const revealInner = document.getElementById("reveal-inner");
  const revealFront = document.getElementById("reveal-front");
  const resultEl = document.getElementById("open-result");
  const resultName = document.getElementById("result-name");
  const resultMeta = document.getElementById("result-meta");
  const resultPrice = document.getElementById("result-price");
  const btnReset = document.getElementById("btn-reset");

  let pack = null;
  let pool = [];
  let drawn = null;
  let tear = 0;
  let dragging = false;
  let torn = false;
  let glowAliveRaf = 0;
  let glowAlivePhase = 0;
  /** @type {'back'|'front'} */
  let cardFacing = "back";
  let faceRevealed = false;
  let flipBusy = false;
  /** @type {null|{pointerId:number,startX:number,startY:number,horizontal:boolean,dx:number}} */
  let flipDrag = null;
  /** @type {{x:number,y:number,rawX?:number,rawY?:number}[]} */
  let points = [];
  const strokeCtx = tearStroke.getContext("2d");

  function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
  }

  /** Push TEAR numbers into CSS so zone/clip/glow stay in sync. */
  function applyTearConfig() {
    packEl.style.setProperty("--top-ratio", String(TEAR.ratio));
    packEl.style.setProperty("--tear-y-min", String(TEAR.yMin));
    packEl.style.setProperty("--tear-y-max", String(TEAR.yMax));
    tearZone.style.top = TEAR.yMin * 100 + "%";
    tearZone.style.height = (TEAR.yMax - TEAR.yMin) * 100 + "%";
  }

  function setTear(value) {
    tear = clamp(value, 0, 1);
    packEl.style.setProperty("--tear", String(tear));
    const shake = Math.sin(tear * Math.PI * 10) * tear * 1.4;
    packEl.style.setProperty("--shake", `${shake}px`);
    tearZone.setAttribute("aria-valuenow", String(Math.round(tear * 100)));
  }

  function stopGlowAlive() {
    if (glowAliveRaf) {
      cancelAnimationFrame(glowAliveRaf);
      glowAliveRaf = 0;
    }
    packEl.style.setProperty("--glow-alive", "0");
  }

  function pumpGlowAlive() {
    if (packEl.dataset.state !== "drawing") {
      glowAliveRaf = 0;
      packEl.style.setProperty("--glow-alive", "0");
      return;
    }
    glowAlivePhase += 0.08;
    packEl.style.setProperty("--glow-alive", String(Math.sin(glowAlivePhase) * 0.012));
    glowAliveRaf = requestAnimationFrame(pumpGlowAlive);
  }

  function startGlowAlive() {
    if (glowAliveRaf) return;
    glowAlivePhase = 0;
    glowAliveRaf = requestAnimationFrame(pumpGlowAlive);
  }

  function setState(state) {
    packEl.dataset.state = state;
    if (state === "drawing") startGlowAlive();
    else stopGlowAlive();
  }

  function resetClip() {
    const y = TEAR.ratio.toFixed(4);
    tearPolyTop.setAttribute("points", `0,0 1,0 1,${y} 0,${y}`);
    tearPolyBody.setAttribute("points", `0,${y} 1,${y} 1,1 0,1`);
    syncOpenFx(null);
  }

  function packPointFromEvent(e) {
    const rect = packInner.getBoundingClientRect();
    const rawX = (e.clientX - rect.left) / rect.width;
    const rawY = (e.clientY - rect.top) / rect.height;
    return {
      x: clamp(rawX, 0, 1),
      y: clamp(rawY, TEAR.yMin, TEAR.yMax),
      rawX: rawX,
      rawY: rawY,
    };
  }

  function dist(a, b) {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function strokeBounds() {
    if (points.length < 2) return { minX: 1, maxX: 0, coverage: 0, minRaw: 1, maxRaw: 0 };
    let minX = 1;
    let maxX = 0;
    let minRaw = Infinity;
    let maxRaw = -Infinity;
    for (let i = 0; i < points.length; i++) {
      minX = Math.min(minX, points[i].x);
      maxX = Math.max(maxX, points[i].x);
      const rx = points[i].rawX != null ? points[i].rawX : points[i].x;
      minRaw = Math.min(minRaw, rx);
      maxRaw = Math.max(maxRaw, rx);
    }
    return {
      minX: minX,
      maxX: maxX,
      coverage: Math.max(0, maxX - minX),
      minRaw: minRaw,
      maxRaw: maxRaw,
    };
  }

  function isStrokeComplete() {
    if (points.length < TEAR.minPoints) return false;
    const b = strokeBounds();
    return b.minRaw <= TEAR.edgeLeft && b.maxRaw >= TEAR.edgeRight;
  }

  function coverage() {
    return strokeBounds().coverage;
  }

  /* Glow follows finger: can grow and shrink when reversing (bbox coverage cannot). */
  function liveTearProgress() {
    if (!points.length) return 0;
    const first = points[0];
    const last = points[points.length - 1];
    return clamp(last.x - first.x, 0, 1);
  }

  function edgePath() {
    if (points.length < 2) return [];

    let path = points.map(function (p) {
      return { x: p.x, y: p.y };
    });
    if (path[path.length - 1].x < path[0].x) {
      path = path.slice().reverse();
    }

    const mono = [{ x: path[0].x, y: path[0].y }];
    for (let i = 1; i < path.length; i++) {
      const prev = mono[mono.length - 1];
      const cur = path[i];
      if (cur.x > prev.x + 0.0008) {
        mono.push({ x: cur.x, y: cur.y });
      } else if (cur.x >= prev.x) {
        mono[mono.length - 1] = { x: cur.x, y: cur.y };
      }
    }

    if (mono.length < 2) return mono;

    const out = [];
    const first = mono[0];
    const last = mono[mono.length - 1];

    if (first.x > 0.002) out.push({ x: 0, y: clamp(first.y, TEAR.yMin, TEAR.yMax) });
    for (let i = 0; i < mono.length; i++) {
      out.push({
        x: clamp(mono[i].x, 0, 1),
        y: clamp(mono[i].y, TEAR.yMin, TEAR.yMax),
      });
    }
    if (last.x < 0.998) out.push({ x: 1, y: clamp(last.y, TEAR.yMin, TEAR.yMax) });

    return out;
  }

  function updateClip() {
    if (points.length < 2) {
      resetClip();
      syncOpenFx(null);
      return;
    }
    const edge = edgePath();
    if (!edge.length) {
      resetClip();
      syncOpenFx(null);
      return;
    }
    const left = edge[0];
    const right = edge[edge.length - 1];

    const topParts = ["0,0", "1,0", `1,${right.y.toFixed(4)}`];
    for (let i = edge.length - 1; i >= 0; i--) {
      topParts.push(`${edge[i].x.toFixed(4)},${edge[i].y.toFixed(4)}`);
    }
    topParts.push(`0,${left.y.toFixed(4)}`);
    tearPolyTop.setAttribute("points", topParts.join(" "));

    const bodyParts = [`0,${left.y.toFixed(4)}`];
    for (let i = 0; i < edge.length; i++) {
      bodyParts.push(`${edge[i].x.toFixed(4)},${edge[i].y.toFixed(4)}`);
    }
    bodyParts.push(`1,${right.y.toFixed(4)}`, "1,1", "0,1");
    tearPolyBody.setAttribute("points", bodyParts.join(" "));

    syncOpenFx(edge, topParts.join(" "));
  }

  /** PC open FX: seam along cut + upward fan bloom clipped above the tear. */
  function syncOpenFx(edge, abovePoints) {
    if (!openFxSeam || !openFxFanFill || !openFxFanRays || !openFxAbovePoly) return;

    const y = TEAR.ratio;
    const fallbackEdge = [
      { x: 0, y: y },
      { x: 0.5, y: y },
      { x: 1, y: y },
    ];
    const src = edge && edge.length >= 2 ? edge : fallbackEdge;

    const seamD =
      "M " +
      src
        .map(function (p) {
          return p.x.toFixed(4) + " " + p.y.toFixed(4);
        })
        .join(" L ");
    openFxSeam.setAttribute("d", seamD);

    // Fan fill: tear edge → flared arc above (부채꼴)
    const fill = [];
    for (let i = 0; i < src.length; i++) fill.push(src[i]);
    for (let i = src.length - 1; i >= 0; i--) {
      const p = src[i];
      const t = src.length <= 1 ? 0.5 : i / (src.length - 1);
      const lift = Math.sin(t * Math.PI); // taller near center
      const outward = (p.x - 0.5) * (0.22 + 0.45 * lift);
      fill.push({
        x: clamp(p.x + outward, -0.08, 1.08),
        y: clamp(p.y - (0.06 + 0.16 * lift), 0, 1),
      });
    }
    openFxFanFill.setAttribute(
      "points",
      fill
        .map(function (p) {
          return p.x.toFixed(4) + "," + p.y.toFixed(4);
        })
        .join(" ")
    );

    // Soft rays from seam samples, fanning upward
    const rayParts = [];
    const sampleStep = Math.max(1, Math.floor(src.length / 7));
    for (let i = 0; i < src.length; i += sampleStep) {
      const p = src[i];
      const t = src.length <= 1 ? 0.5 : i / (src.length - 1);
      const angles = [-0.95, -0.55, -0.2, 0.2, 0.55, 0.95]; // radians from vertical
      for (let a = 0; a < angles.length; a++) {
        const ang = angles[a];
        const len = 0.07 + 0.11 * Math.sin(t * Math.PI) * (0.65 + (a % 2) * 0.35);
        const ex = p.x + Math.sin(ang) * len;
        const ey = p.y - Math.cos(ang) * len;
        rayParts.push(
          "M " +
            p.x.toFixed(4) +
            " " +
            p.y.toFixed(4) +
            " L " +
            clamp(ex, -0.1, 1.1).toFixed(4) +
            " " +
            clamp(ey, 0, 1).toFixed(4)
        );
      }
    }
    openFxFanRays.setAttribute("d", rayParts.join(" "));

    if (abovePoints) {
      openFxAbovePoly.setAttribute("points", abovePoints);
    } else {
      const yy = y.toFixed(4);
      openFxAbovePoly.setAttribute("points", `0,0 1,0 1,${yy} 0,${yy}`);
    }
  }

  function sizeCanvas() {
    const rect = packInner.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(1, Math.round(rect.width * dpr));
    const h = Math.max(1, Math.round(rect.height * dpr));
    if (tearStroke.width !== w || tearStroke.height !== h) {
      tearStroke.width = w;
      tearStroke.height = h;
    }
    return { w: rect.width, h: rect.height, dpr: dpr };
  }

  function drawStroke() {
    const size = sizeCanvas();
    const ctx = strokeCtx;
    ctx.setTransform(size.dpr, 0, 0, size.dpr, 0, 0);
    ctx.clearRect(0, 0, size.w, size.h);
    if (points.length < 2) return;

    const ordered = points;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";

    function strokePath(width, color) {
      ctx.beginPath();
      ctx.moveTo(ordered[0].x * size.w, ordered[0].y * size.h);
      for (let i = 1; i < ordered.length; i++) {
        ctx.lineTo(ordered[i].x * size.w, ordered[i].y * size.h);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.stroke();
    }

    strokePath(14, "rgba(255, 200, 100, 0.35)");
    strokePath(8, "rgba(255, 230, 150, 0.55)");
    strokePath(4, "rgba(255, 248, 220, 0.9)");
    strokePath(1.6, "rgba(255, 255, 255, 0.95)");

    ctx.fillStyle = "rgba(255, 250, 220, 0.95)";
    for (let i = 0; i < ordered.length; i += 1) {
      const p = ordered[i];
      const spark = 0.7 + (i % 4) * 0.35;
      ctx.beginPath();
      ctx.arc(
        p.x * size.w + Math.sin(i * 3.1) * 2.2,
        p.y * size.h + Math.cos(i * 2.4) * 1.8,
        spark,
        0,
        Math.PI * 2
      );
      ctx.fill();
    }
  }

  function refreshStrokeOnly() {
    setTear(liveTearProgress());
    drawStroke();
  }

  function openAlongPath() {
    if (torn) return;
    updateClip();
    setState("splitting");
    window.setTimeout(function () {
      completeTear();
    }, 520);
  }

  function pickCard() {
    if (!pool.length) return null;
    return pool[Math.floor(Math.random() * pool.length)];
  }

  function cardImage(card) {
    return (card.images && (card.images.jp || card.images.kr)) || card.image || "";
  }

  function mountFront(card) {
    revealFront.innerHTML = "";
    const holo = PT.createHoloCardEl({
      name: PT.cardName ? PT.cardName(card) : card.nameKo || card.nameEn || "",
      image: cardImage(card),
      holoStyle: PT.resolveHoloStyle ? PT.resolveHoloStyle(card) : card.holoStyle || "holo",
    });
    revealFront.appendChild(holo);
    PT.mountHoloCard(holo);
  }

  function completeTear() {
    if (torn) return;
    torn = true;
    dragging = false;
    setTear(1);
    setState("torn");

    drawn = pickCard();
    if (!drawn) {
      hintEl.textContent = "카드 풀을 찾지 못했어요";
      return;
    }

    mountFront(drawn);
    cardRise.hidden = false;
    cardFacing = "back";
    faceRevealed = false;
    flipBusy = false;
    revealBtn.classList.remove("is-flipped", "is-dragging");
    revealInner.style.transform = "";
    hintEl.textContent = "";

    window.setTimeout(function () {
      if (packEl.dataset.state === "torn") setState("revealed");
    }, 1600);
  }

  function onPointerDown(e) {
    if (torn) return;
    dragging = true;
    points = [];
    resetClip();
    setState("drawing");
    try {
      tearZone.setPointerCapture(e.pointerId);
    } catch (_) {}
    points.push(packPointFromEvent(e));
    refreshStrokeOnly();
  }

  function onPointerMove(e) {
    if (!dragging || torn) return;
    const p = packPointFromEvent(e);
    const last = points[points.length - 1];
    if (!last || dist(last, p) >= TEAR.sampleDist || Math.abs((last.rawX || 0) - p.rawX) >= TEAR.sampleDist) {
      points.push(p);
      refreshStrokeOnly();
    }
  }

  function onPointerUp(e) {
    if (!dragging) return;
    dragging = false;
    try {
      tearZone.releasePointerCapture(e.pointerId);
    } catch (_) {}
    if (torn) return;

    setTear(coverage());
    drawStroke();

    if (isStrokeComplete()) {
      openAlongPath();
      return;
    }

    points = [];
    resetClip();
    drawStroke();
    setTear(0);
    setState("sealed");
    hintEl.textContent = "왼쪽 끝에서 오른쪽 끝까지 그어주세요";
    window.setTimeout(function () {
      if (!torn && packEl.dataset.state === "sealed") {
        hintEl.textContent = "팩을 그어 개봉해주세요";
      }
    }, 1400);
  }

  function cardAvgPrice(card) {
    const langs = PT.LANG_ORDER || ["jp", "kr", "en"];
    for (let i = 0; i < langs.length; i++) {
      const price = card.variants && card.variants[langs[i]] && card.variants[langs[i]].price;
      if (!PT.isLivePrice || !PT.isLivePrice(price)) continue;
      const grades = PT.PRICE_GRADES || ["10", "9", "8"];
      for (let g = 0; g < grades.length; g++) {
        const stats = PT.priceRangeForGrade(price, grades[g]);
        if (stats && stats.avg != null) {
          return {
            amount: stats.avg,
            currency: price.currency || "USD",
            grade: grades[g],
            lang: langs[i],
          };
        }
      }
    }
    return null;
  }

  function showResult() {
    if (!drawn) return;
    const name = PT.cardName ? PT.cardName(drawn) : drawn.nameKo || drawn.nameEn || "";
    resultName.textContent = name;
    resultMeta.textContent = `${drawn.number || ""} · ${drawn.rarity || "PROMO"}`;

    const avg = cardAvgPrice(drawn);
    if (avg) {
      const money = PT.formatMoney(avg.amount, avg.currency);
      const langLabel = PT.langLabel ? PT.langLabel(avg.lang) : String(avg.lang || "").toUpperCase();
      resultPrice.textContent = `평균 시세 ${money} · PSA ${avg.grade} (${langLabel})`;
    } else {
      resultPrice.textContent = "평균 시세 —";
    }

    resultEl.classList.add("is-visible");
    resultEl.setAttribute("aria-hidden", "false");
    if (openInfo) openInfo.classList.add("has-result");
    btnReset.hidden = false;
  }

  function flipBaseAngle() {
    return cardFacing === "front" ? 180 : 0;
  }

  function flipRelFromDx(dx) {
    const width = Math.max(revealBtn.offsetWidth, 1);
    return clamp((dx / width) * 180, -180, 180);
  }

  function shortestToward(from, to) {
    let start = from;
    while (start - to > 180) start -= 360;
    while (to - start > 180) start += 360;
    return start;
  }

  function commitFacing(face) {
    cardFacing = face;
    revealBtn.classList.toggle("is-flipped", face === "front");
    if (face === "front") {
      faceRevealed = true;
      setState("flipped");
      showResult();
    }
  }

  function clearInlineFlipTransform() {
    revealInner.style.transition = "none";
    revealInner.style.transform = "";
    void revealInner.offsetWidth;
    revealInner.style.transition = "";
    flipBusy = false;
  }

  /**
   * One flip with velocity-based overshoot bounce, then settle.
   * @param {number} fromAngle
   * @param {'back'|'front'} nextFace
   * @param {number} vx pointer velocity px/ms (sign = drag direction)
   */
  function finishFlipOnce(fromAngle, nextFace, vx) {
    flipBusy = true;
    const target = nextFace === "front" ? 180 : 0;
    const start = shortestToward(fromAngle, target);
    const dir = target >= start ? 1 : -1;

    // speed → overshoot degrees (gentle flick = small bounce, hard throw = more)
    const width = Math.max(revealBtn.offsetWidth, 1);
    const speed = Math.abs(vx || 0); // px/ms
    const throwBoost = clamp(speed * (180 / width) * 14, 0, 22);
    const overshoot = clamp(6 + throwBoost, 6, 28) * dir;
    const peak = target + overshoot;

    const throwMs = Math.round(clamp(300 - throwBoost * 4, 180, 300));
    const settleMs = 420;

    revealInner.style.transition = "none";
    revealInner.style.transform = `rotateY(${start}deg)`;

    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        // fling past the resting angle
        revealInner.style.transition =
          "transform " + throwMs + "ms cubic-bezier(0.15, 0.85, 0.25, 1)";
        revealInner.style.transform = `rotateY(${peak}deg)`;
        commitFacing(nextFace);

        window.setTimeout(function () {
          // spring back into place
          revealInner.style.transition =
            "transform " + settleMs + "ms cubic-bezier(0.34, 1.55, 0.64, 1)";
          revealInner.style.transform = `rotateY(${target}deg)`;

          window.setTimeout(clearInlineFlipTransform, settleMs + 20);
        }, throwMs);
      });
    });
  }

  function onCardPointerDown(e) {
    if (!drawn || cardRise.hidden || !torn || flipBusy) return;
    if (packEl.dataset.state === "torn") return;
    const now = performance.now();
    flipDrag = {
      pointerId: e.pointerId,
      startX: e.clientX,
      startY: e.clientY,
      horizontal: false,
      dx: 0,
      lastX: e.clientX,
      lastT: now,
      vx: 0,
    };
    try {
      revealBtn.setPointerCapture(e.pointerId);
    } catch (_) {}
  }

  function onCardPointerMove(e) {
    if (!flipDrag || e.pointerId !== flipDrag.pointerId || flipBusy) return;
    const dx = e.clientX - flipDrag.startX;
    const dy = e.clientY - flipDrag.startY;
    flipDrag.dx = dx;

    const now = performance.now();
    const dt = Math.max(now - flipDrag.lastT, 1);
    const instVx = (e.clientX - flipDrag.lastX) / dt;
    flipDrag.vx = flipDrag.vx * 0.55 + instVx * 0.45;
    flipDrag.lastX = e.clientX;
    flipDrag.lastT = now;

    if (!flipDrag.horizontal) {
      if (Math.abs(dx) < 10 && Math.abs(dy) < 10) return;
      if (Math.abs(dx) <= Math.abs(dy)) return;
      flipDrag.horizontal = true;
      revealBtn.classList.add("is-dragging");
    }

    e.preventDefault();
    revealInner.style.transform = `rotateY(${flipBaseAngle() + flipRelFromDx(dx)}deg)`;
  }

  function onCardPointerUp(e) {
    if (!flipDrag || e.pointerId !== flipDrag.pointerId) return;
    const dx = flipDrag.dx;
    const vx = flipDrag.vx;
    const wasHorizontal = flipDrag.horizontal;
    revealBtn.classList.remove("is-dragging");
    try {
      revealBtn.releasePointerCapture(e.pointerId);
    } catch (_) {}
    flipDrag = null;
    if (document.activeElement === revealBtn) revealBtn.blur();

    if (flipBusy) {
      revealInner.style.transform = "";
      return;
    }

    // First reveal only: tap/click flips to front (later flips stay drag-only)
    if (!wasHorizontal) {
      if (!faceRevealed && cardFacing === "back") {
        finishFlipOnce(flipBaseAngle(), "front", 0);
      } else {
        revealInner.style.transform = "";
      }
      return;
    }

    const rel = flipRelFromDx(dx);
    const from = flipBaseAngle() + rel;

    if (Math.abs(rel) >= 90) {
      finishFlipOnce(from, cardFacing === "front" ? "back" : "front", vx);
    } else {
      // soft settle home — tiny bounce if they flicked
      const speed = Math.abs(vx);
      if (speed > 0.35) {
        flipBusy = true;
        const base = flipBaseAngle();
        const kick = clamp(speed * 8, 3, 12) * (vx < 0 ? -1 : 1);
        revealInner.style.transition = "transform 0.18s cubic-bezier(0.2, 0.8, 0.3, 1)";
        revealInner.style.transform = `rotateY(${base + kick}deg)`;
        window.setTimeout(function () {
          revealInner.style.transition = "transform 0.38s cubic-bezier(0.34, 1.5, 0.64, 1)";
          revealInner.style.transform = `rotateY(${base}deg)`;
          window.setTimeout(clearInlineFlipTransform, 400);
        }, 180);
      } else {
        revealInner.style.transform = "";
      }
    }
  }

  function reset() {
    torn = false;
    dragging = false;
    drawn = null;
    points = [];
    cardFacing = "back";
    faceRevealed = false;
    flipBusy = false;
    flipDrag = null;
    setTear(0);
    resetClip();
    drawStroke();
    setState("sealed");
    cardRise.hidden = true;
    revealBtn.classList.remove("is-flipped", "is-dragging");
    revealInner.style.transform = "";
    revealFront.innerHTML = "";
    resultEl.classList.remove("is-visible");
    resultEl.setAttribute("aria-hidden", "true");
    if (openInfo) openInfo.classList.remove("has-result");
    resultName.textContent = "";
    resultMeta.textContent = "";
    resultPrice.textContent = "";
    btnReset.hidden = true;
    hintEl.textContent = "팩을 그어 개봉해주세요";
  }

  function init() {
    pack = PT.getPacks().find(function (p) {
      return p.id === PACK_ID;
    });
    if (!pack) {
      hintEl.textContent = "팩을 찾을 수 없어요";
      return;
    }

    const ids = new Set(pack.cardIds || []);
    pool = PT.getCards().filter(function (c) {
      return ids.has(c.id);
    });
    if (!pool.length) {
      hintEl.textContent = "카탈로그에 카드가 없어요";
      return;
    }

    applyTearConfig();
    resetClip();
    sizeCanvas();
    setTear(0);
    setState("sealed");

    const back = document.getElementById("open-back");
    if (back && PT.t) back.textContent = PT.t("backToSet");

    tearZone.addEventListener("pointerdown", onPointerDown);
    tearZone.addEventListener("pointermove", onPointerMove);
    tearZone.addEventListener("pointerup", onPointerUp);
    tearZone.addEventListener("pointercancel", onPointerUp);
    window.addEventListener("resize", function () {
      drawStroke();
    });

    revealBtn.addEventListener("pointerdown", onCardPointerDown);
    revealBtn.addEventListener("pointermove", onCardPointerMove);
    revealBtn.addEventListener("pointerup", onCardPointerUp);
    revealBtn.addEventListener("pointercancel", onCardPointerUp);
    btnReset.addEventListener("click", reset);
  }

  init();
})();
