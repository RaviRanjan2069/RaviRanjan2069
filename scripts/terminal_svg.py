"""Write assets/terminal.svg: a terminal window where a short intro types itself, in a loop.

Plain SVG + SMIL, so it animates inside a GitHub README image. Re-run after editing LINES:
python scripts/terminal_svg.py
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

PROMPT = "ravi@github:~$ "
# (kind, text): "cmd" lines type after the prompt, "out" lines appear as output
LINES = [
    ("cmd", "whoami"),
    ("out", "Ravi Ranjan · Full-stack + AI developer"),
    ("out", "Noida, India"),
    ("cmd", "cat stack.txt"),
    ("out", "Java · Python · JavaScript"),
    ("out", "Spring Boot · FastAPI · MongoDB"),
    ("cmd", "mentora --status"),
    ("ok", "● live → mentora-sdlb.onrender.com/app"),
    ("cmd", "leetcode --user"),
    ("out", "Raviranjan2069"),
    ("cmd", "echo $NOW"),
    ("out", "Shipping features, one commit at a time."),
]

# sized to sit beside the ASCII portrait at the same height
W, H, LINE_H, FONT = 440, 400, 24, 13
CHAR_W = FONT * 0.62
TOP, LEFT = 60, 20
CYCLE = 18.0  # seconds for the whole loop
TYPE_PER_CHAR = 0.055
OUT_TIME = 0.25
PAUSE = 0.35

COLOURS = {"prompt": "#4ade80", "cmd": "#e6edf3", "out": "#9da7b3", "ok": "#7dd3fc"}


def build() -> str:
    h = H
    parts: list[str] = []
    clips: list[str] = []
    t = 0.6
    for i, (kind, text) in enumerate(LINES):
        y = TOP + LINE_H * i
        if kind == "cmd":
            full = PROMPT + text
            start_w = len(PROMPT) * CHAR_W
            dur = len(text) * TYPE_PER_CHAR
            spans = (
                f'<tspan fill="{COLOURS["prompt"]}">{escape(PROMPT)}</tspan>'
                f'<tspan fill="{COLOURS["cmd"]}">{escape(text)}</tspan>'
            )
        else:
            full = text
            start_w = 0.0
            dur = OUT_TIME
            spans = f'<tspan fill="{COLOURS[kind]}">{escape(text)}</tspan>'
        end_w = len(full) * CHAR_W + 12
        k0, k1 = t / CYCLE, (t + dur) / CYCLE
        clips.append(
            f'<clipPath id="c{i}"><rect x="{LEFT}" y="{y - FONT - 4}" height="{LINE_H}" width="0">'
            f'<animate attributeName="width" dur="{CYCLE}s" repeatCount="indefinite" '
            f'keyTimes="0;{k0:.4f};{k0 + 0.0001:.4f};{k1:.4f};0.97;1" '
            f'values="0;0;{start_w:.1f};{end_w:.1f};{end_w:.1f};0"/></rect></clipPath>'
        )
        parts.append(f'<text x="{LEFT}" y="{y}" clip-path="url(#c{i})">{spans}</text>')
        t += dur + PAUSE
    # the final prompt with a blinking cursor
    y = TOP + LINE_H * len(LINES)
    k = t / CYCLE
    cursor_x = LEFT + len(PROMPT) * CHAR_W + 2
    parts.append(
        f'<g opacity="0"><animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
        f'keyTimes="0;{k:.4f};{k + 0.0001:.4f};0.97;1" values="0;0;1;1;0"/>'
        f'<text x="{LEFT}" y="{y}" fill="{COLOURS["prompt"]}">{escape(PROMPT)}</text>'
        f'<rect x="{cursor_x:.1f}" y="{y - FONT + 1}" width="9" height="{FONT + 2}" fill="{COLOURS["cmd"]}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect></g>'
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="Terminal: Ravi Ranjan, full-stack and AI developer">
<defs>{''.join(clips)}</defs>
<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="34" rx="12" fill="#161b22"/>
<rect x="0.5" y="22" width="{W - 1}" height="13" fill="#161b22"/>
<line x1="0" x2="{W}" y1="35" y2="35" stroke="#30363d"/>
<circle cx="22" cy="18" r="6" fill="#ff5f57"/><circle cx="42" cy="18" r="6" fill="#febc2e"/><circle cx="62" cy="18" r="6" fill="#28c840"/>
<text x="{W / 2}" y="22" text-anchor="middle" fill="#8b949e" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="12">ravi@github: ~</text>
<g font-family="Consolas, 'SFMono-Regular', Menlo, 'DejaVu Sans Mono', monospace" font-size="{FONT}">
{chr(10).join(parts)}
</g>
</svg>
"""


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "assets" / "terminal.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print("wrote", out)
