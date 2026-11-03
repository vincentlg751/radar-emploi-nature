"""Dessine les icônes de l'application (radar + feuille). Usage : python radar-app/make_icons.py"""
import math, pathlib
from PIL import Image, ImageDraw

OUT = pathlib.Path(__file__).resolve().parent / "icons"
BG, RING, LEAF, SWEEP = (29, 102, 88), (220, 235, 229), (241, 244, 239), (98, 185, 162)


def draw(size, pad_ratio=0.0, rounded=True):
    S = 1024
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if rounded:
        d.rounded_rectangle((0, 0, S - 1, S - 1), radius=int(S * 0.22), fill=BG)
    else:
        d.rectangle((0, 0, S, S), fill=BG)
    c, scale = S / 2, 1 - pad_ratio
    R = S * 0.36 * scale
    # balayage du radar
    d.pieslice((c - R, c - R, c + R, c + R), -90, -30, fill=SWEEP)
    w = S * 0.018 * scale
    for k in (1, 0.62):
        r = R * k
        mask = Image.new("L", (S, S), 0)
        md = ImageDraw.Draw(mask)
        md.ellipse((c - r - w / 2, c - r - w / 2, c + r + w / 2, c + r + w / 2), fill=255)
        md.ellipse((c - r + w / 2, c - r + w / 2, c + r - w / 2, c + r - w / 2), fill=0)
        im.paste(Image.new("RGBA", (S, S), RING), (0, 0), mask)
    # feuille au centre (pointue aux deux bouts, nervure dans l'axe), inclinée
    L, W = R * 0.42, R * 0.2
    pts = [(c + math.sin(i / 60 * math.pi) * W, c - L + 2 * L * i / 60) for i in range(61)]
    pts += [(2 * c - x, y) for x, y in reversed(pts)]
    leaf = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(leaf)
    ld.polygon(pts, fill=LEAF)
    ld.line((c, c - L * 0.75, c, c + L * 1.25), fill=BG, width=int(S * 0.014 * scale))
    im.alpha_composite(leaf.rotate(-35, center=(c, c), resample=Image.BICUBIC))
    d = ImageDraw.Draw(im)
    # point détecté
    pr, px, py = S * 0.035 * scale, c + R * 0.62 * math.cos(math.radians(-60)), c + R * 0.62 * math.sin(math.radians(-60))
    d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=(246, 230, 211))
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    draw(192).save(OUT / "icon-192.png")
    draw(512).save(OUT / "icon-512.png")
    draw(512, pad_ratio=0.2, rounded=False).save(OUT / "icon-maskable-512.png")
    draw(180, rounded=False).convert("RGB").save(OUT / "apple-touch-icon.png")
    draw(1024, rounded=False).convert("RGB").save(OUT / "icon-1024.png")  # source des icônes natives
    print("Icônes ->", OUT)
