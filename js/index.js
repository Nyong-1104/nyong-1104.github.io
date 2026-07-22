const allCards = [];
const ORDER_KEY = 'nyong_card_order';
let suppressFlipUntil = 0;
 
function resetAllCards() {
  allCards.forEach(c => {
    c.clearTilt();
    c.reset();
  });
}
 
function applyTilt(wrap, el, clientX, clientY, invert) {
  const r = el.getBoundingClientRect();
  const x = (clientX - r.left) / r.width;
  const y = (clientY - r.top) / r.height;
  const tiltX = invert ? (y - 0.5) * -18 : (y - 0.5) * 18;
  const tiltY = invert ? (x - 0.5) * 18 : (x - 0.5) * -18;
  wrap.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale(1.02)`;
}
 
function initCard(wrapId, frontId, backId, openId) {
  const wrap    = document.getElementById(wrapId);
  const front   = document.getElementById(frontId);
  const back    = document.getElementById(backId);
  const openBtn = openId ? document.getElementById(openId) : null;
  let flipped = false;
 
  function clearTilt() {
    wrap.style.transform = '';
  }
 
  function reset() {
    if (!flipped) return;
    flipped = false;
    clearTilt();
    wrap.classList.remove('flipped', 'expanded');
  }
 
  allCards.push({ wrap, reset, clearTilt });
 
  if (openBtn) {
    openBtn.addEventListener('click', e => e.stopPropagation());
    openBtn.addEventListener('pointerdown', e => e.stopPropagation());
  }
 
  function bindTilt(el, invert, activeWhen) {
    el.addEventListener('pointermove', e => {
      if (!activeWhen()) return;
      applyTilt(wrap, el, e.clientX, e.clientY, invert);
    });
    el.addEventListener('pointerdown', e => {
      if (!activeWhen()) return;
      applyTilt(wrap, el, e.clientX, e.clientY, invert);
    });
    el.addEventListener('pointerleave', () => {
      if (activeWhen()) clearTilt();
    });
    el.addEventListener('pointerup', () => {
      if (activeWhen()) clearTilt();
    });
    el.addEventListener('pointercancel', () => {
      if (activeWhen()) clearTilt();
    });
  }
 
  bindTilt(front, false, () => !flipped);
  bindTilt(back, true, () => flipped);
 
  front.addEventListener('click', e => {
    e.stopPropagation();
    if (Date.now() < suppressFlipUntil) return;
    if (flipped) return;
    resetAllCards();
    flipped = true;
    clearTilt();
    wrap.classList.add('flipped', 'expanded');
  });
 
  back.addEventListener('click', e => {
    e.stopPropagation();
    if (Date.now() < suppressFlipUntil) return;
    if (!flipped) return;
    flipped = false;
    clearTilt();
    wrap.classList.remove('flipped', 'expanded');
  });
}
 
function readOrder(count) {
  try {
    const raw = localStorage.getItem(ORDER_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    if (!Array.isArray(parsed) || parsed.length !== count) return null;
    if (new Set(parsed).size !== count) return null;
    return parsed;
  } catch {
    return null;
  }
}
 
function saveOrder(order) {
  try {
    localStorage.setItem(ORDER_KEY, JSON.stringify(order));
  } catch {}
}
 
function initCardDrag() {
  const stage = document.getElementById('stage');
  const drags = [...document.querySelectorAll('.card-drag')];
  const count = drags.length;
  const EASE = 'left 0.52s cubic-bezier(0.45, 0, 0.55, 1), top 0.52s cubic-bezier(0.45, 0, 0.55, 1)';
  const MOBILE_MQ = window.matchMedia('(max-width: 720px)');
  let order = readOrder(count) || drags.map((_, i) => i);

  function isMobile() {
    return MOBILE_MQ.matches;
  }

  function cols() {
    return isMobile() ? 2 : count;
  }

  function getGap() {
    if (isMobile()) return Math.max(12, Math.min(18, stage.clientWidth * 0.04));
    return Math.min(22, stage.clientWidth * 0.03);
  }

  function getCardW() {
    const sample = drags.find(el => !el.querySelector('.card-wrap.expanded')) || drags[0];
    return sample.offsetWidth;
  }

  function getCardH() {
    const sample = drags.find(el => !el.querySelector('.card-wrap.expanded')) || drags[0];
    return sample.offsetHeight;
  }

  function slotPositions() {
    const gap = getGap();
    const cardW = getCardW();
    const cardH = getCardH();
    const colCount = cols();
    const totalW = colCount * cardW + (colCount - 1) * gap;
    const startX = Math.max(0, (stage.clientWidth - totalW) / 2);

    return Array.from({ length: count }, (_, i) => {
      const col = i % colCount;
      const row = Math.floor(i / colCount);
      return {
        x: startX + col * (cardW + gap),
        y: row * (cardH + gap)
      };
    });
  }

  function stagePoint(clientX, clientY) {
    const rect = stage.getBoundingClientRect();
    return { x: clientX - rect.left, y: clientY - rect.top };
  }

  function layoutAll(excludeCardIdx = null, animate = true) {
    const slots = slotPositions();
    const gap = getGap();
    const cardH = getCardH();
    const rowCount = Math.ceil(count / cols());

    order.forEach((cardIdx, slotIdx) => {
      if (cardIdx === excludeCardIdx) return;
      const el = drags[cardIdx];
      const slot = slots[slotIdx];
      el.style.transition = animate ? EASE : 'none';
      el.style.left = `${slot.x}px`;
      el.style.top = `${slot.y}px`;
    });

    stage.style.minHeight = `${rowCount * cardH + (rowCount - 1) * gap + 16}px`;
    stage.classList.toggle('is-mobile', isMobile());
  }

  function hoverSlotFromPoint(clientX, clientY) {
    const { x: relX, y: relY } = stagePoint(clientX, clientY);
    const slots = slotPositions();
    const cardW = getCardW();
    const cardH = getCardH();
    const colCount = cols();

    if (colCount === 1 || !isMobile()) {
      let slot = 0;
      for (let i = 0; i < count - 1; i++) {
        const boundary = (slots[i].x + cardW + slots[i + 1].x) / 2;
        if (relX > boundary) slot = i + 1;
      }
      return slot;
    }

    // 2x2: pick nearest slot center
    let best = 0;
    let bestDist = Infinity;
    for (let i = 0; i < count; i++) {
      const cx = slots[i].x + cardW / 2;
      const cy = slots[i].y + cardH / 2;
      const dist = (relX - cx) ** 2 + (relY - cy) ** 2;
      if (dist < bestDist) {
        bestDist = dist;
        best = i;
      }
    }
    return best;
  }

  function shiftOthersAside(cardIdx, targetSlot) {
    const fromSlot = order.indexOf(cardIdx);
    if (fromSlot === targetSlot) return;
    order.splice(fromSlot, 1);
    order.splice(targetSlot, 0, cardIdx);
    layoutAll(cardIdx, true);
  }

  function followPointer(dragEl, clientX, clientY, drag) {
    const { x, y } = stagePoint(clientX, clientY);
    dragEl.style.left = `${x - drag.offsetX}px`;
    dragEl.style.top = `${Math.max(0, y - drag.offsetY)}px`;
  }

  function snapDraggedToSlot(dragEl, cardIdx) {
    const slots = slotPositions();
    const slotIdx = order.indexOf(cardIdx);
    const slot = slots[slotIdx];
    dragEl.style.transition = EASE;
    dragEl.style.left = `${slot.x}px`;
    dragEl.style.top = `${slot.y}px`;
  }

  layoutAll(null, false);

  window.addEventListener('resize', () => layoutAll(null, false));
  MOBILE_MQ.addEventListener('change', () => layoutAll(null, false));

  const DRAG_THRESHOLD = 8;

  drags.forEach((dragEl, cardIdx) => {
    const wrap = dragEl.querySelector('.card-wrap');
    const card = () => allCards.find(c => c.wrap === wrap);
    let drag = null;

    function beginDrag(e) {
      const rect = dragEl.getBoundingClientRect();
      const stageRect = stage.getBoundingClientRect();
      drag.active = true;
      drag.offsetX = e.clientX - rect.left;
      drag.offsetY = e.clientY - rect.top;
      dragEl.setPointerCapture(e.pointerId);
      dragEl.classList.add('is-dragging');
      dragEl.style.transition = 'none';
      dragEl.style.left = `${rect.left - stageRect.left}px`;
      dragEl.style.top = `${rect.top - stageRect.top}px`;
      card()?.clearTilt();
    }

    function onPointerMove(e) {
      if (!drag || drag.id !== e.pointerId) return;

      if (!drag.active) {
        const dx = e.clientX - drag.startX;
        const dy = e.clientY - drag.startY;
        if (Math.abs(dx) < DRAG_THRESHOLD && Math.abs(dy) < DRAG_THRESHOLD) return;
        beginDrag(e);
      }

      drag.moved = true;
      followPointer(dragEl, e.clientX, e.clientY, drag);

      const hoverSlot = hoverSlotFromPoint(e.clientX, e.clientY);
      if (hoverSlot !== drag.hoverSlot) {
        drag.hoverSlot = hoverSlot;
        shiftOthersAside(drag.cardIdx, hoverSlot);
      }
    }

    function endDrag(e) {
      if (!drag || drag.id !== e.pointerId) return;

      document.removeEventListener('pointermove', onPointerMove);
      document.removeEventListener('pointerup', endDrag);
      document.removeEventListener('pointercancel', endDrag);

      if (drag.active) {
        if (drag.moved) {
          shiftOthersAside(drag.cardIdx, hoverSlotFromPoint(e.clientX, e.clientY));
          saveOrder(order);
          suppressFlipUntil = Date.now() + 280;
        }
        dragEl.classList.remove('is-dragging');
        snapDraggedToSlot(dragEl, drag.cardIdx);
      }

      drag = null;
    }

    dragEl.addEventListener('pointerdown', e => {
      if (e.target.closest('.open-btn')) return;
      drag = {
        id: e.pointerId,
        cardIdx,
        startX: e.clientX,
        startY: e.clientY,
        hoverSlot: order.indexOf(cardIdx),
        active: false,
        moved: false
      };
      document.addEventListener('pointermove', onPointerMove);
      document.addEventListener('pointerup', endDrag);
      document.addEventListener('pointercancel', endDrag);
    });
  });
}
 
initCard('card1', 'front1', 'back1', 'open1');
initCard('card2', 'front2', 'back2', 'open2');
initCard('card3', 'front3', 'back3', 'open3');
initCard('card4', 'front4', 'back4', 'open4');
initCardDrag();
 
document.body.addEventListener('click', e => {
  if (e.target.closest('.card-wrap')) return;
  resetAllCards();
});
