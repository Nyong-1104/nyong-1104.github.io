/** Pixel sprite that follows the mouse (fine pointer only). */
(function () {
  var SPRITES = [
    "./assets/cursor-follower-bulbasaur.png",
    "./assets/cursor-follower-pokeball.png",
    "./assets/cursor-follower-charmander.png",
    "./assets/cursor-follower-squirtle.png",
    "./assets/cursor-follower-pikachu.png",
  ];
  var OFFSET_X = 14;
  var OFFSET_Y = 14;
  var LERP = 0.22;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!window.matchMedia("(pointer: fine)").matches) return;

  var img = document.createElement("img");
  img.className = "cursor-follower";
  img.alt = "";
  img.decoding = "async";
  img.draggable = false;
  img.src = SPRITES[Math.floor(Math.random() * SPRITES.length)];
  document.body.appendChild(img);

  var targetX = -9999;
  var targetY = -9999;
  var curX = targetX;
  var curY = targetY;
  var visible = false;
  var raf = 0;

  function tick() {
    raf = 0;
    curX += (targetX - curX) * LERP;
    curY += (targetY - curY) * LERP;
    img.style.transform =
      "translate3d(" + Math.round(curX) + "px," + Math.round(curY) + "px,0)";
    if (
      Math.abs(targetX - curX) > 0.4 ||
      Math.abs(targetY - curY) > 0.4
    ) {
      raf = requestAnimationFrame(tick);
    }
  }

  function schedule() {
    if (!raf) raf = requestAnimationFrame(tick);
  }

  window.addEventListener(
    "mousemove",
    function (e) {
      targetX = e.clientX + OFFSET_X;
      targetY = e.clientY + OFFSET_Y;
      if (!visible) {
        visible = true;
        curX = targetX;
        curY = targetY;
        img.classList.add("is-visible");
        img.style.transform =
          "translate3d(" + curX + "px," + curY + "px,0)";
      }
      schedule();
    },
    { passive: true }
  );
})();
