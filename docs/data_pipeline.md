# Data Pipeline

Issue #3 owns the reproducible path from raw datasets to `dashboard/data.js`.
The default source is the workbook `Dataviz_proj_all_datasets.xlsx` (downloaded separately, not stored in git), so
teammates do not need temporary local CSV files to rebuild the dashboard.

## Run

```bash
python3 scripts/build_dashboard_data.py
```

Optional faster CSV mode:

```bash
python3 scripts/build_dashboard_data.py --source-dir /path/to/raw_csvs
```

The script validates required columns before building the output. It fails early
if a source file or required field is missing.

## Source Tables Used

| Logical table | Workbook sheet | CSV file |
| --- | --- | --- |
| customers | `customers_dataset` | `customers_dataset.csv` |
| sellers | `sellers_dataset` | `sellers_dataset.csv` |
| orders | `orders_dataset` | `orders_dataset.csv` |
| items | `order_items_dataset` | `order_items_dataset.csv` |
| reviews | `order_reviews_dataset` | `order_reviews_dataset.csv` |
| products | `products_dataset` | `products_dataset.csv` |
| translation | `product_category_name_translati` | `product_category_name_translation.csv` |
| marketing leads | `marketing_qualified_leads_datas` | `marketing_qualified_leads_dataset.csv` |
| closed deals | `closed_deals` | `closed_deals_dataset.csv` |

The workbook sheet names for translation and marketing leads are truncated by the
spreadsheet format.

## Join Logic

Order-level analysis starts from `orders_dataset`, joins `customers_dataset` on
`customer_id`, and joins average review score by `order_id`.

Item-level analysis starts from `order_items_dataset`, then joins:

- `products_dataset` on `product_id`
- `orders_dataset` on `order_id`
- `customers_dataset` on `customer_id`
- `sellers_dataset` on `seller_id`
- review rollup on `order_id`

Product categories are mapped to English names with
`product_category_name_translation.csv`; missing translations fall back to the
original category and then to `unknown`.

## Derived Fields

| Field | Level | Definition |
| --- | --- | --- |
| `delivery_days` | order/item | Delivered customer date minus purchase timestamp, in days |
| `delay_days` | order/item | Delivered customer date minus estimated delivery date, in days |
| `is_delivered` | order/item | `order_status == delivered` and delivered customer date exists |
| `is_late` | order/item | Delivered order with `delay_days > 0` |
| `low_review` | order/item | Review score less than or equal to 2 |
| `one_star` | order | Review score less than or equal to 1 |
| `month` | order | Purchase timestamp converted to `YYYY-MM` |
| `weekday` | order | Purchase weekday name |
| `same_state` | item | Customer state equals seller state |
| `year` | item | Purchase timestamp year |
| `month_num` | item | Purchase timestamp month number |
| `freight_ratio` | item | Freight value divided by item price; zero price becomes missing |

## Dashboard Output

`dashboard/data.js` contains deterministic JSON assigned to
`window.DVD_DASHBOARD_DATA`. It includes:

- `metadata`: source label, source row counts, and pipeline version
- `summary`: KPI values used by the dashboard
- `reviewDistribution`
- `monthlyOrders`
- `weekdayOrders`
- `deliveryBins`
- `delayImpactSummary`
- `delayBins`
- `sameState`
- `regionalDemand`
- `regionalRisk`
- `topCategoriesByItems`
- `topCategoriesByRevenue`
- `riskCategories`
- `topStates`
- `riskStates`
- `riskSellers`
- `healthySellers`
- `growthCategories`

The output intentionally does not include a generated timestamp, so repeated
runs against the same input produce stable file content.

## Marketing Funnel Report Pipeline

Issue #10 uses a separate reproducible report builder because its seller outcome
analysis is supporting evidence rather than a core dashboard data contract:

```bash
python3 scripts/build_marketing_funnel_analysis.py
python3 scripts/build_live_report_pages.py
python3 scripts/validate_marketing_funnel_analysis.py
```

The builder reads marketing leads, closed deals, orders, order items, and reviews
from the same source workbook. It joins MQLs to closed deals by `mql_id`, then
joins closed sellers to seller-order rows by `seller_id`. Seller outcomes use a
fixed 30-day period after `won_date`; only sellers with the full period before
the final item-backed purchase timestamp are eligible.

The generated outputs are:

- `docs/eda/marketing_funnel_analysis.md`
- `docs/eda/marketing_funnel_conversion_by_origin.png`
- `dashboard/reports/marketing-funnel.html` after the live-report build

Blank and literal `unknown` marketing origins are normalized to
`Unknown / missing`. Reviews are rolled up by order and joined only to
single-seller orders for seller-origin comparisons.
