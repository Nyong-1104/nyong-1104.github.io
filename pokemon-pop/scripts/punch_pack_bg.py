from PIL import Image
from pathlib import Path

assets = Path(r"C:\Users\User\nyong-app\nyong-1104.github.io\pokemon-pop\assets")


def punch_black(path: Path, threshold: int = 28) -> None:
    im = Image.open(path).convert("RGBA")
    pixels = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r <= threshold and g <= threshold and b <= threshold:
                pixels[x, y] = (r, g, b, 0)
    bbox = im.getbbox()
    if bbox:
        pad = 4
        l, t, r2, b2 = bbox
        l = max(0, l - pad)
        t = max(0, t - pad)
        r2 = min(w, r2 + pad)
        b2 = min(h, b2 + pad)
        im = im.crop((l, t, r2, b2))
    im.save(path, "PNG")
    print(path.name, "->", im.size)


for name in ("pack-151.png", "pack-pokekyun.png"):
    punch_black(assets / name)
