# Data Quality Audit

Issue #2 documents how the e-commerce datasets connect, what quality risks were
found, and which cleaning decisions should be used consistently across the
dashboard, notebooks, report, and presentation.

Source materials:

- Issue #2 comment thread and linked Colab notebook
- Schema draft: https://dbdiagram.io/d/6a88811afd15a881e5d1cef4
- Current reproducible pipeline: `docs/data_pipeline.md`
- Metric definitions: `docs/metric_dictionary.md`

## Dataset Inventory

The dashboard pipeline currently consumes the committed workbook
`Dataviz_proj_all_datasets.xlsx`. Row counts below are from
`dashboard/data.js` metadata after the reproducible pipeline build.

| Dataset | Current dashboard role | Rows |
| --- | --- | ---: |
| `customers_dataset` | Customer IDs, customer city/state, regional demand | 99,441 |
| `sellers_dataset` | Seller IDs, seller city/state, seller performance | 3,095 |
| `orders_dataset` | Order status, purchase/delivery dates, delivery performance | 99,441 |
| `order_items_dataset` | Item grain, product/seller linkage, price, freight, revenue | 112,650 |
| `order_reviews_dataset` | Review score and customer satisfaction proxy | 99,224 |
| `products_dataset` | Product attributes and product category key | 32,951 |
| `product_category_name_translation` | English category labels | 71 |
| `marketing_qualified_leads_dataset` | Seller acquisition funnel leads | 8,000 |
| `closed_deals_dataset` | Won seller acquisition deals | 842 |

The Issue #2 notebook also audited `order_payments_dataset` and
`geolocation_dataset`. They are useful optional sources for payment analysis,
distance analysis, and regional mapping, but they are not currently required by
the dashboard data pipeline.

## Join Summary

LEFT JOINs are used for analytical joins so base marketplace rows are preserved.
Missing lookup attributes remain missing instead of causing row drops.

| Base table | Join key | Lookup table | Lookup key | Reported unmatched rows | Use |
| --- | --- | --- | --- | ---: | --- |
| `orders_dataset` | `customer_id` | `customers_dataset` | `customer_id` | 0 | Customer geography for orders |
| `order_items_dataset` | `order_id` | `orders_dataset` | `order_id` | 0 | Delivery/order context for item rows |
| `order_items_dataset` | `product_id` | `products_dataset` | `product_id` | 0 | Product category and attributes |
| `order_items_dataset` | `seller_id` | `sellers_dataset` | `seller_id` | 0 | Seller geography and seller metrics |
| `order_payments_dataset` | `order_id` | `orders_dataset` | `order_id` | 0 | Optional payment/order analysis |
| `order_reviews_dataset` | `order_id` | `orders_dataset` | `order_id` | 0 | Review/order analysis |
| `products_dataset` | `product_category_name` | `product_category_name_translation` | `product_category_name` | 13 rows before cleanup | English category labels |
| `customers_dataset` | `customer_zip_code_prefix` | `geolocation_dataset` | `geolocation_zip_code_prefix` | 278 | Optional customer coordinates |
| `sellers_dataset` | `seller_zip_code_prefix` | `geolocation_dataset` | `geolocation_zip_code_prefix` | 7 | Optional seller coordinates |
| `closed_deals_dataset` | `mql_id` | `marketing_qualified_leads_dataset` | `mql_id` | 0 | Lead-to-deal funnel |
| `closed_deals_dataset` | `seller_id` | `sellers_dataset` | `seller_id` | Not blocking | Optional link from acquisition to seller performance |

The final master table from the Issue #2 notebook has item-level grain:
`1 row = 1 order item`. The reported row count is 112,650, matching
`order_items_dataset`.

## Key Data Quality Findings

| Finding | Count / share | Decision |
| --- | ---: | --- |
| Core marketplace joins with missing lookup rows | 0 for customer, order, product, seller, payment, review, and MQL joins | Safe to use as primary analysis joins |
| Product category translations missing before cleanup | 13 product rows, 2 category values, about 0.04% of product-category join rows | Keep product rows; preserve original category; use documented fallback or manual mapping |
| Unmatched customer geolocation ZIP prefixes | 278, about 0.28% of customer rows | Keep customer rows; leave coordinate fields missing for unmatched ZIP prefixes |
| Unmatched seller geolocation ZIP prefixes | 7, about 0.23% of seller rows | Keep seller rows; leave coordinate fields missing for unmatched ZIP prefixes |
| `order_delivered_carrier_date < order_purchase_timestamp` | 166 orders, about 0.17% of orders | Keep order rows; flag invalid carrier timestamp; exclude invalid carrier-stage duration from pickup-time metrics |
| Major carrier timestamp anomaly | 2 orders more than 24 hours early | Treat as the severe subset of the 6 records more than 2 hours early |
| Duplicate final master-table keys | 0 duplicate `(order_id, order_item_id)` keys | Item-level master table is stable for item/category/seller analysis |

Timestamp anomaly buckets should be read as:

- 160 records are less than or equal to 2 hours early.
- 6 records are more than 2 hours early.
- The 2 records more than 24 hours early are included inside those 6 records.
- Total affected records: 160 + 6 = 166.

## Cleaning Decisions

### Invalid Carrier Timestamps

Do not delete the full row when `order_delivered_carrier_date` is earlier than
`order_purchase_timestamp`. The affected records are a small share of all
orders and can still be valid for revenue, category, seller, customer, review,
estimated-delivery, and final customer-delivery analysis.

Policy:

- Preserve raw timestamp columns.
- Add a flag such as `carrier_date_was_invalid` or
  `invalid_carrier_before_purchase`.
- Set invalid carrier-stage or pickup-duration derived fields to missing.
- Exclude flagged rows only from carrier handoff or pickup-time metrics.
- Keep flagged rows for total delivery analysis when purchase timestamp,
  customer delivery timestamp, and estimated delivery timestamp are valid.
- Do not impute carrier timestamps by default. If imputation is required later,
  impute only a derived field, use seller/category medians with a minimum sample
  rule, and keep an imputation flag.

### Category Translation

Do not drop products when a category translation is missing.

Policy:

- Keep the original `product_category_name`.
- Use the English translation when available.
- Fall back to original category and then `unknown` for dashboard grouping.
- Add a flag such as `category_translation_missing` in detailed audit notebooks
  when analyzing unmatched translation rows.
- Keep raw join keys unchanged; create separate display labels for charts and
  report text.

### Geolocation

The raw geolocation data contains multiple rows per ZIP-code prefix. For mapping
or distance work, aggregate it to one row per prefix before joining.

Suggested aggregation:

- latitude: median latitude;
- longitude: median longitude;
- city/state: standardized representative value.

Geolocation fields are optional for the final dashboard unless the distance join
is fully validated.

### Text and Missing Values

Clean text fields for display and grouping, but do not mutate identifier keys.

Policy:

- Keep raw IDs such as `order_id`, `customer_id`, `product_id`, `seller_id`,
  `review_id`, and `mql_id` unchanged.
- Standardize non-ID categorical fields for analysis only after join keys are
  preserved.
- Convert null-like strings and empty strings to missing values.
- Keep missing dates as `NaT`; do not fabricate timestamps.

## Grain Rules

The master table grain is item-level: `1 row = 1 order item`.

Use the item-level table for:

- revenue;
- freight;
- product and category analysis;
- seller contribution;
- item volume;
- customer/seller geography attached to item rows.

Use an order-level table for:

- order count;
- order status distribution;
- delivered rate;
- late-delivery rate;
- delivery days and delay days;
- review-by-order comparisons;
- late-vs-on-time low-review rates.

Order-level KPIs must not be calculated directly from the item-level master
table unless the table is first deduplicated to one row per `order_id`.
Multi-item orders would otherwise be counted more than once.

## Table Contribution Map

| Dataset | Dashboard/report contribution |
| --- | --- |
| `orders_dataset` | Order status, purchase timing, delivery timing, estimated-vs-actual delivery, order-level delivery risk |
| `order_items_dataset` | Item grain, seller/product linkage, item volume, revenue, freight value |
| `order_reviews_dataset` | Review score, low-review rate, customer satisfaction proxy |
| `products_dataset` | Product category, product dimensions, product weight, product photo count |
| `product_category_name_translation` | English category labels and category grouping |
| `customers_dataset` | Customer city/state and regional demand |
| `sellers_dataset` | Seller city/state and seller performance segmentation |
| `order_payments_dataset` | Optional payment value/type analysis and payment behavior context |
| `geolocation_dataset` | Optional coordinate-based regional mapping or distance analysis |
| `marketing_qualified_leads_dataset` | Marketing lead count, first-contact timing, lead-source/segment analysis |
| `closed_deals_dataset` | Closed seller deals, acquisition conversion, optional joined seller-performance analysis |

## Exclusions and Cautions

- Delivery-time and late-delivery metrics exclude undelivered orders.
- Missing reviews are not treated as negative reviews.
- Category, seller, and regional rates should use minimum sample thresholds
  before making recommendations.
- Geolocation distance should remain supporting analysis unless unmatched ZIP
  prefixes and duplicate-prefix aggregation are fully documented.
- Payment analysis is optional and should not drive the main story unless the
  team adds a clear business question for it.
- Marketing funnel analysis is supporting evidence unless closed sellers can be
  linked reliably to marketplace seller outcomes.
