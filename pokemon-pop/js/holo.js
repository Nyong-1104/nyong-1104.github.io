/**
 * Pointer-driven holographic tilt — inspired by simeydotme/pokemon-cards-css
 */
window.PopTracker = window.PopTracker || {};

(function (PT) {
  function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
  }

  function round(n) {
    return Math.round(n * 100) / 100;
  }

  PT.mountHoloCard = function (root) {
    if (!root || root.dataset.holoReady) return;
    root.dataset.holoReady = "1";
    root.style.setProperty("--seed", String(Math.random()));

    let raf = null;
    let pending = null;

    const apply = (bg, rotate, glareO) => {
      root.style.setProperty("--background-x", `${bg.x}%`);
      root.style.setProperty("--background-y", `${bg.y}%`);
      root.style.setProperty("--rotate-x", `${rotate.x}deg`);
      root.style.setProperty("--rotate-y", `${rotate.y}deg`);
      root.style.setProperty("--pointer-x", `${bg.px}%`);
      root.style.setProperty("--pointer-y", `${bg.py}%`);
      root.style.setProperty("--card-opacity", String(glareO));
      const dx = bg.px - 50;
      const dy = bg.py - 50;
      const fromCenter = clamp(Math.sqrt(dx * dx + dy * dy) / 50, 0, 1);
      root.style.setProperty("--pointer-from-center", String(round(fromCenter)));
    };

    const interact = (clientX, clientY) => {
      const rect = root.getBoundingClientRect();
      const x = clamp(((clientX - rect.left) / rect.width) * 100, 0, 100);
      const y = clamp(((clientY - rect.top) / rect.height) * 100, 0, 100);
      const cx = x - 50;
      const cy = y - 50;
      pending = {
        bg: {
          x: 37 + (x / 100) * 26,
          y: 33 + (y / 100) * 34,
          px: x,
          py: y,
        },
        rotate: {
          x: round(-(cx / 3.5)),
          y: round(cy / 3.5),
        },
        o: 1,
      };
      if (raf == null) {
        raf = requestAnimationFrame(() => {
          if (pending) {
            root.classList.add("interacting");
            apply(pending.bg, pending.rotate, pending.o);
            pending = null;
          }
          raf = null;
        });
      }
    };

    const reset = () => {
      root.classList.remove("interacting");
      apply({ x: 50, y: 50, px: 50, py: 50 }, { x: 0, y: 0 }, 0);
    };

    root.addEventListener("pointermove", (e) => interact(e.clientX, e.clientY));
    root.addEventListener("pointerenter", (e) => interact(e.clientX, e.clientY));
    root.addEventListener("pointerleave", reset);
    root.addEventListener(
      "touchmove",
      (e) => {
        if (!e.touches[0]) return;
        interact(e.touches[0].clientX, e.touches[0].clientY);
      },
      { passive: true }
    );
    root.addEventListener("touchend", reset);

    reset();
  };

  PT.createHoloCardEl = function (opts) {
    const style = opts.holoStyle || "sar";
    const wrap = document.createElement("div");
    wrap.className = `holo-card holo-card--${style}${opts.compact ? " holo-card--compact" : ""}`;
    const img = document.createElement("img");
    img.className = "holo-card__img";
    img.loading = "lazy";
    img.alt = opts.name || "";
    PT.bindHoloImageFallback(img, opts.image, opts.fallbackImage, opts.onFallback);
    if (opts.image) img.src = opts.image;

    const rotator = document.createElement("div");
    rotator.className = "holo-card__rotator";
    const front = document.createElement("div");
    front.className = "holo-card__front";
    const shine = document.createElement("div");
    shine.className = "holo-card__shine";
    shine.setAttribute("aria-hidden", "true");
    const glare = document.createElement("div");
    glare.className = "holo-card__glare";
    glare.setAttribute("aria-hidden", "true");
    front.appendChild(img);
    front.appendChild(shine);
    front.appendChild(glare);
    rotator.appendChild(front);
    wrap.appendChild(rotator);
    return wrap;
  };

  PT.bindHoloImageFallback = function (img, primary, fallback, onFallback) {
    if (!img) return;
    img.onerror = null;
    if (!fallback || !primary || fallback === primary) return;
    img.onerror = function () {
      img.onerror = null;
      if (img.getAttribute("src") === fallback) return;
      img.src = fallback;
      if (typeof onFallback === "function") onFallback();
    };
  };

  PT.setHoloCardImage = function (root, image, name, opts) {
    if (!root) return;
    const img = root.querySelector(".holo-card__img");
    if (!img) return;
    opts = opts || {};
    if (name != null) img.alt = name;
    PT.bindHoloImageFallback(img, image, opts.fallbackImage, opts.onFallback);
    if (image) img.src = image;
    else if (opts.fallbackImage) img.src = opts.fallbackImage;
  };
})(window.PopTracker);
