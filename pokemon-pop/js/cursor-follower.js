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

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!window.matchMedia("(pointer: fine)").matches) return;

  var img = document.createElement("img");
  img.className = "cursor-follower";
  img.alt = "";
  img.decoding = "async";
  img.draggable = false;
  img.src = SPRITES[Math.floor(Math.random() * SPRITES.length)];
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
})();
