# Local Metabase dashboards (Group 3)

A hi-fi, interactive version of the weekly-tracking dashboards from the team
brief (`Dashboard.pdf`, courtesy Durga Prasad): one consolidated dashboard with
three tabs — **Overview** (common panel), **Product**, and **Seller** — driven by
a shared **Week (Mon)** filter with this-week / previous-week / best-week
comparisons. Charts are sized to the full page width.

Data comes from the same validated pipeline as the report and the static
dashboard, so the numbers match (`build_metabase_tables.py` reuses
`build_dashboard_data.py`).

## Stack

- **Postgres** (`dvd-postgres`, port 5433) — holds `order_base`, `item_base`
  and the analytical views in `marts.sql`.
- **Metabase** (`dvd-metabase`, http://localhost:3000) — dashboards + cards.
- Both on the `dvd-net` Docker network; Metabase reaches Postgres as host
  `dvd-postgres:5432`.

Admin login: `admin@dvd.local` / `Dvdproj123!`

## Rebuild from scratch

```bash
# 1. Export the cleaned master tables + seller coordinates to CSV
python3 scripts/build_metabase_tables.py   # order_base + item_base
python3 scripts/build_seller_geo.py        # seller_geo (for alternative-seller suggestions)

# 2. Start Postgres + Metabase and load schema.sql (data) + marts.sql + geo_marts.sql (views)
bash metabase/setup_stack.sh
docker cp metabase/marts.sql dvd-postgres:/marts.sql
docker exec dvd-postgres psql -U olist -d olist -f /marts.sql
docker cp metabase/geo_marts.sql dvd-postgres:/geo_marts.sql
docker exec dvd-postgres psql -U olist -d olist -f /geo_marts.sql

# 3. Wait ~1-2 min for Metabase to boot, then register the map + build the dashboard
python3 metabase/register_map.py   # register the Brazil-states choropleth GeoJSON
python3 metabase/provision.py      # build the one tabbed dashboard (Overview/Product/Seller)
```

The dashboard has a **Week** filter and a **State** cross-filter (dropdown, or
click a state on the map / bar) that filters the Overview KPIs and volume trend.
The Seller tab suggests, for each seller doing poorly this week, the nearest
healthy seller selling the same category (haversine on `seller_geo`).

`provision.py` is one-shot but archives any earlier `Group 3 ·` dashboard on each
run, so re-running is safe (it leaves the newest one active).

## Share with teammates (public read-only link via Cloudflare tunnel)

```bash
bash metabase/publish.sh        # prints a https://<...>.trycloudflare.com public link
bash metabase/publish.sh stop   # stop sharing
```

## Restart after a reboot

```bash
docker start dvd-postgres dvd-metabase
```

## Definitions (match the metric dictionary)

- **Intervention sellers** = `riskSellers`: ≥ 50 orders and (avg review < 3.8 OR
  late rate > 14% OR low-review rate > 20%). 103 sellers.
- **Tracked categories** = `riskCategories` eligibility: ≥ 500 items. 30 categories.
- **Late / delivered / review** metrics are order-grain; revenue and per-seller /
  per-category volume are item-grain, matching the report.

## Notes

- Metabase also ships a built-in "Sample Database" with demo cards — unrelated to
  this project (our cards are all on the "Olist marketplace" database). Remove it
  under Admin → Databases if you want a clean instance.
- The default selected week is `2018-08-13` (a full, representative week).
