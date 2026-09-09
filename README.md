# Marketplace Dashboard — Group 3

An interactive dashboard for a Brazilian e-commerce marketplace, built with
**Next.js + Tailwind + Apache ECharts** on top of a **PostgreSQL** database.
It has three sections — **Overview, Product, Seller** — with a week slider, a
click-to-filter state map, and live charts.

**Live demo:** https://pubmed-dui-necessity-barnes.trycloudflare.com
*(temporary Cloudflare link — it changes when the app is relaunched)*

---

## Get started (from scratch)

**You need:** Docker, Node.js 18+, and Python 3. The dataset workbook
(`Dataviz_proj_all_datasets.xlsx`) is included in the repo, so cloning is all you
need.

```bash
# 1. Clone
git clone https://github.com/22f3002680/Dataviz-project-Group3.git
cd Dataviz-project-Group3

# 2. Install the Python dependencies
pip install -r requirements.txt

# 3. Build the data and start the database (PostgreSQL in Docker)
python3 scripts/build_metabase_tables.py     # cleaned order/item tables
python3 scripts/build_seller_geo.py          # seller locations
bash metabase/setup_stack.sh                 # starts Postgres
for f in marts geo_marts materialize; do
  docker cp metabase/$f.sql dvd-postgres:/$f.sql
  docker exec dvd-postgres psql -U olist -d olist -f /$f.sql
done

# 4. Run the web app
cd webapp
cp .env.example .env.local
npm install
npm run dev
```

Open **http://localhost:3001**.

To share it on a public link (Cloudflare tunnel): `bash webapp/publish.sh`
(stop with `bash webapp/publish.sh stop`).

---

## How it works

- **Frontend** (`webapp/app`, `webapp/lib`, `webapp/components`) — a Next.js app.
  Each section calls an API route (`/api/overview`, `/api/product`, `/api/seller`)
  and draws the results with Apache ECharts. The week slider and state filter are
  just query parameters sent to those routes.
- **Backend** (`webapp/lib/db.ts`, `webapp/lib/queries.ts`) — the API routes run
  parameterised SQL against **PostgreSQL** and return only the slice each chart
  needs, so filtering is live.
- **Database** — two core tables, `order_base` (one row per order) and
  `item_base` (one row per order item), plus pre-aggregated views
  (`weekly_overview`, `weekly_category`, `weekly_seller`, `seller_stats`,
  `category_stats`, `seller_alternatives`, …) that keep the queries fast.
- **Data** comes from the marketplace workbook, cleaned by the scripts in
  `scripts/` into the tables above.
