# Marketplace Weekly Dashboard (Next.js + ECharts)

Interactive alternative to the Metabase dashboard, built with **Next.js (App
Router)**, **Tailwind**, and **Apache ECharts**, reading **live** from the same
Postgres (`dvd-postgres`) via API routes. Applies the team's Design principles
(muted figure-ground palette, one accent for attention, rate-not-count
choropleth, direct labels, position-on-common-scale, minimal chart junk).

## Features
- Three tabs — **Overview / Product / Seller** — with a shared **Week** slider.
- **Cross-filter:** click a state on the choropleth or the orders-by-state bar
  (or use the chip) to filter the KPIs, volume, and category/seller views.
- Brazil **choropleth** of late-delivery rate; **quadrant** and **seller
  revenue-vs-satisfaction** scatters; merged orders/delayed bars; diverging
  review-change bars; **alternative-seller** suggestions (geolocation).
- Light / dark theme.

## Run
Requires the Postgres stack from `../metabase/` up (`dvd-postgres` on :5433 with
schema.sql + marts.sql + geo_marts.sql loaded).

```bash
cp .env.example .env.local     # DB connection (defaults match the local stack)
npm install
npm run dev                    # http://localhost:3001  (PORT=3001 to avoid Metabase on 3000)
# or: npm run build && PORT=3001 npm run start
```

## Structure
- `lib/db.ts` — pg pool; `lib/queries.ts` — parameterized SQL (week + optional state)
- `app/api/{meta,overview,product,seller}` — JSON endpoints
- `lib/theme.ts` — design-principles palette; `lib/charts.ts` — ECharts option builders
- `components/EChart.tsx` — canvas chart wrapper; `app/page.tsx` — dashboard UI
- `public/brazil-states.geojson` — choropleth boundaries (joined on `sigla`)
