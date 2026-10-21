"""Turn the GitHub profile photo into ASCII art on a dark terminal (assets/ascii-avatar.svg).

Rows of characters draw in one after another when the image loads. Re-run after changing the
profile photo:  pip install pillow && python scripts/ascii_avatar.py
"""

from __future__ import annotations

import io
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFilter, ImageOps

USER = "RaviRanjan2069"
COLS = 84
CROP = (95, 0, 365, 360)  # head and shoulders of the 460 px photo
CHAR_ASPECT = 0.5  # a monospace character is about twice as tall as it is wide
# from empty to dense: on a dark background, dense characters read as bright
RAMP = " .'`^\",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@"
FONT, LINE_H, CHAR_W = 9, 9.4, 5.42
PAD = 18


def load_photo() -> Image.Image:
    url = f"https://avatars.githubusercontent.com/{USER}?s=460"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")


def person_mask(img: Image.Image, tolerance: int = 34) -> Image.Image:
    """White where the person is: flood-fill the plain background from the edges."""
    small = img.filter(ImageFilter.GaussianBlur(2))
    mask = Image.new("L", img.size, 255)
    marker = (255, 0, 255)
    probe = small.copy()
    w, h = img.size
    seeds = [(x, 0) for x in range(0, w, 10)] + [(0, y) for y in range(0, h * 2 // 3, 10)] + [(w - 1, y) for y in range(0, h * 2 // 3, 10)]
    for seed in seeds:
        if probe.getpixel(seed) != marker:
            ImageDraw.floodfill(probe, seed, marker, thresh=tolerance)
    px, mx = probe.load(), mask.load()
    for y in range(h):
        for x in range(w):
            if px[x, y] == marker:
                mx[x, y] = 0
    # close small holes and soften the edge
    return mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.5))


def to_ascii(img: Image.Image, mask: Image.Image) -> list[str]:
    img, mask = img.crop(CROP), mask.crop(CROP)
    rows = int(COLS * img.height / img.width * CHAR_ASPECT)
    grey = ImageOps.grayscale(img).filter(ImageFilter.UnsharpMask(radius=3, percent=180, threshold=2))
    grey = ImageOps.equalize(grey, mask=mask.point(lambda v: 255 if v > 128 else 0))
    edges = ImageOps.grayscale(img).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.8))
    g = grey.resize((COLS, rows), Image.LANCZOS)
    e = ImageOps.autocontrast(edges.resize((COLS, rows), Image.LANCZOS), cutoff=2)
    m = mask.resize((COLS, rows), Image.LANCZOS)
    lines = []
    for y in range(rows):
        row = []
        fade = 1.0 if y < rows * 0.62 else max(0.25, 1 - (y - rows * 0.62) / (rows * 0.45))
        for x in range(COLS):
            if m.getpixel((x, y)) < 160:
                row.append(" ")
                continue
            # brightness, with features (eyes, brows, mouth, hair line) pushed out by the edges
            v = (0.8 * g.getpixel((x, y)) / 255 + 0.35 * e.getpixel((x, y)) / 255) * fade
            v = min(1.0, v) ** 1.6
            row.append(RAMP[min(len(RAMP) - 1, int(v * (len(RAMP) - 1)))])
        lines.append("".join(row).rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def svg(lines: list[str]) -> str:
    w = int(COLS * CHAR_W + PAD * 2)
    h = int(len(lines) * LINE_H + PAD * 2 + 26)
    rows = []
    for i, line in enumerate(lines):
        y = PAD + 30 + i * LINE_H
        begin = 0.3 + i * 0.045
        rows.append(
            f'<text x="{PAD}" y="{y:.1f}" opacity="0" xml:space="preserve">{escape(line)}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur="0.35s" fill="freeze"/></text>'
        )
    scan_end = 0.3 + len(lines) * 0.045
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="ASCII art portrait of Ravi Ranjan">
<defs><linearGradient id="ink" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#e6edf3"/><stop offset="1" stop-color="#9fb4d0"/>
</linearGradient></defs>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
<circle cx="22" cy="18" r="5.5" fill="#ff5f57"/><circle cx="40" cy="18" r="5.5" fill="#febc2e"/><circle cx="58" cy="18" r="5.5" fill="#28c840"/>
<text x="{w / 2}" y="22" text-anchor="middle" fill="#8b949e" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="12">ravi.txt</text>
<g fill="url(#ink)" font-family="Consolas, 'SFMono-Regular', Menlo, 'DejaVu Sans Mono', monospace" font-size="{FONT}">
{chr(10).join(rows)}
</g>
<rect x="1" y="{PAD + 22}" width="{w - 2}" height="3" fill="#7dd3fc" opacity="0">
  <animate attributeName="opacity" values="0;.55;.55;0" keyTimes="0;.05;.95;1" begin="0.3s" dur="{scan_end:.2f}s" fill="freeze"/>
  <animate attributeName="y" from="{PAD + 22}" to="{h - PAD}" begin="0.3s" dur="{scan_end:.2f}s" fill="freeze"/>
</rect>
</svg>
"""


def main() -> None:
    img = load_photo()
    lines = to_ascii(img, person_mask(img))
    out = Path(__file__).resolve().parents[1] / "assets" / "ascii-avatar.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(svg(lines), encoding="utf-8")
    (out.with_suffix(".txt")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(lines)} rows)")


if __name__ == "__main__":
    main()
