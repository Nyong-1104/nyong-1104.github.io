(function (global) {
  const dirs = {
    up: false,
    down: false,
    left: false,
    right: false,
  };
  let bombPressed = false;
  let itemPressed = false;
  let bombLatched = false;
  let itemLatched = false;

  const keyMap = {
    ArrowUp: "up",
    ArrowDown: "down",
    ArrowLeft: "left",
    ArrowRight: "right",
    KeyW: "up",
    KeyS: "down",
    KeyA: "left",
    KeyD: "right",
  };

  function isTypingTarget(el) {
    if (!el) return false;
    const tag = (el.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return true;
    if (el.isContentEditable) return true;
    return false;
  }

  function onKey(e, down) {
    if (isTypingTarget(e.target)) return;
    const dir = keyMap[e.code];
    if (dir) {
      dirs[dir] = down;
      e.preventDefault();
      return;
    }
    if (e.code === "Space" || e.code === "KeyZ") {
      if (down && !e.repeat) bombPressed = true;
      e.preventDefault();
      return;
    }
    if (e.code === "KeyX" || e.code === "ShiftLeft" || e.code === "ShiftRight") {
      if (down && !e.repeat) itemPressed = true;
      e.preventDefault();
    }
  }

  window.addEventListener("keydown", (e) => onKey(e, true), { passive: false });
  window.addEventListener("keyup", (e) => onKey(e, false), { passive: false });

  function bindHold(el, dir) {
    if (!el) return;
    const set = (v) => {
      dirs[dir] = v;
    };
    const start = (e) => {
      e.preventDefault();
      set(true);
    };
    const end = (e) => {
      e.preventDefault();
      set(false);
    };
    el.addEventListener("pointerdown", start);
    el.addEventListener("pointerup", end);
    el.addEventListener("pointerleave", end);
    el.addEventListener("pointercancel", end);
  }

  function bindTap(el, kind) {
    if (!el) return;
    el.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      if (kind === "bomb") bombPressed = true;
      if (kind === "item") itemPressed = true;
    });
  }

  function bindTouchUI(root) {
    bindHold(root.querySelector('[data-dir="up"]'), "up");
    bindHold(root.querySelector('[data-dir="down"]'), "down");
    bindHold(root.querySelector('[data-dir="left"]'), "left");
    bindHold(root.querySelector('[data-dir="right"]'), "right");
    bindTap(root.querySelector('[data-action="bomb"]'), "bomb");
    bindTap(root.querySelector('[data-action="item"]'), "item");
  }

  function poll() {
    const bomb = bombPressed && !bombLatched;
    const item = itemPressed && !itemLatched;
    bombLatched = bombPressed;
    itemLatched = itemPressed;
    bombPressed = false;
    itemPressed = false;
    return {
      up: dirs.up,
      down: dirs.down,
      left: dirs.left,
      right: dirs.right,
      bomb,
      item,
    };
  }

  global.GameInput = { bindTouchUI, poll };
})(window);
