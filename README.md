# Dataviz-project-Group3

Group 3 · IIT Madras BS · Data Visualization Design Project. A visual study of a
Brazilian e-commerce marketplace's order journey — placement, seller handling,
freight, delivery and review — to help the marketplace **grow without breaking
the customer experience**.

Live dashboard: https://22f3002680.github.io/Dataviz-project-Group3/

## Project scope

See `docs/project_scope.md` for the business goal, the final analysis questions,
core metrics, planned visuals, and the dashboard/report mapping.

## Repository structure

| Path | What it is |
| --- | --- |
| `dashboard/` | Static GitHub Pages dashboard (Overview, Delivery, Categories, Regions, Sellers, Growth) reading precomputed `dashboard/data.js`. |
| `metabase/` | Local **weekly-tracking** dashboards on Postgres + Metabase (one tabbed dashboard, Week filter, State cross-filter, Brazil choropleth, alternative-seller suggestions). See `metabase/README.md`. |
| `webapp/` | Custom **interactive dashboard** — Next.js + Tailwind + Apache ECharts, reading live from the same Postgres via API routes. See `webapp/README.md`. |
| `scripts/` | Reproducible pipeline: build the cleaned tables, dashboard data, EDA reports, and validators. |
| `docs/` | Project scope, metric dictionary, data pipeline, data-quality audit, dashboard QA, and per-theme EDA writeups (`docs/eda/`). |
| `location_analysis/` | Geographic supply-gap EDA notebook (issue 7). |
| `*.ipynb` | Exploratory notebooks contributed per work package. |

The source workbook `Dataviz_proj_all_datasets.xlsx` is **not** stored in git
(too large); download it separately and place it at the repo root for the
pipeline scripts to read.

## Analysis & documentation

- `docs/project_scope.md` — scope, questions, success metrics
- `docs/metric_dictionary.md` — validated metric definitions and thresholds
- `docs/data_pipeline.md` — cleaning, joins, derived fields
- `docs/data_quality_audit.md` — schema/join audit and cleaning decisions
- `docs/eda/order_journey_eda.md` — baseline order-journey EDA
- `docs/eda/delivery_delay_impact.md` — delivery delay vs review impact
- `docs/eda/regional_analysis.md` — regional demand and delivery risk
- `docs/eda/marketing_funnel_analysis.md` — MQL conversion and seller linkage
- `docs/dashboard_qa.md` — dashboard interaction/accessibility/deployment checks

## Dashboards

**1. Static (published):** the GitHub Pages site in `dashboard/`, built from
`dashboard/data.js`.

**2. Metabase (local, weekly tracking):** Postgres + Metabase stack under
`metabase/` — one tabbed dashboard (Overview / Product / Seller) with a Week
filter, a click-to-filter State cross-filter, a Brazil late-delivery choropleth,
and nearest-healthy-alternative-seller suggestions. Setup in `metabase/README.md`.

**3. Next.js + ECharts (local, interactive):** the app under `webapp/` reads live
from the same Postgres and adds per-plot zoom/enlarge, cross-filtering, and a
design-principles palette. Setup in `webapp/README.md`.

Both local dashboards can be shared via a Cloudflare quick tunnel
(`metabase/publish.sh`, `webapp/publish.sh`).

## Rebuild the data

The published dashboard reads precomputed data from `dashboard/data.js`:

```bash
python3 scripts/build_dashboard_data.py                    # from the workbook
python3 scripts/build_dashboard_data.py --source-dir CSVS  # faster, from CSVs
```

Analytical tables for the local dashboards (Postgres):

```bash
python3 scripts/build_metabase_tables.py   # cleaned order/item master tables
python3 scripts/build_seller_geo.py        # seller coordinates (alt-seller feature)
```

## Reproduce EDA reports & validate

```bash
python3 scripts/build_order_journey_eda.py
python3 scripts/build_delivery_delay_analysis.py
python3 scripts/build_regional_analysis.py
python3 scripts/build_marketing_funnel_analysis.py
python3 scripts/build_live_report_pages.py
python3 scripts/validate_dashboard_metrics.py
python3 scripts/validate_marketing_funnel_analysis.py
```

Live reports: https://22f3002680.github.io/Dataviz-project-Group3/reports/index.html

## Final deliverables

- [Final technical report (Google Docs)](https://docs.google.com/document/d/10zrbGT52cCArMm5L8SqdSxQ9qCn2YxASzopuL5tOMks/edit)
- [Final presentation (Google Slides)](https://docs.google.com/presentation/d/10aYpiZmsREwXdvXY38dQX9lBCxzdiKlOF7JN3HLp0xU/edit)
- [Interactive dashboard](https://22f3002680.github.io/Dataviz-project-Group3/)
- [Supporting analysis reports](https://22f3002680.github.io/Dataviz-project-Group3/reports/index.html)
