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

  function clearDirs() {
    dirs.up = false;
    dirs.down = false;
    dirs.left = false;
    dirs.right = false;
  }

  function bindJoystick(root) {
    if (!root) return;
    const knob = root.querySelector(".joystick__knob") || document.getElementById("move-joystick-knob");
    const maxR = 46;
    const dead = 0.28;
    let pointerId = null;
    let originX = 0;
    let originY = 0;

    function setKnob(nx, ny) {
      if (!knob) return;
      knob.style.transform = `translate(calc(-50% + ${nx * maxR}px), calc(-50% + ${ny * maxR}px))`;
    }

    function applyVector(dx, dy) {
      const len = Math.hypot(dx, dy) || 1;
      let nx = dx / len;
      let ny = dy / len;
      const mag = Math.min(1, Math.hypot(dx, dy) / maxR);
      if (mag < dead) {
        clearDirs();
        setKnob(0, 0);
        return;
      }
      nx *= mag;
      ny *= mag;
      dirs.left = nx < -dead;
      dirs.right = nx > dead;
      dirs.up = ny < -dead;
      dirs.down = ny > dead;
      setKnob(nx, ny);
    }

    function endStick(e) {
      if (pointerId == null || e.pointerId !== pointerId) return;
      pointerId = null;
      clearDirs();
      setKnob(0, 0);
      try {
        root.releasePointerCapture(e.pointerId);
      } catch {
        /* ignore */
      }
    }

    root.addEventListener(
      "pointerdown",
      (e) => {
        e.preventDefault();
        pointerId = e.pointerId;
        const rect = root.getBoundingClientRect();
        originX = rect.left + rect.width / 2;
        originY = rect.top + rect.height / 2;
        try {
          root.setPointerCapture(e.pointerId);
        } catch {
          /* ignore */
        }
        applyVector(e.clientX - originX, e.clientY - originY);
      },
      { passive: false }
    );

    root.addEventListener(
      "pointermove",
      (e) => {
        if (pointerId == null || e.pointerId !== pointerId) return;
        e.preventDefault();
        applyVector(e.clientX - originX, e.clientY - originY);
      },
      { passive: false }
    );

    root.addEventListener("pointerup", endStick);
    root.addEventListener("pointercancel", endStick);
    root.addEventListener("lostpointercapture", () => {
      pointerId = null;
      clearDirs();
      setKnob(0, 0);
    });
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
    if (!root) return;
    bindJoystick(root.querySelector("#move-joystick") || root.querySelector(".joystick"));
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
