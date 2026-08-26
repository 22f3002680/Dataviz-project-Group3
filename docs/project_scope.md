# Project Scope and Business Questions

Source brief: https://docs.google.com/document/d/e/2PACX-1vTK3D-jGSwK2p0mPOOeC7SieNxD137LHUBW1-iF4B0VH4Y_7GNdwQ53GZeNoCRU8KWgW-XyJclYPuNn/pub

Issue #1 defines the project framing for the e-commerce marketplace analysis.
The project goal is to help the marketplace grow revenue and seller activity
without damaging customer satisfaction.

## Business Goal

The marketplace connects many sellers with customers across Brazil. Growth can
come from more sellers, broader product coverage, and higher order volume, but
that growth is only valuable if delivery reliability and product experience stay
strong. This project uses order, item, product, seller, customer, delivery,
review, regional, and optional marketing funnel data to identify:

- where the marketplace should invest for growth;
- where customer experience is already strong enough to scale;
- where late delivery, weak reviews, or seller performance create risk;
- which constraints and assumptions should be visible in the final story.

## Final Analysis Questions

| # | Question | Metrics | Dataset columns | Planned visualization | Dashboard/report section |
| --- | --- | --- | --- | --- | --- |
| 1 | How is marketplace demand distributed over time and geography? | Orders, items, revenue, customer count, seller count, monthly order trend, state demand share | `orders_dataset.order_id`, `orders_dataset.order_purchase_timestamp`, `order_items_dataset.order_item_id`, `order_items_dataset.price`, `customers_dataset.customer_state`, `sellers_dataset.seller_state` | KPI cards, monthly trend line, top customer-state ranking | Overview, Regions |
| 2 | How does delivery performance affect customer satisfaction? | Delivery days, delay days, delivered rate, late-delivery rate, average review, low-review rate, late-vs-on-time low-review rate | `orders_dataset.order_status`, `orders_dataset.order_purchase_timestamp`, `orders_dataset.order_delivered_customer_date`, `orders_dataset.order_estimated_delivery_date`, `order_reviews_dataset.review_score` | Delivery-time bins, late vs on-time comparison, delay impact chart | Delivery |
| 3 | Which product categories are growth opportunities or risk areas? | Category item volume, revenue, average price, average review, low-review rate, late-delivery rate, Jan-Aug 2017 vs Jan-Aug 2018 growth | `order_items_dataset.product_id`, `order_items_dataset.order_item_id`, `order_items_dataset.price`, `products_dataset.product_category_name`, `product_category_name_translation.product_category_name_english`, order dates, review score | Top category bars, category opportunity/risk table, growth guardrail chart | Categories, Growth |
| 4 | Which regions show high demand but weak delivery or customer experience? | State item volume, state revenue, average delivery days, late-delivery rate, low-review rate, same-state vs cross-state performance | `customers_dataset.customer_state`, `customers_dataset.customer_city`, `sellers_dataset.seller_state`, `sellers_dataset.seller_city`, order dates, item price, review score | Regional demand/risk ranking, same-state comparison, priority-zone table | Regions, Delivery |
| 5 | Which sellers are high-value but operationally risky? | Seller revenue, seller order count, delivered orders, late rate, low-review rate, average review score, intervention watchlist, healthy seller benchmark | `order_items_dataset.seller_id`, `order_items_dataset.order_id`, `order_items_dataset.price`, `sellers_dataset.seller_state`, `orders_dataset.order_delivered_customer_date`, `orders_dataset.order_estimated_delivery_date`, `order_reviews_dataset.review_score` | Seller risk scatter, intervention watchlist table, healthy seller benchmark table | Sellers |
| 6 | Does freight or logistics structure affect customer experience? | Freight value, freight ratio, same-state flag, average freight, delivery days, late-delivery rate, average review | `order_items_dataset.freight_value`, `order_items_dataset.price`, customer/seller state fields, delivery dates, review score | Same-state grouped bars, freight-ratio summary, delivery and review comparison | Delivery, Regions |
| 7 | Is the marketing-to-seller funnel healthy enough to support growth? | Marketing qualified leads, closed deals, win rate, lead origin, business segment, optional linked seller performance | `marketing_qualified_leads_dataset.mql_id`, `marketing_qualified_leads_dataset.first_contact_date`, `closed_deals_dataset.mql_id`, `closed_deals_dataset.seller_id`, `closed_deals_dataset.won_date`, available lead/deal segment fields | Funnel KPI cards, win-rate by segment/origin, linked seller contribution if join quality is sufficient | Growth, Technical appendix |

## Core Metric Rules

- Review score is the main customer satisfaction proxy.
- Low review means `review_score <= 2`.
- Delivery metrics are computed from order-level rows.
- Late delivery means a delivered order where customer delivery happened after
  the estimated delivery date.
- Delivery-time averages and late-delivery rates exclude undelivered orders.
- Revenue, freight, product, category, and seller contribution metrics use
  item-level rows because price and freight are item-level fields.
- Multi-item orders must not be duplicated when calculating order-level KPIs.
- Marketing funnel analysis is supporting evidence unless seller joins are
  strong enough to connect funnel outcomes to marketplace performance.

See `docs/metric_dictionary.md` for the detailed validated metric definitions.

## Scope and Assumptions

- The analysis focuses on the complete e-commerce order journey: purchase,
  seller handling, freight/delivery, product/category context, and customer
  review.
- The available historical data is treated as representative of the observed
  marketplace period, not as a guarantee of future performance.
- Customer reviews are interpreted as satisfaction signals, not perfect measures
  of customer loyalty.
- Observed relationships are reported as associations unless a stronger causal
  design is explicitly added.
- Geolocation distance analysis is optional. Regional analysis should use
  customer and seller city/state fields unless a validated geolocation join is
  added.
- Missing values, unmatched joins, and low-sample groups must be documented
  before using them for recommendations.

## Expected Outputs

- A reproducible code path from raw data to dashboard-ready metrics.
- Exploratory notebooks for order journey, data quality, delivery, category,
  regional, seller, and marketing funnel analysis.
- An interactive dashboard organized around Overview, Delivery, Categories,
  Regions, Sellers, and Growth.
- A final report that connects the business problem, methods, findings,
  implications, limitations, and recommended actions.
- A final presentation that uses a focused visual story rather than a catalogue
  of every chart.
- Individual contribution logs for each team member.

## Success Criteria

The project is successful if each final question is answered with a clear metric,
an appropriate visual, a stated limitation, and a concrete business implication.
The final recommendation should distinguish between growth opportunities,
monitoring guardrails, and operational interventions.
