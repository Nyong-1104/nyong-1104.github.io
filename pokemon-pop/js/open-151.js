/**
 * 151 Pack Open — tear → flip 1/7…7/7 → gallery
 */
(function () {
  const PT = window.PopTracker;
  const PACK_ID = "sv2a-151";

  const TEAR = {
    ratio: 0.21,
    yMin: 0.17,
    yMax: 0.26,
    edgeLeft: 0.05,
    edgeRight: 0.95,
    minPoints: 10,
    sampleDist: 0.01,
  };

  const HIT_RARITIES = { MSB: 1, SR: 1, SAR: 1, UR: 1 };
  /** Foil light during flat reveal — skip commons / R */
  const FOIL_RARITIES = { RR: 1, AR: 1, SR: 1, SAR: 1, UR: 1, MB: 1, MSB: 1 };

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
  const resultEl = document.getElementById("open-result");
  const resultName = document.getElementById("result-name");
  const resultMeta = document.getElementById("result-meta");
  const resultPrice = document.getElementById("result-price");
  const revealPhase = document.getElementById("reveal-phase");
  const cardStack = document.getElementById("card-stack");
  const galleryPhase = document.getElementById("gallery-phase");
  const galleryGrid = document.getElementById("gallery-grid");
  const btnReset = document.getElementById("btn-reset");
  const btnOpenAll = document.getElementById("btn-open-all");
  const modal = document.getElementById("card-modal");
  const modalCard = document.getElementById("modal-card");
  const modalName = document.getElementById("modal-name");
  const modalMeta = document.getElementById("modal-meta");
  const modalPrice = document.getElementById("modal-price");
  const modalLink = document.getElementById("modal-link");
  const modalClose = document.getElementById("modal-close");
  const modalBackdrop = document.getElementById("modal-backdrop");
  const galleryFocus = document.getElementById("gallery-focus");
  const galleryFocusCard = document.getElementById("gallery-focus-card");
  const galleryFocusBackdrop = document.getElementById("gallery-focus-backdrop");
  const openBack = document.getElementById("open-back");
  const packTitle = document.getElementById("open-pack-title");

  const CARD_BACK = "./assets/card-back-jp.png";

  let rates = null;
  let drawnSlots = [];
  let revealIndex = 0;
  let stackReady = false;
  let flingBusy = false;
  let openAllBusy = false;
  let galleryFocusSlot = null;
  let focusBusy = false;
  /** @type {null|{pointerId:number,startX:number,startY:number,dx:number,dy:number,lastX:number,lastY:number,lastT:number,vx:number,vy:number}} */
  let flingDrag = null;
  let tear = 0;
  let dragging = false;
  let torn = false;
  let glowAliveRaf = 0;
  let glowAlivePhase = 0;
  let flatHoloRaf = 0;
  /** @type {"stack"|"gallery"|null} */
  let flatHoloMode = null;
  /** @type {{x:number,y:number,rawX?:number,rawY?:number}[]} */
  let points = [];
  const strokeCtx = tearStroke.getContext("2d");

  function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
  }

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
    if (glowAliveRaf) cancelAnimationFrame(glowAliveRaf);
    glowAliveRaf = 0;
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
    if (points.length < 2) return { minRaw: 1, maxRaw: 0, coverage: 0 };
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
    return { coverage: Math.max(0, maxX - minX), minRaw: minRaw, maxRaw: maxRaw };
  }

  function isStrokeComplete() {
    if (points.length < TEAR.minPoints) return false;
    const b = strokeBounds();
    return b.minRaw <= TEAR.edgeLeft && b.maxRaw >= TEAR.edgeRight;
  }

  function liveTearProgress() {
    if (!points.length) return 0;
    return clamp(points[points.length - 1].x - points[0].x, 0, 1);
  }

  function edgePath() {
    if (points.length < 2) return [];
    let path = points.map(function (p) {
      return { x: p.x, y: p.y };
    });
    if (path[path.length - 1].x < path[0].x) path = path.slice().reverse();
    const mono = [{ x: path[0].x, y: path[0].y }];
    for (let i = 1; i < path.length; i++) {
      const prev = mono[mono.length - 1];
      const cur = path[i];
      if (cur.x > prev.x + 0.0008) mono.push({ x: cur.x, y: cur.y });
      else if (cur.x >= prev.x) mono[mono.length - 1] = { x: cur.x, y: cur.y };
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
      return;
    }
    const edge = edgePath();
    if (!edge.length) {
      resetClip();
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

  function syncOpenFx(edge, abovePoints) {
    if (!openFxSeam || !openFxFanFill || !openFxFanRays || !openFxAbovePoly) return;
    const y = TEAR.ratio;
    const src =
      edge && edge.length >= 2
        ? edge
        : [
            { x: 0, y: y },
            { x: 0.5, y: y },
            { x: 1, y: y },
          ];
    openFxSeam.setAttribute(
      "d",
      "M " +
        src
          .map(function (p) {
            return p.x.toFixed(4) + " " + p.y.toFixed(4);
          })
          .join(" L ")
    );
    const fill = [];
    for (let i = 0; i < src.length; i++) fill.push(src[i]);
    for (let i = src.length - 1; i >= 0; i--) {
      const p = src[i];
      const t = src.length <= 1 ? 0.5 : i / (src.length - 1);
      const lift = Math.sin(t * Math.PI);
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
    const rayParts = [];
    const sampleStep = Math.max(1, Math.floor(src.length / 7));
    for (let i = 0; i < src.length; i += sampleStep) {
      const p = src[i];
      const t = src.length <= 1 ? 0.5 : i / (src.length - 1);
      [-0.95, -0.55, -0.2, 0.2, 0.55, 0.95].forEach(function (ang, a) {
        const len = 0.07 + 0.11 * Math.sin(t * Math.PI) * (0.65 + (a % 2) * 0.35);
        rayParts.push(
          "M " +
            p.x.toFixed(4) +
            " " +
            p.y.toFixed(4) +
            " L " +
            clamp(p.x + Math.sin(ang) * len, -0.1, 1.1).toFixed(4) +
            " " +
            clamp(p.y - Math.cos(ang) * len, 0, 1).toFixed(4)
        );
      });
    }
    openFxFanRays.setAttribute("d", rayParts.join(" "));
    if (abovePoints) openFxAbovePoly.setAttribute("points", abovePoints);
    else {
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
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    function strokePath(width, color) {
      ctx.beginPath();
      ctx.moveTo(points[0].x * size.w, points[0].y * size.h);
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x * size.w, points[i].y * size.h);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.stroke();
    }
    strokePath(14, "rgba(255, 200, 100, 0.35)");
    strokePath(8, "rgba(255, 230, 150, 0.55)");
    strokePath(4, "rgba(255, 248, 220, 0.9)");
    strokePath(1.6, "rgba(255, 255, 255, 0.95)");
  }

  function refreshStrokeOnly() {
    setTear(liveTearProgress());
    drawStroke();
  }

  function cardImage(card) {
    return (card.images && (card.images.jp || card.images.kr)) || card.image || "";
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

  function formatPriceLine(card) {
    const avg = cardAvgPrice(card);
    if (!avg) return "평균 시세 —";
    const money = PT.formatMoney(avg.amount, avg.currency);
    const langLabel = PT.langLabel ? PT.langLabel(avg.lang) : String(avg.lang || "").toUpperCase();
    return `평균 시세 ${money} · PSA ${avg.grade} (${langLabel})`;
  }

  function isHit(card) {
    return !!(card && HIT_RARITIES[String(card.rarity || "").toUpperCase()]);
  }

  function isFoil(card) {
    if (!card) return false;
    const rarity = String(card.rarity || "").toUpperCase();
    if (FOIL_RARITIES[rarity]) return true;
    const style = PT.resolveHoloStyle ? PT.resolveHoloStyle(card) : card.holoStyle;
    return style === "monster-ball" || style === "master-ball";
  }

  function makeFace(card, faceDown) {
    const wrap = document.createElement("button");
    wrap.type = "button";
    wrap.className = "open151-card" + (faceDown ? " is-back" : " is-front is-flat");
    if (card && isHit(card)) wrap.classList.add("is-hit");
    if (card && isFoil(card)) wrap.classList.add("is-foil");
    wrap.setAttribute("aria-label", card ? PT.cardName(card) : "카드");

    const inner = document.createElement("span");
    inner.className = "open151-card__inner";

    const front = document.createElement("span");
    front.className = "open151-card__face open151-card__face--front";
    if (card) {
      const holo = PT.createHoloCardEl({
        name: PT.cardName(card),
        image: cardImage(card),
        holoStyle: PT.resolveHoloStyle ? PT.resolveHoloStyle(card) : card.holoStyle || "holo",
      });
      front.appendChild(holo);
      PT.mountHoloCard(holo);
    }

    if (faceDown) {
      const back = document.createElement("span");
      back.className = "open151-card__face open151-card__face--back";
      const backImg = document.createElement("img");
      backImg.src = CARD_BACK;
      backImg.alt = "";
      backImg.draggable = false;
      back.appendChild(backImg);
      inner.appendChild(back);
      inner.appendChild(front);
    } else {
      // Gallery / face-up only: no card-back (avoids black plate behind tilt)
      front.style.transform = "none";
      inner.appendChild(front);
    }

    wrap.appendChild(inner);
    return wrap;
  }

  function clearFlatHoloNode(holo) {
    if (!holo) return;
    holo.classList.remove("is-flat-sweep", "interacting");
    holo.style.setProperty("--card-opacity", "0");
    holo.style.setProperty("--rotate-x", "0deg");
    holo.style.setProperty("--rotate-y", "0deg");
    holo.style.setProperty("--pointer-x", "50%");
    holo.style.setProperty("--pointer-y", "50%");
    holo.style.setProperty("--background-x", "50%");
    holo.style.setProperty("--background-y", "50%");
    holo.style.setProperty("--pointer-from-center", "0");
  }

  function applyFlatHoloPan(holo, phase) {
    const t = performance.now() / 1000 + phase;
    const x = 50 + Math.sin(t * 1.15) * 40;
    const y = 48 + Math.cos(t * 0.9) * 30;
    const dx = x - 50;
    const dy = y - 50;
    const fromCenter = Math.min(1, Math.sqrt(dx * dx + dy * dy) / 50);
    holo.classList.add("is-flat-sweep", "interacting");
    holo.style.setProperty("--pointer-x", x.toFixed(2) + "%");
    holo.style.setProperty("--pointer-y", y.toFixed(2) + "%");
    holo.style.setProperty("--background-x", (37 + (x / 100) * 26).toFixed(2) + "%");
    holo.style.setProperty("--background-y", (33 + (y / 100) * 34).toFixed(2) + "%");
    holo.style.setProperty("--card-opacity", "1");
    holo.style.setProperty("--pointer-from-center", fromCenter.toFixed(3));
    holo.style.setProperty("--rotate-x", "0deg");
    holo.style.setProperty("--rotate-y", "0deg");
  }

  function stopFlatHoloSweep() {
    if (flatHoloRaf) cancelAnimationFrame(flatHoloRaf);
    flatHoloRaf = 0;
    flatHoloMode = null;
    cardStack.querySelectorAll(".holo-card.is-flat-sweep").forEach(clearFlatHoloNode);
    galleryGrid.querySelectorAll(".holo-card.is-flat-sweep").forEach(clearFlatHoloNode);
  }

  function pumpFlatHoloSweep() {
    if (flatHoloMode === "stack") {
      if (!stackReady || revealPhase.hidden) {
        flatHoloRaf = 0;
        flatHoloMode = null;
        return;
      }
      const topCard = cardStack.querySelector(".open151-card.is-top:not(.is-flung)");
      const top =
        topCard && topCard.classList.contains("is-foil")
          ? topCard.querySelector(".holo-card")
          : null;
      cardStack.querySelectorAll(".holo-card.is-flat-sweep").forEach(function (holo) {
        if (holo !== top) clearFlatHoloNode(holo);
      });
      if (top) applyFlatHoloPan(top, 0);
      flatHoloRaf = requestAnimationFrame(pumpFlatHoloSweep);
      return;
    }

    if (flatHoloMode === "gallery") {
      if (galleryPhase.hidden) {
        flatHoloRaf = 0;
        flatHoloMode = null;
        return;
      }
      // Thumbnails keep flat foil light; focused 3D card is a separate overlay
      const holos = galleryGrid.querySelectorAll(
        ".open151-gallery__cell:not(.is-focused) .open151-card--gallery.is-foil .holo-card"
      );
      const live = new Set(holos);
      galleryGrid.querySelectorAll(".holo-card.is-flat-sweep").forEach(function (holo) {
        if (!live.has(holo)) clearFlatHoloNode(holo);
      });
      holos.forEach(function (holo, i) {
        applyFlatHoloPan(holo, i * 0.55);
      });
      flatHoloRaf = requestAnimationFrame(pumpFlatHoloSweep);
      return;
    }

    flatHoloRaf = 0;
  }

  function startFlatHoloSweep(mode) {
    flatHoloMode = mode || "stack";
    if (flatHoloRaf) return;
    flatHoloRaf = requestAnimationFrame(pumpFlatHoloSweep);
  }

  function stripBacksAndFlatten() {
    cardStack.querySelectorAll(".open151-card").forEach(function (el) {
      const back = el.querySelector(".open151-card__face--back");
      if (back && back.parentNode) back.parentNode.removeChild(back);
      const inner = el.querySelector(".open151-card__inner");
      const front = el.querySelector(".open151-card__face--front");
      el.classList.remove("is-back");
      el.classList.add("is-front", "is-flat");
      if (inner) {
        inner.style.transform = "none";
        inner.style.transition = "none";
      }
      if (front) front.style.transform = "none";
    });
  }

  function showRevealInfo(card) {
    if (!card) return;
    resultName.textContent = PT.cardName(card);
    resultMeta.textContent = `${card.number || ""} · ${card.rarity || ""}`;
    resultPrice.textContent = "";
    resultEl.classList.add("is-visible");
    resultEl.setAttribute("aria-hidden", "false");
    openInfo.classList.add("has-result");
    const hit = isHit(card);
    resultEl.classList.toggle("is-hit", hit);
    resultName.classList.toggle("open-result__shine--gold", hit);
  }

  function stackOffset(iFromTop) {
    return {
      y: iFromTop * -7,
      scale: 1 - iFromTop * 0.016,
      z: 100 - iFromTop,
    };
  }

  function remainingCount() {
    return cardStack.querySelectorAll(".open151-card:not(.is-flung)").length;
  }

  function applyStackLayout() {
    const cards = cardStack.querySelectorAll(".open151-card:not(.is-flung)");
    cards.forEach(function (el, i) {
      const o = stackOffset(i);
      el.style.setProperty("--stack-i", String(i));
      el.style.zIndex = String(o.z);
      el.classList.toggle("is-top", i === 0);
      el.classList.remove("is-under");
      if (i === 0) {
        el.style.transform = "";
        el.style.opacity = "1";
        el.removeAttribute("aria-hidden");
        el.tabIndex = 0;
      } else {
        el.style.transform =
          "translateY(" + o.y + "px) scale(" + o.scale + ")";
        el.style.opacity = "1";
        el.tabIndex = -1;
        el.setAttribute("aria-hidden", "true");
      }
    });
  }

  function setOpenAllVisible(show) {
    if (!btnOpenAll) return;
    btnOpenAll.hidden = !show;
  }

  function bindTopFling() {
    const top = cardStack.querySelector(".open151-card.is-top");
    if (!top) return;
    top.onpointerdown = onFlingDown;
    top.onpointermove = onFlingMove;
    top.onpointerup = onFlingUp;
    top.onpointercancel = onFlingUp;
  }

  function unbindAllFling() {
    cardStack.querySelectorAll(".open151-card").forEach(function (el) {
      el.onpointerdown = null;
      el.onpointermove = null;
      el.onpointerup = null;
      el.onpointercancel = null;
      el.classList.remove("is-dragging");
    });
    flingDrag = null;
  }

  function flingFadeOpacity(dist, threshold) {
    if (dist <= threshold) return 1;
    return clamp(1 - (dist - threshold) / (threshold * 0.9), 0, 1);
  }

  function onFlingDown(e) {
    if (!stackReady || flingBusy || openAllBusy) return;
    const top = cardStack.querySelector(".open151-card.is-top");
    if (!top || e.currentTarget !== top) return;
    flingDrag = {
      pointerId: e.pointerId,
      startX: e.clientX,
      startY: e.clientY,
      dx: 0,
      dy: 0,
      lastX: e.clientX,
      lastY: e.clientY,
      lastT: performance.now(),
      vx: 0,
      vy: 0,
    };
    top.classList.add("is-dragging");
    try {
      top.setPointerCapture(e.pointerId);
    } catch (_) {}
  }

  function onFlingMove(e) {
    if (!flingDrag || e.pointerId !== flingDrag.pointerId || flingBusy) return;
    e.preventDefault();
    const top = cardStack.querySelector(".open151-card.is-top");
    if (!top) return;
    const dx = e.clientX - flingDrag.startX;
    const dy = e.clientY - flingDrag.startY;
    flingDrag.dx = dx;
    flingDrag.dy = dy;
    const now = performance.now();
    const dt = Math.max(now - flingDrag.lastT, 1);
    flingDrag.vx = flingDrag.vx * 0.55 + ((e.clientX - flingDrag.lastX) / dt) * 0.45;
    flingDrag.vy = flingDrag.vy * 0.55 + ((e.clientY - flingDrag.lastY) / dt) * 0.45;
    flingDrag.lastX = e.clientX;
    flingDrag.lastY = e.clientY;
    flingDrag.lastT = now;

    const cardW = Math.max(top.offsetWidth, 1);
    const cardH = Math.max(top.offsetHeight, 1);
    const dist = Math.hypot(dx, dy);
    const axisThresh = Math.abs(dx) > Math.abs(dy) ? cardW : cardH;
    top.style.transform = "translate(" + dx + "px, " + dy + "px)";
    top.style.opacity = String(flingFadeOpacity(dist, axisThresh));
  }

  function onFlingUp(e) {
    if (!flingDrag || e.pointerId !== flingDrag.pointerId) return;
    const top = cardStack.querySelector(".open151-card.is-top");
    const dx = flingDrag.dx;
    const dy = flingDrag.dy;
    const vx = flingDrag.vx;
    const vy = flingDrag.vy;
    flingDrag = null;
    if (!top) return;
    top.classList.remove("is-dragging");
    try {
      top.releasePointerCapture(e.pointerId);
    } catch (_) {}

    const dist = Math.hypot(dx, dy);
    const speed = Math.hypot(vx, vy);

    // Last card: tap opens gallery
    if (remainingCount() <= 1 && dist < 12 && speed < 0.2) {
      enterGallery();
      return;
    }

    const distanceOk = dist > 70;
    const velocityOk = speed > 0.55;
    if (distanceOk || velocityOk) {
      const scoreX = dx + vx * 40;
      const scoreY = dy + vy * 40;
      let dirX = 0;
      let dirY = 0;
      if (Math.abs(scoreX) > Math.abs(scoreY)) {
        dirX = scoreX < 0 ? -1 : 1;
      } else {
        dirY = scoreY < 0 ? -1 : 1;
      }
      flingTopCard(dirX, dirY);
      return;
    }
    top.style.transition = "transform 0.28s ease, opacity 0.28s ease";
    top.style.transform = "";
    top.style.opacity = "1";
    window.setTimeout(function () {
      top.style.transition = "";
    }, 300);
  }

  function flingTopCard(dirX, dirY) {
    if (flingBusy || openAllBusy) return;
    const top = cardStack.querySelector(".open151-card.is-top");
    if (!top) return;
    flingBusy = true;
    const cardW = Math.max(top.offsetWidth, 160);
    const cardH = Math.max(top.offsetHeight, 220);
    // Travel ~1.35× card size so fade starts after one card-length
    const travel = (dirX !== 0 ? cardW : cardH) * 1.35;
    const tx = dirX * travel;
    const ty = dirY * travel;
    top.classList.add("is-flung");
    top.style.pointerEvents = "none";
    top.style.transition =
      "transform 0.42s cubic-bezier(0.2, 0.8, 0.25, 1), opacity 0.28s ease 0.14s";
    top.style.transform = "translate(" + tx + "px, " + ty + "px)";
    top.style.opacity = "0";

    revealIndex += 1;
    window.setTimeout(function () {
      if (top.parentNode) top.parentNode.removeChild(top);
      flingBusy = false;
      if (revealIndex >= drawnSlots.length) {
        enterGallery();
        return;
      }
      applyStackLayout();
      bindTopFling();
      showRevealInfo(drawnSlots[revealIndex].card);
    }, 430);
  }

  function openAllAtOnce() {
    if (!stackReady || flingBusy || openAllBusy) return;
    const cards = Array.prototype.slice.call(
      cardStack.querySelectorAll(".open151-card:not(.is-flung)")
    );
    if (!cards.length) {
      enterGallery();
      return;
    }

    openAllBusy = true;
    stackReady = false;
    flingDrag = null;
    setOpenAllVisible(false);
    unbindAllFling();
    stopFlatHoloSweep();

    const cardH = Math.max(cards[0].offsetHeight || 0, 220);
    const travel = cardH * 1.55;
    const stagger = 85;
    const flyMs = 320;

    cards.forEach(function (card, i) {
      window.setTimeout(function () {
        card.classList.add("is-flung");
        card.classList.remove("is-top", "is-dragging");
        card.style.pointerEvents = "none";
        card.style.zIndex = String(220 - i);
        card.style.transition =
          "transform " +
          flyMs / 1000 +
          "s cubic-bezier(0.15, 0.85, 0.25, 1), opacity " +
          flyMs / 1000 * 0.55 +
          "s ease " +
          flyMs / 1000 * 0.2 +
          "s";
        card.style.transform = "translateY(-" + travel + "px) scale(0.94)";
        card.style.opacity = "0";
      }, i * stagger);
    });

    window.setTimeout(function () {
      revealIndex = drawnSlots.length;
      openAllBusy = false;
      enterGallery();
    }, (cards.length - 1) * stagger + flyMs + 80);
  }

  function dealThenFlipStack() {
    stopFlatHoloSweep();
    setOpenAllVisible(false);
    cardStack.innerHTML = "";
    cardStack.classList.remove("is-face-up", "is-flipping-all", "has-deck");
    cardStack.style.removeProperty("--deck-n");
    stackReady = false;
    flingBusy = false;
    openAllBusy = false;
    revealIndex = 0;

    const total = drawnSlots.length;
    for (let i = 0; i < total; i++) {
      const el = makeFace(drawnSlots[i].card, true);
      el.dataset.index = String(i);
      el.classList.add("is-dealing");
      el.style.opacity = "0";
      el.style.transform = "translateY(46%) scale(0.9)";
      el.style.zIndex = String(100 - i);
      cardStack.appendChild(el);
    }

    // Rise bottom→top visually: card6 first, card0 last (ends on top)
    let delay = 0;
    for (let step = 0; step < total; step++) {
      const idx = total - 1 - step;
      const el = cardStack.querySelector('[data-index="' + idx + '"]');
      if (!el) continue;
      window.setTimeout(
        function (node, fromTop) {
          node.classList.remove("is-dealing");
          node.classList.add("is-dealt");
          node.style.transition =
            "transform 0.55s cubic-bezier(0.2, 0.75, 0.25, 1), opacity 0.45s ease";
          const o = stackOffset(fromTop);
          node.style.opacity = "1";
          node.style.zIndex = String(o.z);
          node.style.transform =
            "translateY(" + o.y + "px) scale(" + o.scale + ")";
        },
        delay,
        el,
        idx
      );
      delay += 115;
    }

    window.setTimeout(function () {
      cardStack.classList.add("is-flipping-all");
      const all = cardStack.querySelectorAll(".open151-card");
      all.forEach(function (el) {
        el.classList.remove("is-back");
        el.classList.add("is-front");
      });
      window.setTimeout(function () {
        cardStack.classList.remove("is-flipping-all");
        stripBacksAndFlatten();
        cardStack.classList.add("is-face-up");
        applyStackLayout();
        stackReady = true;
        bindTopFling();
        startFlatHoloSweep("stack");
        setOpenAllVisible(true);
        showRevealInfo(drawnSlots[0] && drawnSlots[0].card);
      }, 620);
    }, delay + 260);
  }

  function focusCardSize(maxW, maxH) {
    const widthCap = Math.min(200, Math.max(140, (maxW || window.innerWidth) * 0.48));
    let w = widthCap;
    let h = w / 0.716;
    const heightCap = Math.min(maxH || window.innerHeight * 0.5, 340);
    if (h > heightCap) {
      h = heightCap;
      w = h * 0.716;
    }
    return { w: w, h: h };
  }

  function setFocusCardBox(box) {
    if (!galleryFocusCard) return;
    galleryFocusCard.style.position = "fixed";
    galleryFocusCard.style.left = box.left + "px";
    galleryFocusCard.style.top = box.top + "px";
    galleryFocusCard.style.width = box.width + "px";
    galleryFocusCard.style.height = box.height + "px";
    galleryFocusCard.style.right = "auto";
    galleryFocusCard.style.bottom = "auto";
    galleryFocusCard.style.margin = "0";
    galleryFocusCard.style.zIndex = "72";
  }

  function centerFocusBox() {
    // Use layout viewport — focus overlay is outside .open-stage now
    const width = window.innerWidth;
    const height = window.innerHeight;
    const infoRect = openInfo ? openInfo.getBoundingClientRect() : null;
    const resetRect = btnReset ? btnReset.getBoundingClientRect() : null;

    const topBound = (infoRect ? infoRect.bottom : 88) + 10;
    let bottomBound = height - 20;
    if (resetRect && resetRect.top > topBound + 80) {
      bottomBound = resetRect.top - 12;
    }
    const bandH = Math.max(160, bottomBound - topBound);
    const size = focusCardSize(width, bandH * 0.9);
    const left = (width - size.w) / 2;
    const top = topBound + Math.max(0, (bandH - size.h) / 2);
    return { left: left, top: top, width: size.w, height: size.h };
  }

  function resetFocusDom() {
    galleryPhase.classList.remove("has-focus");
    galleryGrid.querySelectorAll(".open151-gallery__cell.is-focused").forEach(function (el) {
      el.classList.remove("is-focused");
    });
    if (galleryFocusCard) {
      galleryFocusCard.innerHTML = "";
      galleryFocusCard.style.cssText = "";
    }
    if (galleryFocus) {
      galleryFocus.hidden = true;
      galleryFocus.classList.remove("is-flying");
    }
    galleryFocusSlot = null;
    document.body.classList.remove("is-gallery-focus");
    resultEl.classList.remove("is-visible", "is-hit");
    resultEl.setAttribute("aria-hidden", "true");
    openInfo.classList.remove("has-result");
    resultName.classList.remove("open-result__shine--gold");
  }

  function clearGalleryFocus(animate) {
    if (focusBusy) return;
    if (!galleryFocusSlot || !galleryFocusCard || !galleryFocus || galleryFocus.hidden || animate === false) {
      resetFocusDom();
      return;
    }

    const cell = galleryFocusSlot.cell;
    const dest = cell.getBoundingClientRect();
    focusBusy = true;
    galleryFocus.classList.add("is-flying");
    resultEl.classList.remove("is-visible", "is-hit");
    openInfo.classList.remove("has-result");
    resultName.classList.remove("open-result__shine--gold");

    galleryFocusCard.style.transition =
      "left 0.38s cubic-bezier(0.22, 0.82, 0.25, 1), top 0.38s cubic-bezier(0.22, 0.82, 0.25, 1), width 0.38s cubic-bezier(0.22, 0.82, 0.25, 1), height 0.38s cubic-bezier(0.22, 0.82, 0.25, 1)";
    setFocusCardBox({
      left: dest.left,
      top: dest.top,
      width: dest.width,
      height: dest.height,
    });

    window.setTimeout(function () {
      resetFocusDom();
      focusBusy = false;
    }, 400);
  }

  function mountFocusHolo(card) {
    galleryFocusCard.innerHTML = "";
    const holo = PT.createHoloCardEl({
      name: PT.cardName(card),
      image: cardImage(card),
      holoStyle: PT.resolveHoloStyle ? PT.resolveHoloStyle(card) : card.holoStyle || "holo",
    });
    holo.classList.add("open151-focus__holo");
    holo.style.background = "transparent";
    holo.style.backgroundColor = "transparent";
    holo.style.pointerEvents = "auto";
    holo.style.touchAction = "none";
    const front = holo.querySelector(".holo-card__front");
    if (front) {
      front.style.background = "transparent";
      front.style.backgroundColor = "transparent";
    }
    // Allow remount after fly-in (mountHoloCard is one-shot via dataset)
    delete holo.dataset.holoReady;
    galleryFocusCard.appendChild(holo);
    PT.mountHoloCard(holo);

    // Mobile: keep receiving move events while dragging on the card
    holo.addEventListener("pointerdown", function (e) {
      try {
        holo.setPointerCapture(e.pointerId);
      } catch (_) {}
    });
  }

  function openGalleryFocus(cell, card) {
    if (focusBusy) return;
    resetFocusDom();

    const origin = cell.getBoundingClientRect();
    cell.classList.add("is-focused");
    galleryPhase.classList.add("has-focus");
    galleryFocusSlot = { cell: cell, card: card };
    document.body.classList.add("is-gallery-focus");

    mountFocusHolo(card);
    galleryFocus.hidden = false;
    galleryFocus.classList.add("is-flying");

    galleryFocusCard.style.transition = "none";
    galleryFocusCard.style.opacity = "1";
    setFocusCardBox({
      left: origin.left,
      top: origin.top,
      width: origin.width,
      height: origin.height,
    });
    void galleryFocusCard.offsetWidth;

    requestAnimationFrame(function () {
      showRevealInfo(card);
      requestAnimationFrame(function () {
        galleryFocusCard.style.transition =
          "left 0.42s cubic-bezier(0.16, 1, 0.3, 1), top 0.42s cubic-bezier(0.16, 1, 0.3, 1), width 0.42s cubic-bezier(0.16, 1, 0.3, 1), height 0.42s cubic-bezier(0.16, 1, 0.3, 1)";
        setFocusCardBox(centerFocusBox());
        window.setTimeout(function () {
          galleryFocus.classList.remove("is-flying");
          // Remount holo at final size so tilt math / listeners are fresh
          if (galleryFocusSlot && galleryFocusSlot.card) {
            mountFocusHolo(galleryFocusSlot.card);
          }
        }, 430);
      });
    });
  }

  function toggleGalleryFocus(cell, card) {
    if (focusBusy) return;
    if (cell.classList.contains("is-focused") && galleryFocus && !galleryFocus.hidden) {
      clearGalleryFocus(true);
      return;
    }
    openGalleryFocus(cell, card);
  }

  function isMobileGalleryLayout() {
    return window.matchMedia("(max-width: 560px)").matches;
  }

  function makeGalleryCell(card, i) {
    const btn = makeFace(card, false);
    btn.classList.add("open151-card--gallery");
    btn.style.setProperty("--stack-i", "0");
    const cell = document.createElement("div");
    cell.className = "open151-gallery__cell";
    cell.style.animationDelay = i * 0.05 + "s";
    cell.appendChild(btn);
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      toggleGalleryFocus(cell, card);
    });
    return cell;
  }

  function enterGallery() {
    stopFlatHoloSweep();
    setOpenAllVisible(false);
    stackReady = false;
    openAllBusy = false;
    flingBusy = false;
    revealPhase.hidden = true;
    cardStack.innerHTML = "";
    galleryPhase.hidden = false;
    galleryPhase.classList.remove("is-ready");
    clearGalleryFocus(false);
    hintEl.textContent = "";
    openInfo.classList.add("is-gallery");
    packEl.hidden = true;
    packEl.classList.remove("is-gallery-behind");

    galleryGrid.innerHTML = "";
    const cards = drawnSlots.map(function (s) { return s && s.card; }).filter(Boolean);
    const mobile = isMobileGalleryLayout();
    // Mobile: 2 / 3 / 2 — Desktop: 4 / 3
    const pattern = mobile ? [2, 3, 2] : [4, 3];
    let idx = 0;
    pattern.forEach(function (count) {
      const row = document.createElement("div");
      row.className = "open151-gallery__row open151-gallery__row--" + count;
      for (let n = 0; n < count && idx < cards.length; n++, idx++) {
        row.appendChild(makeGalleryCell(cards[idx], idx));
      }
      galleryGrid.appendChild(row);
    });

    startFlatHoloSweep("gallery");

    window.setTimeout(function () {
      galleryPhase.classList.add("is-ready");
    }, 900);
  }

  function openModal(card) {
    modalCard.innerHTML = "";
    const holo = PT.createHoloCardEl({
      name: PT.cardName(card),
      image: cardImage(card),
      holoStyle: PT.resolveHoloStyle ? PT.resolveHoloStyle(card) : card.holoStyle || "holo",
    });
    modalCard.appendChild(holo);
    PT.mountHoloCard(holo);
    modalName.textContent = PT.cardName(card);
    modalMeta.textContent = `${card.number || ""} · ${card.rarity || ""}`;
    modalPrice.textContent = formatPriceLine(card);
    modalLink.href = "./card.html?id=" + encodeURIComponent(card.id);
    modal.hidden = false;
    document.body.classList.add("is-modal-open");
  }

  function closeModal() {
    modal.hidden = true;
    modalCard.innerHTML = "";
    document.body.classList.remove("is-modal-open");
  }

  function startRevealPhase() {
    packEl.hidden = false;
    packEl.classList.remove("is-gallery-behind");
    revealPhase.hidden = false;
    galleryPhase.hidden = true;
    revealIndex = 0;
    stackReady = false;
    hintEl.textContent = "";
    openInfo.classList.remove("is-gallery", "has-result");
    resultEl.classList.remove("is-visible", "is-hit");
    dealThenFlipStack();
    window.setTimeout(function () {
      if (packEl.dataset.state === "torn") setState("revealed");
    }, 1600);
  }

  function completeTear() {
    if (torn) return;
    torn = true;
    dragging = false;
    setTear(1);
    setState("torn");

    if (!rates) {
      torn = false;
      setTear(0);
      resetClip();
      drawStroke();
      setState("sealed");
      hintEl.textContent = "확률표를 아직 불러오지 못했어요. 잠시 후 다시 그어주세요";
      return;
    }

    const cards = PT.getCards ? PT.getCards() : [];
    drawnSlots = PT.drawPackFromRates(rates, cards);
    const ok = drawnSlots.some(function (s) {
      return s && s.card;
    });
    if (!ok) {
      hintEl.textContent = "카드 풀을 찾지 못했어요 (catalog " + cards.length + ")";
      return;
    }

    hintEl.textContent = "";
    window.setTimeout(function () {
      startRevealPhase();
    }, 900);
  }

  function openAlongPath() {
    if (torn) return;
    updateClip();
    setState("splitting");
    window.setTimeout(completeTear, 520);
  }

  function onPointerDown(e) {
    if (torn) return;
    if (!rates) {
      hintEl.textContent = "확률표를 불러오는 중이에요…";
      return;
    }
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

  function onPointerUp() {
    if (!dragging) return;
    dragging = false;
    if (torn) return;
    setTear(strokeBounds().coverage);
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

  function reset() {
    torn = false;
    dragging = false;
    drawnSlots = [];
    revealIndex = 0;
    stackReady = false;
    flingBusy = false;
    openAllBusy = false;
    flingDrag = null;
    points = [];
    stopFlatHoloSweep();
    setOpenAllVisible(false);
    setTear(0);
    resetClip();
    drawStroke();
    setState("sealed");
    packEl.hidden = false;
    packEl.classList.remove("is-gallery-behind");
    revealPhase.hidden = true;
    galleryPhase.hidden = true;
    cardStack.innerHTML = "";
    cardStack.classList.remove("is-face-up", "is-flipping-all", "has-deck");
    cardStack.style.removeProperty("--deck-n");
    galleryGrid.innerHTML = "";
    galleryPhase.classList.remove("has-focus", "is-ready");
    clearGalleryFocus(false);
    closeModal();
    resultEl.classList.remove("is-visible", "is-hit");
    resultEl.setAttribute("aria-hidden", "true");
    openInfo.classList.remove("has-result", "is-gallery");
    resultName.textContent = "";
    resultName.classList.remove("open-result__shine--gold");
    resultMeta.textContent = "";
    resultPrice.textContent = "";
    hintEl.textContent = "팩을 그어 개봉해주세요";
  }

  function init() {
    const pack = PT.getPacks().find(function (p) {
      return p.id === PACK_ID;
    });
    if (!pack) {
      hintEl.textContent = "팩을 찾을 수 없어요";
      return;
    }
    if (packTitle) packTitle.textContent = PT.packName(pack);
    if (openBack) {
      openBack.href = "./set.html?pack=" + encodeURIComponent(PACK_ID);
      openBack.textContent = PT.t("backToSet") || "← 세트 목록";
    }
    document.title = "151 Pack Open Simulator · PokePop";

    applyTearConfig();
    resetClip();
    sizeCanvas();

    tearZone.addEventListener("pointerdown", onPointerDown);
    tearZone.addEventListener("pointermove", onPointerMove);
    tearZone.addEventListener("pointerup", onPointerUp);
    tearZone.addEventListener("pointercancel", onPointerUp);
    window.addEventListener("resize", function () {
      sizeCanvas();
      drawStroke();
    });

    btnReset.addEventListener("click", reset);
    if (btnOpenAll) btnOpenAll.addEventListener("click", openAllAtOnce);
    modalClose.addEventListener("click", closeModal);
    modalBackdrop.addEventListener("click", closeModal);
    if (galleryFocusBackdrop) {
      galleryFocusBackdrop.addEventListener("click", function () {
        clearGalleryFocus(true);
      });
    }
    if (galleryFocusCard) {
      let focusPtr = null;
      galleryFocusCard.addEventListener("pointerdown", function (e) {
        focusPtr = { x: e.clientX, y: e.clientY, moved: false, id: e.pointerId };
      });
      galleryFocusCard.addEventListener("pointermove", function (e) {
        if (!focusPtr || e.pointerId !== focusPtr.id) return;
        if (Math.hypot(e.clientX - focusPtr.x, e.clientY - focusPtr.y) > 10) {
          focusPtr.moved = true;
        }
      });
      galleryFocusCard.addEventListener("click", function (e) {
        e.stopPropagation();
        // Ignore click right after fly-in / while flying
        if (galleryFocus.classList.contains("is-flying") || focusBusy) return;
        const moved = focusPtr && focusPtr.moved;
        focusPtr = null;
        // Drag = tilt only; short tap = put back
        if (moved) return;
        clearGalleryFocus(true);
      });
    }
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        if (galleryFocus && !galleryFocus.hidden) clearGalleryFocus(true);
        else closeModal();
      }
    });

    PT.loadOpenRates(PACK_ID)
      .then(function (json) {
        rates = json;
        hintEl.textContent = "팩을 그어 개봉해주세요";
      })
      .catch(function () {
        hintEl.textContent = "확률표를 불러오지 못했어요";
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
