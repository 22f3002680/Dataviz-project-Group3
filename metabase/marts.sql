-- Analytical marts for the weekly-tracking dashboards (Durga Prasad brief).
-- Built on top of order_base / item_base. Definitions follow the report/deck
-- methodology so the dashboards flag the same intervention sellers and
-- high-risk / high-revenue categories.

-- ---------------------------------------------------------------------------
-- Seller-level stats over the full period.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS weekly_seller CASCADE;
DROP VIEW IF EXISTS intervention_sellers CASCADE;
DROP VIEW IF EXISTS seller_stats CASCADE;
-- Metrics match build_dashboard_data.build_seller_summary: orders = distinct
-- order_id (all statuses), late_rate / low_review_rate as percentages over all
-- item rows, avg_review skips missing reviews.
CREATE VIEW seller_stats AS
SELECT
    seller_id,
    MIN(seller_state)                                     AS seller_state,
    COUNT(DISTINCT order_id)                              AS orders,
    SUM(price)                                            AS revenue,
    AVG(review_score)                                     AS avg_review,
    100.0 * AVG(CASE WHEN is_late THEN 1 ELSE 0 END)      AS late_rate,
    100.0 * AVG(CASE WHEN low_review THEN 1 ELSE 0 END)   AS low_review_rate
FROM item_base
GROUP BY seller_id;

-- Intervention watchlist = committed `riskSellers` definition (metric dictionary):
-- >= 50 orders and weak review, late, or low-review metrics.
CREATE VIEW intervention_sellers AS
SELECT *
FROM seller_stats
WHERE orders >= 50
  AND (avg_review < 3.8 OR late_rate > 14 OR low_review_rate > 20);

-- Benchmark = committed `healthySellers`: >= 80 orders, review >= 4.1, late <= 8%.
DROP VIEW IF EXISTS healthy_sellers CASCADE;
CREATE VIEW healthy_sellers AS
SELECT *
FROM seller_stats
WHERE orders >= 80 AND avg_review >= 4.1 AND late_rate <= 8;

-- ---------------------------------------------------------------------------
-- Category-level stats over the full period.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS weekly_category CASCADE;
DROP VIEW IF EXISTS tracked_categories CASCADE;
DROP VIEW IF EXISTS category_stats CASCADE;
-- Metrics match build_dashboard_data.build_category_summary.
CREATE VIEW category_stats AS
SELECT
    category,
    COUNT(*)                                             AS items,
    COUNT(DISTINCT order_id)                             AS orders,
    SUM(price)                                           AS revenue,
    AVG(review_score)                                    AS avg_review,
    100.0 * AVG(CASE WHEN is_late THEN 1 ELSE 0 END)     AS late_rate,
    100.0 * AVG(CASE WHEN low_review THEN 1 ELSE 0 END)  AS low_review_rate
FROM item_base
WHERE category IS NOT NULL
GROUP BY category;

-- Tracked categories = committed `riskCategories` eligibility: >= 500 items,
-- the high-scale, review/late-risk set surfaced on the Categories tab.
CREATE VIEW tracked_categories AS
SELECT *
FROM category_stats
WHERE items >= 500;

-- ---------------------------------------------------------------------------
-- Weekly rollups (drive the dashboards + best-week comparison).
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS weekly_overview CASCADE;
CREATE VIEW weekly_overview AS
SELECT
    purchase_week,
    COUNT(*)                                   AS orders,
    COUNT(*) FILTER (WHERE is_delivered)       AS delivered,
    COUNT(*) FILTER (WHERE is_late)            AS late_orders,
    ROUND(AVG(review_score), 2)                AS avg_review,
    ROUND(100.0 * AVG(CASE WHEN is_late THEN 1 ELSE 0 END), 1) AS late_rate_pct
FROM order_base
GROUP BY purchase_week;

CREATE VIEW weekly_category AS
SELECT
    i.purchase_week,
    i.category,
    COUNT(DISTINCT i.order_id)                                   AS orders,
    COUNT(DISTINCT i.order_id) FILTER (WHERE i.is_late)          AS late_orders,
    ROUND(AVG(i.review_score), 2)                               AS avg_review,
    ROUND(SUM(i.price), 2)                                      AS revenue
FROM item_base i
JOIN tracked_categories tc ON tc.category = i.category
GROUP BY i.purchase_week, i.category;

CREATE VIEW weekly_seller AS
SELECT
    i.purchase_week,
    i.seller_id,
    i.seller_state,
    COUNT(DISTINCT i.order_id)                                   AS orders,
    COUNT(DISTINCT i.order_id) FILTER (WHERE i.is_late)          AS late_orders,
    ROUND(AVG(i.review_score), 2)                               AS avg_review,
    ROUND(SUM(i.price), 2)                                      AS revenue
FROM item_base i
JOIN intervention_sellers isv ON isv.seller_id = i.seller_id
GROUP BY i.purchase_week, i.seller_id, i.seller_state;
