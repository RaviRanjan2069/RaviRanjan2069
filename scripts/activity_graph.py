"""Draw an animated line graph of the last 31 days of GitHub contributions (light and dark SVG).

Run by .github/workflows/profile-art.yml every day: python scripts/activity_graph.py <out_dir>
Needs GITHUB_TOKEN (the workflow's own token is enough) and GH_USER.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

DAYS = 31
W, H = 900, 300
LEFT, RIGHT, TOP, BOTTOM = 56, 24, 64, 46

THEMES = {
    "activity-graph.svg": {
        "bg": "#ffffff", "border": "#d0d7de", "title": "#1f2328", "muted": "#656d76",
        "grid": "#eaeef2", "line": "#2f62e8", "area": "#2f62e8", "dot_ring": "#ffffff",
    },
    "activity-graph-dark.svg": {
        "bg": "#0d1117", "border": "#30363d", "title": "#e6edf3", "muted": "#8b949e",
        "grid": "#21262d", "line": "#6b8ff5", "area": "#6b8ff5", "dot_ring": "#0d1117",
    },
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch(user: str, token: str) -> list[tuple[date, int]]:
    body = json.dumps({"query": QUERY, "variables": {"login": user}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise SystemExit(f"GitHub API error: {data['errors']}")
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [
        (date.fromisoformat(d["date"]), d["contributionCount"])
        for w in weeks
        for d in w["contributionDays"]
    ]
    return days[-DAYS:]


def nice_max(v: int) -> int:
    for step in (4, 8, 12, 20, 40, 60, 100, 200, 400, 1000):
        if v <= step:
            return step
    return v


def svg(days: list[tuple[date, int]], c: dict[str, str]) -> str:
    counts = [n for _, n in days]
    top = nice_max(max(counts) if counts else 0)
    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM
    x = [LEFT + pw * i / (len(days) - 1) for i in range(len(days))]
    y = [TOP + ph * (1 - n / top) for n in counts]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x[i]:.1f},{y[i]:.1f}" for i in range(len(days)))
    area = f"{line} L{x[-1]:.1f},{TOP + ph} L{x[0]:.1f},{TOP + ph} Z"
    total = sum(counts)
    active = sum(1 for n in counts if n)
    grid = []
    for k in range(5):
        gy = TOP + ph * k / 4
        val = round(top * (1 - k / 4))
        grid.append(f'<line x1="{LEFT}" x2="{W - RIGHT}" y1="{gy:.1f}" y2="{gy:.1f}" class="grid"/>')
        grid.append(f'<text x="{LEFT - 10}" y="{gy + 4:.1f}" text-anchor="end" class="axis">{val}</text>')
    labels = [
        f'<text x="{x[i]:.1f}" y="{H - 18}" text-anchor="middle" class="axis">{d.strftime("%d %b")}</text>'
        for i, (d, _) in enumerate(days)
        if i % 5 == 0 or i == len(days) - 1
    ]
    dots = [
        f'<circle cx="{x[i]:.1f}" cy="{y[i]:.1f}" r="4" class="dot" style="animation-delay:{0.6 + 1.8 * i / len(days):.2f}s">'
        f"<title>{d.isoformat()}: {n} contributions</title></circle>"
        for i, (d, n) in enumerate(days)
        if n
    ]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last {DAYS} days">
<style>
  .t {{ font: 600 17px 'Segoe UI', Ubuntu, sans-serif; fill: {c['title']}; }}
  .s {{ font: 400 13px 'Segoe UI', Ubuntu, sans-serif; fill: {c['muted']}; }}
  .axis {{ font: 400 11px 'Segoe UI', Ubuntu, sans-serif; fill: {c['muted']}; }}
  .grid {{ stroke: {c['grid']}; stroke-width: 1; }}
  .line {{ fill: none; stroke: {c['line']}; stroke-width: 3; stroke-linejoin: round; stroke-linecap: round;
          stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 2.4s ease-out .3s forwards; }}
  .area {{ fill: url(#fade); opacity: 0; animation: show 1s ease 1.8s forwards; }}
  .dot {{ fill: {c['line']}; stroke: {c['dot_ring']}; stroke-width: 2; opacity: 0; animation: show .4s ease forwards; }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  @keyframes show {{ to {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{ .line, .area, .dot {{ animation: none; stroke-dashoffset: 0; opacity: 1; }} }}
</style>
<defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{c['area']}" stop-opacity=".28"/><stop offset="1" stop-color="{c['area']}" stop-opacity="0"/>
</linearGradient></defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="{c['bg']}" stroke="{c['border']}"/>
<text x="{LEFT - 32}" y="34" class="t">Contribution activity</text>
<text x="{W - RIGHT}" y="34" text-anchor="end" class="s">{total} contributions · {active} active days · last {DAYS} days</text>
{''.join(grid)}
{''.join(labels)}
<path d="{area}" class="area"/>
<path d="{line}" class="line" pathLength="1"/>
{''.join(dots)}
</svg>
"""


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    out.mkdir(parents=True, exist_ok=True)
    days = fetch(os.environ["GH_USER"], os.environ["GITHUB_TOKEN"])
    for name, colours in THEMES.items():
        (out / name).write_text(svg(days, colours), encoding="utf-8")
    print(f"wrote {len(THEMES)} graphs, {sum(n for _, n in days)} contributions")


if __name__ == "__main__":
    main()
