# Dataviz-project-Group3

Group 3 · IIT Madras BS · Data Visualization Design Project.

An end-to-end study of a Brazilian e-commerce marketplace's order journey —
placement, seller handling, freight, delivery and review — built to help the
marketplace **grow without breaking the customer experience**. The repository
contains the reproducible data pipeline, the analysis, and **three dashboards**.

- **Static dashboard (published):** https://22f3002680.github.io/Dataviz-project-Group3/
- **Interactive dashboard (Next.js + ECharts):** live via a Cloudflare tunnel (URL is temporary; run locally with the steps below)

---

## Dashboards

| Dashboard | Stack | Where |
| --- | --- | --- |
| **Static** | Vanilla JS + precomputed `data.js` | `dashboard/` → GitHub Pages |
| **Weekly tracking** | Postgres + Metabase | `metabase/` |
| **Interactive** | **Next.js + Tailwind + Apache ECharts + PostgreSQL** | `webapp/` |

The interactive app has three sections — **Overview, Product, Seller** — a Week
slider, a click-to-filter State cross-filter, a Brazil late-delivery choropleth,
a week-reactive category **risk quadrant**, per-plot zoom/enlarge, and
nearest-healthy-alternative-seller suggestions. It reads **live** from PostgreSQL.

---

## Quick start — interactive dashboard (`webapp/`)

The app reads live from a PostgreSQL database, so bring the database up first.

### 1. Get the data into PostgreSQL

Requires Docker and Python 3 (`pandas`, `openpyxl`). Download the source workbook
`Dataviz_proj_all_datasets.xlsx` (not stored in git — too large) and place it at
the repo root.

```bash
# Build the cleaned analytical tables + seller coordinates as CSVs
python3 scripts/build_metabase_tables.py     # order_base + item_base
python3 scripts/build_seller_geo.py          # seller_geo (alternative-seller feature)

# Start Postgres (+ Metabase) and load the schema, marts, geo marts, and matviews
bash metabase/setup_stack.sh
for f in marts geo_marts materialize; do
  docker cp metabase/$f.sql dvd-postgres:/$f.sql
  docker exec dvd-postgres psql -U olist -d olist -f /$f.sql
done
```

This creates `order_base`, `item_base` and the derived views/tables the dashboard
queries. See `metabase/README.md` for details.

### 2. Run the app

```bash
cd webapp
cp .env.example .env.local        # DB connection (defaults match the local stack)
npm install
npm run dev                       # http://localhost:3001
# production: npm run build && PORT=3001 npm run start
```

Port 3001 is used so it does not clash with Metabase on 3000. The app connects to
Postgres on `localhost:5433` via the `PG*` variables in `.env.local`.

### 3. (Optional) share it

```bash
bash webapp/publish.sh            # serves the build + a Cloudflare quick tunnel
bash webapp/publish.sh stop       # stop sharing
```

---

## Reproduce the analysis & static dashboard

The published dashboard reads a precomputed `dashboard/data.js`:

```bash
python3 scripts/build_dashboard_data.py                    # from the workbook
python3 scripts/build_dashboard_data.py --source-dir CSVS  # faster, from extracted CSVs
```

Rebuild the EDA report pages and run the validators:

```bash
python3 scripts/build_order_journey_eda.py
python3 scripts/build_delivery_delay_analysis.py
python3 scripts/build_regional_analysis.py
python3 scripts/build_marketing_funnel_analysis.py
python3 scripts/build_live_report_pages.py
python3 scripts/validate_dashboard_metrics.py
python3 scripts/validate_marketing_funnel_analysis.py
```

All three dashboards derive from the **same validated pipeline**, so their numbers
match the report.

---

## Repository structure

```
.
├── dashboard/            # Static GitHub Pages dashboard (reads data.js)
├── webapp/               # Next.js + Tailwind + ECharts interactive dashboard (Postgres)
│   ├── app/              #   pages + API routes (/api/{meta,overview,product,seller})
│   ├── lib/              #   db pool, SQL queries, ECharts option builders, theme
│   └── components/       #   chart wrapper
├── metabase/             # Postgres + Metabase stack: schema, marts, materialize, provision
├── scripts/              # Reproducible pipeline (build tables, dashboard data, EDA, validate)
├── docs/                 # Scope, metric dictionary, data pipeline, quality audit, EDA writeups
├── location_analysis/    # Geographic supply-gap EDA notebook
├── *.ipynb               # Exploratory notebooks
└── .github/workflows/    # GitHub Pages deploy
```

## Data model

- **Source:** 9–10 raw marketplace tables in the workbook (orders, order_items,
  customers, sellers, products, reviews, category translation, marketing leads,
  closed deals; plus geolocation for the seller-distance feature).
- **Core tables:** `order_base` (one row per order) and `item_base` (one row per
  order item), built by the cleaning pipeline.
- **Derived views/tables** used by the interactive dashboard: `weekly_overview`,
  `weekly_category`, `weekly_seller`, `category_stats`, `seller_stats`,
  `intervention_sellers`, `tracked_categories`, `seller_alternatives`.

Metric definitions and thresholds are documented in `docs/metric_dictionary.md`.

## Notes

- The workbook `Dataviz_proj_all_datasets.xlsx` is downloaded separately (not in git).
- The Cloudflare tunnel URL is temporary; for a stable link use a named tunnel or
  deploy the app to a host with a reachable PostgreSQL instance.
