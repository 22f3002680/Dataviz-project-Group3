# Metric Dictionary

Issue #4 validates that dashboard metrics are defined consistently and can be
recomputed from the raw e-commerce datasets.

## Principles

- Review percentages use rows in `order_reviews_dataset` unless the metric is
  explicitly joined to orders.
- Delivery metrics use order-level rows and only count delivered orders when
  the metric depends on actual delivery timing.
- Revenue, category, seller, and regional tables use item-level rows because
  price and freight live in `order_items_dataset`.
- Missing review scores are not counted as low reviews. In joined order/item
  tables, `low_review` is `False` when no review score is present.
- Undelivered, canceled, unavailable, or otherwise incomplete orders are
  excluded from delivery-time averages and late-delivery rates.
- Product category names use the English translation table where available.
  Missing translations fall back to the original category and then `unknown`.
- Marketing conversion means a closed-deal record is observed for an MQL by the
  dataset snapshot. Leads without a match are not described as failed leads.
- Seller-acquisition outcome comparisons use equal 30-day post-win windows and
  exclude multi-seller orders from seller-attributed review metrics.

## Summary KPIs

| Metric | Level | Definition | Source columns | Missing/exclusion handling | Dashboard use |
| --- | --- | --- | --- | --- | --- |
| `orders` | Order | Count of rows in `orders_dataset` | `orders_dataset.order_id` | Includes all order statuses | Overview KPI context |
| `items` | Item | Count of rows in `order_items_dataset` | `order_items_dataset.order_item_id` | Includes all available item rows | Metadata/context |
| `customers` | Customer | Distinct `customer_unique_id` count | `customers_dataset.customer_unique_id` | Missing IDs are excluded by distinct count behavior | Metadata/context |
| `sellers` | Seller | Distinct seller count | `sellers_dataset.seller_id` | Missing IDs are excluded by distinct count behavior | Metadata/context |
| `products` | Product | Distinct product count | `products_dataset.product_id` | Missing IDs are excluded by distinct count behavior | Metadata/context |
| `categories` | Product | Distinct normalized product category count | `products_dataset.product_category_name`, translation table | Missing category becomes `unknown` | Metadata/context |
| `avgReview` | Review | Mean review score | `order_reviews_dataset.review_score` | Missing scores ignored by mean | Overview KPI |
| `highReviewRate` | Review | Percent of reviews with score `>= 4` | `order_reviews_dataset.review_score` | Missing scores evaluate as not high | Overview KPI note |
| `lowReviewRate` | Review | Percent of reviews with score `<= 2` | `order_reviews_dataset.review_score` | Missing scores evaluate as not low | Report/reporting context |
| `deliveredRate` | Order | Percent of orders with status `delivered` and a delivered-customer timestamp | `orders_dataset.order_status`, `order_delivered_customer_date` | Orders without delivered timestamp are not delivered | Overview KPI note |
| `lateRate` | Order | Percent of delivered orders where delivered-customer date is after estimated delivery date | `order_delivered_customer_date`, `order_estimated_delivery_date` | Only delivered orders are included | Late delivery KPI |
| `avgDeliveryDays` | Order | Average days from purchase timestamp to delivered-customer date | `order_purchase_timestamp`, `order_delivered_customer_date` | Only delivered orders are included | Delivery KPI |
| `medianDeliveryDays` | Order | Median days from purchase timestamp to delivered-customer date | `order_purchase_timestamp`, `order_delivered_customer_date` | Only delivered orders are included | Delivery KPI note |
| `lateLowReviewRate` | Order + Review | Percent of late delivered orders with review score `<= 2` | Order dates, review score rollup by `order_id` | Late orders without a review are counted as not low review | Late delivery KPI note |
| `onTimeLowReviewRate` | Order + Review | Percent of delivered non-late orders with review score `<= 2` | Order dates, review score rollup by `order_id` | Delivered on-time orders without a review are counted as not low review | Delivery comparison |
| `mql` | Marketing lead | Count of marketing-qualified lead rows | `marketing_qualified_leads_dataset.mql_id` | Includes all MQL rows | Growth tab |
| `closedDeals` | Marketing deal | Count of closed-deal rows | `closed_deals_dataset.mql_id` | Includes all closed-deal rows | Growth tab |
| `winRate` | Marketing funnel | `closedDeals / mql * 100` | MQL and closed-deal row counts | Returns `0` if MQL count is zero | Growth tab |

## Marketing Funnel Report Metrics

| Metric | Level | Definition | Inclusion and denominator rules |
| --- | --- | --- | --- |
| Observed conversion rate | MQL | MQLs with a matching closed-deal record divided by all MQLs | Reported as observed by the dataset snapshot; unmatched MQLs are not proven losses |
| Origin conversion rate | MQL/origin | Observed wins in an origin divided by MQLs in that origin | Blank and literal `unknown` origins are combined as `Unknown / missing` |
| Marketplace linkage coverage | Closed seller | Closed-deal seller IDs found in marketplace order items divided by all closed sellers | Linkage does not imply that marketing caused marketplace performance |
| Equal-window eligible seller | Closed seller | Seller with non-missing `won_date` at least 30 days before the final item-backed purchase timestamp | Ensures every eligible seller has the same potential follow-up period |
| 30-day activation rate | Closed seller/origin | Eligible sellers with at least one seller-order from `won_date` through the next 30 days divided by all eligible sellers | Uses all eligible closed sellers, including sellers without observed marketplace activity |
| Orders per active seller | Seller-order/origin | Distinct seller-order rows in the 30-day window divided by active sellers | One row per seller and order; multi-item orders for one seller count once |
| Product revenue per active seller | Item/origin | Sum of item `price` in the 30-day window divided by active sellers | Excludes freight; item prices are summed before seller-level standardization |
| Average review after win | Reviewed seller-order/origin | Mean order-level review rollup for reviewed single-seller orders in the 30-day window | Multi-seller orders are excluded because an order review cannot be assigned reliably to one seller |
| Low-review rate after win | Reviewed seller-order/origin | Reviewed single-seller orders with order-level average score `<= 2` divided by reviewed single-seller orders | Missing reviews are excluded from numerator and denominator |

## Grouped Outputs

| Output | Level | Main formulas | Inclusion rules | Dashboard use |
| --- | --- | --- | --- | --- |
| `reviewDistribution` | Review | Count and share by `review_score` | All review rows | Overview chart |
| `deliveryBins` | Order + Review | Delivered orders grouped by delivery-day bins; average review and low-review rate per bin | Delivered orders with non-missing review score | Delivery tab |
| `sameState` | Item | Delivered item rows grouped by whether customer state equals seller state | Delivered item rows only | Delivery tab |
| `topCategoriesByItems` | Item/category | Category item counts, sorted descending | All item rows with joined category | Categories tab |
| `topCategoriesByRevenue` | Item/category | Category revenue as sum of item price, sorted descending | All item rows with joined category | Categories tab |
| `riskCategories` | Item/category | Categories with at least 500 items sorted by low-review rate and late rate | Item-level category rows | Categories tab |
| `topStates` | Item/customer state | Customer-state item counts, sorted descending | Item rows joined to customer state | Regions tab |
| `riskStates` | Item/customer state | States with at least 500 items sorted by late rate and average delivery days | Item rows joined to customer state | Regions tab |
| `riskSellers` | Item/seller | Sellers with at least 50 orders and weak review, late, or low-review metrics | Seller grouped item rows | Sellers tab |
| `healthySellers` | Item/seller | Sellers with at least 80 orders, review `>= 4.1`, and late rate `<= 8%` | Seller grouped item rows | Sellers tab |
| `growthCategories` | Item/category | Jan-Aug 2017 vs Jan-Aug 2018 item/revenue growth with review and late-rate guardrails | Categories with 2017 items `>= 50`, 2018 items `>= 100`, 2018 review `>= 4.0`, 2018 late rate `<= 10%` | Growth tab |

## Validation

Run:

```bash
python3 scripts/validate_dashboard_metrics.py
python3 scripts/validate_marketing_funnel_analysis.py
```

The script independently recomputes summary KPIs, row counts, review
distribution, delivery bins, same-state delivery, category rankings, state
rankings, seller lists, and growth categories from the source data, then
compares them with `dashboard/data.js`.

The marketing-funnel validator checks source-key uniqueness, baseline totals,
origin reconciliation, marketplace linkage, equal-window event boundaries,
single-seller review attribution, bounded rates, and generated report artifacts.
