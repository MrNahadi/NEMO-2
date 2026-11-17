"""Draw the two toolbar icons for the Fusion connector (16 and 32 px, plus 2x)."""

from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1] / "fusion" / "NEMOConnector" / "resources"
INK = (40, 44, 52, 255)
BLUE = (0, 112, 214, 255)


def check_icon(size: int) -> Image.Image:
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = max(4, s // 10)
    # padeye outline with a hole
    d.polygon([(s * 0.12, s * 0.88), (s * 0.88, s * 0.88), (s * 0.66, s * 0.42), (s * 0.34, s * 0.42)], outline=INK, width=w)
    d.ellipse([s * 0.28, s * 0.12, s * 0.72, s * 0.56], outline=INK, width=w)
    d.line([(s * 0.48, s * 0.7), (s * 0.6, s * 0.82), (s * 0.9, s * 0.5)], fill=BLUE, width=w + 2, joint="curve")
    return img.resize((size, size), Image.LANCZOS)


def sheet_icon(size: int) -> Image.Image:
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w = max(4, s // 10)
    d.rounded_rectangle([s * 0.18, s * 0.08, s * 0.82, s * 0.92], radius=s * 0.08, outline=INK, width=w)
    for y in (0.32, 0.5, 0.68):
        d.line([(s * 0.32, s * y), (s * 0.68, s * y)], fill=BLUE if y == 0.32 else INK, width=w)
    return img.resize((size, size), Image.LANCZOS)


for folder, draw in (("NEMOConnectorCheck", check_icon), ("NEMOConnectorSheetCmd", sheet_icon)):
    out = root / folder
    out.mkdir(parents=True, exist_ok=True)
    for size, name in ((16, "16x16.png"), (32, "32x32.png"), (32, "16x16@2x.png"), (64, "32x32@2x.png")):
        draw(size).save(out / name)
    print("wrote", out)
