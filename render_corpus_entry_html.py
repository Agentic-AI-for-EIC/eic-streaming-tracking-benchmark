#!/usr/bin/env python3
"""Render a single MLCommons corpus-entry YAML (the one-item-list format produced by
benchmark-builder's "Generate an MLCommons corpus entry" step) as a standalone HTML page,
styled after https://mlcommons-science.github.io/benchmark/'s individual benchmark pages
(e.g. .../md/benchmarks/jet_classification/): title, breadcrumb, metadata, resources,
keywords, citation, ratings table + average + endorsement badge, and a 6-axis rating
radar chart as inline SVG. No external assets, no build step.

Usage:
    python render_corpus_entry_html.py entry.yaml --out benchmark.html
"""

import argparse
import html
import math
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Missing dependency: pyyaml. Install it with `pip install pyyaml` and re-run.")

RADAR_ORDER = [
    ("software", "Software"),
    ("specification", "Specification"),
    ("dataset", "Dataset"),
    ("metrics", "Metrics"),
    ("reference_solution", "Reference Solution"),
    ("documentation", "Documentation"),
]


def _esc(v):
    return html.escape(str(v)) if v is not None else ""


def _radar_svg(ratings, size=360, max_score=5.0):
    n = len(RADAR_ORDER)
    cx = cy = size / 2
    radius = size * 0.36
    label_radius = size * 0.46

    def point(i, r):
        angle = -math.pi / 2 + i * (2 * math.pi / n)
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    rings = []
    for level in range(1, int(max_score) + 1):
        r = radius * (level / max_score)
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, r) for i in range(n)))
        rings.append(f'<polygon points="{pts}" fill="none" stroke="var(--radar-grid)" stroke-width="1"/>')

    axes = []
    for i in range(n):
        x, y = point(i, radius)
        axes.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="var(--radar-grid)" stroke-width="1"/>')

    data_pts = []
    for i, (key, _) in enumerate(RADAR_ORDER):
        score = (ratings.get(key) or {}).get("rating") or 0.0
        r = radius * (min(max(score, 0), max_score) / max_score)
        data_pts.append(point(i, r))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_pts)
    data_polygon = f'<polygon points="{poly}" fill="var(--radar-fill)" fill-opacity="0.35" stroke="var(--radar-stroke)" stroke-width="2"/>'
    data_dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="var(--radar-stroke)"/>' for x, y in data_pts)

    labels = []
    for i, (key, short) in enumerate(RADAR_ORDER):
        x, y = point(i, label_radius)
        anchor = "middle"
        if x < cx - 5:
            anchor = "end"
        elif x > cx + 5:
            anchor = "start"
        score = (ratings.get(key) or {}).get("rating") or 0.0
        labels.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" dominant-baseline="middle" class="radar-label">'
            f"{_esc(short)} ({score:.1f})</text>"
        )

    return (
        f'<svg viewBox="0 0 {size} {size}" width="100%" height="auto" role="img" aria-label="Rating radar chart">'
        + "".join(rings) + "".join(axes) + data_polygon + data_dots + "".join(labels) + "</svg>"
    )


def _tag_list(items):
    return "".join(f'<span class="tag">{_esc(i)}</span>' for i in (items or []))


def _resource_links(entry):
    rows = []
    if entry.get("url"):
        rows.append(f'<li><strong>Benchmark:</strong> <a href="{_esc(entry["url"])}">{_esc(entry["url"])}</a></li>')
    for d in (entry.get("datasets") or {}).get("links", []):
        if d.get("url"):
            rows.append(f'<li><strong>Dataset:</strong> <a href="{_esc(d["url"])}">{_esc(d.get("name") or d["url"])}</a></li>')
    for r in (entry.get("results") or {}).get("links", []):
        if r.get("url"):
            rows.append(f'<li><strong>Results:</strong> <a href="{_esc(r["url"])}">{_esc(r.get("name") or r["url"])}</a></li>')
    return "".join(rows)


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #f6f7f9;
    --surface: #ffffff;
    --fg: #1a2027;
    --muted: #5c6773;
    --border: #dde1e7;
    --accent: #2f5aa8;
    --accent-fg: #ffffff;
    --accent-bg: #e9eefb;
    --card-bg: #eef1f6;
    --radar-grid: #d3d9e2;
    --radar-fill: #2f5aa8;
    --radar-stroke: #1f3f7d;
    --good-bg: #e4f3e8;
    --good-fg: #1e6b3a;
    --warn-bg: #fdf1de;
    --warn-fg: #8a5a12;
    --warn-border: #f0d6a8;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #11151b; --surface: #171c24; --fg: #e7eaf0; --muted: #94a0b0; --border: #2a313c;
      --accent: #8faeef; --accent-fg: #0d1520; --accent-bg: #1c2740; --card-bg: #1a212b;
      --radar-grid: #333c48; --radar-fill: #8faeef; --radar-stroke: #b9cdfa;
      --good-bg: #133322; --good-fg: #7fdba0;
      --warn-bg: #33270f; --warn-fg: #f0c264; --warn-border: #55401a;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #11151b; --surface: #171c24; --fg: #e7eaf0; --muted: #94a0b0; --border: #2a313c;
    --accent: #8faeef; --accent-fg: #0d1520; --accent-bg: #1c2740; --card-bg: #1a212b;
    --radar-grid: #333c48; --radar-fill: #8faeef; --radar-stroke: #b9cdfa;
    --good-bg: #133322; --good-fg: #7fdba0;
    --warn-bg: #33270f; --warn-fg: #f0c264; --warn-border: #55401a;
  }}
  * {{ box-sizing: border-box; }}
  html {{ background: var(--bg); }}
  body {{
    margin: 0; background: var(--bg); color: var(--fg);
    font-family: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6; -webkit-font-smoothing: antialiased;
  }}
  .wrap {{ max-width: 780px; margin: 0 auto; padding: 3rem 1.5rem 4.5rem; }}
  .breadcrumb {{
    font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 1.5rem;
  }}
  .breadcrumb a {{ color: var(--muted); text-decoration: none; }}
  .breadcrumb a:hover {{ color: var(--accent); }}
  .eyebrow {{
    font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 0.72rem;
    text-transform: uppercase; letter-spacing: 0.1em; color: var(--accent); margin: 0 0 0.6rem;
  }}
  h1 {{ font-size: 2.1rem; font-weight: 700; margin: 0 0 0.5rem; text-wrap: balance; letter-spacing: -0.01em; }}
  .focus {{ color: var(--muted); font-size: 1.08rem; margin: 0 0 1.25rem; max-width: 62ch; text-wrap: pretty; }}
  .draft-banner {{
    background: var(--warn-bg); color: var(--warn-fg); border: 1px solid var(--warn-border);
    border-radius: 8px; padding: 0.8rem 1rem; font-size: 0.88rem; margin: 0 0 1.75rem;
  }}
  h2 {{
    font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 0.82rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted);
    border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin: 2.5rem 0 1.1rem;
  }}
  .meta-grid {{ display: grid; grid-template-columns: minmax(0,11rem) 1fr; row-gap: 0.6rem; column-gap: 1.25rem; font-size: 0.95rem; }}
  .meta-grid dt {{ color: var(--muted); font-weight: 500; }}
  .meta-grid dd {{ margin: 0; }}
  ul.resource-list {{ list-style: none; padding: 0; margin: 0; font-size: 0.95rem; display: flex; flex-direction: column; gap: 0.5rem; }}
  ul.resource-list li {{ word-break: break-word; }}
  ul.resource-list strong {{ font-weight: 500; color: var(--muted); }}
  a {{ color: var(--accent); }}
  .tag {{
    display: inline-block; background: var(--accent-bg); color: var(--accent); border-radius: 4px;
    padding: 0.25rem 0.6rem; font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 0.78rem;
    margin: 0 0.4rem 0.4rem 0;
  }}
  p.summary {{ font-size: 0.98rem; max-width: 66ch; text-wrap: pretty; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; margin-top: 0.25rem; }}
  th, td {{ text-align: left; padding: 0.6rem 0.7rem; border-bottom: 1px solid var(--border); vertical-align: top; }}
  th {{ color: var(--muted); font-weight: 600; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
    font-family: "IBM Plex Mono", ui-monospace, monospace; }}
  .score-cell {{ font-family: "IBM Plex Mono", ui-monospace, monospace; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  .avg-row td {{ font-weight: 700; border-top: 2px solid var(--border); border-bottom: none; }}
  .table-scroll {{ overflow-x: auto; }}
  .endorsed {{
    display: inline-block; margin-top: 0.85rem; padding: 0.4rem 0.85rem; border-radius: 6px;
    font-size: 0.82rem; font-weight: 600; font-family: "IBM Plex Mono", ui-monospace, monospace;
  }}
  .endorsed.yes {{ background: var(--good-bg); color: var(--good-fg); }}
  .endorsed.no {{ background: var(--card-bg); color: var(--muted); border: 1px solid var(--border); }}
  .radar-wrap {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 1.5rem; max-width: 420px; margin: 0.5rem auto 0;
  }}
  .radar-label {{ font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 10px; fill: var(--fg); }}
  pre.citation {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px;
    padding: 1rem; font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 0.78rem;
    overflow-x: auto; white-space: pre-wrap; word-break: break-word; line-height: 1.5;
  }}
  footer {{ margin-top: 3.5rem; padding-top: 1.25rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.8rem; }}
  a:focus-visible, .breadcrumb a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 2px; }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; transition: none !important; }} }}
</style>
</head>
<body>
<div class="wrap">
  <div class="breadcrumb"><a href="https://mlcommons-science.github.io/benchmark/md/benchmarks/">&larr; All benchmarks</a></div>
  <p class="eyebrow">{domain_eyebrow} &middot; Benchmark</p>
  <h1>{name}</h1>
  <p class="focus">{focus}</p>
  {draft_banner}

  <h2>Summary</h2>
  <p class="summary">{summary}</p>

  <h2>Metadata</h2>
  <dl class="meta-grid">
    <dt>Date</dt><dd>{date}</dd>
    <dt>Version</dt><dd>{version}</dd>
    <dt>Domain</dt><dd>{domain}</dd>
    <dt>Task Types</dt><dd>{task_types}</dd>
    <dt>Metrics</dt><dd>{metrics}</dd>
    <dt>Models</dt><dd>{models}</dd>
    <dt>AI/ML Motif</dt><dd>{ml_motif}</dd>
    <dt>Learning Paradigm</dt><dd>{ml_task}</dd>
    <dt>AI Capability Measured</dt><dd>{ai_capability_measured}</dd>
    <dt>License</dt><dd>{licensing}</dd>
  </dl>

  <h2>Resources</h2>
  <ul class="resource-list">
    {resource_links}
  </ul>

  <h2>Keywords</h2>
  <div>{keywords}</div>

  <h2>Citation</h2>
  <pre class='citation'>{bibtex}</pre>

  <h2>Ratings</h2>
  <div class="table-scroll">
  <table>
    <thead><tr><th>Category</th><th>Rating</th><th>Notes</th></tr></thead>
    <tbody>
      {rating_rows}
      <tr class="avg-row"><td>Average</td><td class="score-cell">{overall:.2f} / 5</td><td></td></tr>
    </tbody>
  </table>
  </div>
  <span class="endorsed {endorsed_class}">{endorsed_text}</span>

  <h2>Rating Radar</h2>
  <div class="radar-wrap">{radar_svg}</div>

  <footer>
    Generated from an MLCommons corpus-entry YAML by benchmark-builder, styled after the
    <a href="https://mlcommons-science.github.io/benchmark/">MLCommons Science Working Group
    AI Benchmarks Collection</a>. {notes}
  </footer>
</div>
</body>
</html>
"""


def build_page(entry):
    ratings = entry.get("ratings") or {}
    scores = [(ratings.get(k) or {}).get("rating") for k, _ in RADAR_ORDER]
    scores = [s for s in scores if s is not None]
    overall = sum(scores) / len(scores) if scores else 0.0
    endorsed = overall >= 4.5

    rating_rows = []
    for key, label in RADAR_ORDER:
        r = ratings.get(key) or {}
        rating_rows.append(
            f"<tr><td>{_esc(label)}</td><td class='score-cell'>{(r.get('rating') or 0.0):.2f} / 5</td>"
            f"<td>{_esc(r.get('reason') or 'None')}</td></tr>"
        )

    valid = entry.get("valid")
    draft_banner = ""
    if valid is False:
        draft_banner = (
            "<div class='draft-banner'>Working draft &mdash; not yet verified as a "
            "reproducible, runnable benchmark (see Ratings below for specifics).</div>"
        )

    bibtex = "\n\n".join((entry.get("cite") or []))

    return PAGE_TEMPLATE.format(
        title=_esc(entry.get("name") or "(unnamed benchmark)"),
        name=_esc(entry.get("name") or "(unnamed benchmark)"),
        focus=_esc((entry.get("focus") or "").strip()),
        draft_banner=draft_banner,
        summary=_esc((entry.get("summary") or "").strip()),
        date=_esc(entry.get("date") or "—"),
        version=_esc(entry.get("version") or "—"),
        domain=_esc(", ".join(entry.get("domain") or []) or "—"),
        domain_eyebrow=_esc(", ".join(entry.get("domain") or []) or "Benchmark"),
        task_types=_esc(", ".join(entry.get("task_types") or []) or "—"),
        metrics=_esc(", ".join(entry.get("metrics") or []) or "—"),
        models=_esc(", ".join(entry.get("models") or []) or "—"),
        ml_motif=_esc(", ".join(entry.get("ml_motif") or []) or "—"),
        ml_task=_esc(", ".join(entry.get("ml_task") or []) or "—"),
        ai_capability_measured=_esc(", ".join(entry.get("ai_capability_measured") or []) or "—"),
        licensing=_esc(entry.get("licensing") or "—"),
        resource_links=_resource_links(entry) or "<li>(none listed)</li>",
        keywords=_tag_list(entry.get("keywords")) or "(none listed)",
        bibtex=_esc(bibtex) or "(no citation provided)",
        rating_rows="\n      ".join(rating_rows),
        overall=overall,
        endorsed_class="yes" if endorsed else "no",
        endorsed_text=(
            "Meets MLCommons Endorsement threshold (avg >= 4.5/5)"
            if endorsed else f"Below Endorsement threshold (avg >= 4.5/5) by {4.5 - overall:.2f}"
        ),
        radar_svg=_radar_svg(ratings),
        notes=_esc(entry.get("notes") or ""),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("entry_path", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    data = yaml.safe_load(args.entry_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        entry = data[0]
    else:
        entry = data

    args.out.write_text(build_page(entry), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
