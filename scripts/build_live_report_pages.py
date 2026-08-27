"""Render project reports as static pages published with the dashboard."""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT_DIR / "docs" / "eda"
REPORTS_DIR = ROOT_DIR / "dashboard" / "reports"
ASSETS_DIR = REPORTS_DIR / "assets"
REPORTS = [
    ("order-journey", "Issue 5: Order journey and satisfaction", "order_journey_eda.md"),
    ("delivery-impact", "Issue 6: Delivery delay impact", "delivery_delay_impact.md"),
    ("regional-analysis", "Issue 9: Regional demand and risk", "regional_analysis.md"),
]
STATIC_REPORTS = [
    ("product-analysis", "Issue 7: Product category analysis",
     "Category demand, revenue, growth, satisfaction risk, and delivery risk.",
     "issue7_eda.ipynb", "Categories"),
    ("seller-analysis", "Issue 8: Seller performance analysis",
     "Seller intervention candidates, healthy benchmarks, geography, and operational recommendations.",
     "Issue_8_Seller_Analysis_Sourish.ipynb", "Sellers"),
]


def inline(value: str) -> str:
    value = html.escape(value, quote=False)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    return value


def markdown_to_html(text: str) -> str:
    output: list[str] = []
    in_table = False
    in_list = False

    def close_blocks() -> None:
        nonlocal in_table, in_list
        if in_table:
            output.append("</tbody></table>")
            in_table = False
        if in_list:
            output.append("</ul>")
            in_list = False

    for line in text.splitlines():
        if line.startswith(chr(96) * 3):
            close_blocks()
            continue
        if not line.strip():
            close_blocks()
            continue
        image = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line)
        if image:
            close_blocks()
            name = html.escape(Path(image.group(2)).name)
            alt = html.escape(image.group(1))
            output.append(f'<figure><img src="assets/{name}" alt="{alt}"><figcaption>{alt}</figcaption></figure>')
            continue
        if line.startswith("#"):
            close_blocks()
            level = len(line) - len(line.lstrip("#"))
            output.append(f"<h{level}>{inline(line[level:].strip())}</h{level}>")
            continue
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            if not in_table:
                close_blocks()
                output.append("<table><thead><tr>")
                output.extend(f"<th>{inline(cell)}</th>" for cell in cells)
                output.append("</tr></thead><tbody>")
                in_table = True
            else:
                output.append("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in cells) + "</tr>")
            continue
        if line.startswith("- "):
            if in_table:
                close_blocks()
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{inline(line[2:])}</li>")
            continue
        close_blocks()
        output.append(f"<p>{inline(line)}</p>")
    close_blocks()
    return "\n".join(output)


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)} | DVD Project</title>
    <link rel="stylesheet" href="./styles.css">
  </head>
  <body>
    <header class="site-header">
      <a href="../index.html">DVD Project dashboard</a>
      <nav aria-label="Report navigation"><a href="./index.html">All reports</a></nav>
    </header>
    <main class="report-page">{body}</main>
  </body>
</html>"""


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for image in DOCS_DIR.glob("*.png"):
        shutil.copy2(image, ASSETS_DIR / image.name)

    cards = [
        f'<a class="report-card" href="{slug}.html"><h2>{title}</h2><span>Read analysis and visuals</span></a>'
        for slug, title, _ in REPORTS
    ]
    cards += [
        f'<a class="report-card" href="{slug}.html"><h2>{title}</h2><span>Open analysis summary</span></a>'
        for slug, title, _, _, _ in STATIC_REPORTS
    ]
    index_body = '<p class="eyebrow">DVD Project</p><h1>Reports &amp; methods</h1><p class="lede">Detailed findings, definitions, visuals, and recommendations behind the interactive dashboard.</p><div class="report-grid">' + "".join(cards) + '</div><p class="back-link"><a href="../index.html">Back to dashboard</a></p>'
    (REPORTS_DIR / "index.html").write_text(page("Reports & methods", index_body), encoding="utf-8")

    for slug, title, source_name in REPORTS:
        body = markdown_to_html((DOCS_DIR / source_name).read_text(encoding="utf-8"))
        (REPORTS_DIR / f"{slug}.html").write_text(page(title, body), encoding="utf-8")
    repo = "https://github.com/22f3002680/Dataviz-project-Group3/blob/project-materials/"
    for slug, title, summary, notebook, tab in STATIC_REPORTS:
        body = f'<p class="eyebrow">DVD Project</p><h1>{html.escape(title)}</h1><p class="lede">{html.escape(summary)}</p><section class="callout"><h2>Published source</h2><p>The complete analysis is maintained in the merged project notebook and the dashboard {html.escape(tab)} view.</p><p><a class="button-link" href="{repo}{notebook}">Open the merged notebook on GitHub</a></p></section><p class="back-link"><a href="../index.html">Open dashboard</a></p>'
        (REPORTS_DIR / f"{slug}.html").write_text(page(title, body), encoding="utf-8")
    print(f"Built report pages in {REPORTS_DIR}")


if __name__ == "__main__":
    main()
