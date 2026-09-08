-- Performance: convert the analytical views to MATERIALIZED views + tables so
-- the interactive Next.js app (webapp/) responds in ms instead of recomputing
-- over 112k item rows per request. Run AFTER marts.sql and geo_marts.sql.
--
-- Refresh after the data changes:
--   REFRESH MATERIALIZED VIEW seller_stats, category_stats, intervention_sellers,
--     healthy_sellers, tracked_categories, weekly_overview, weekly_category, weekly_seller;
--   -- then rebuild the derived tables (they depend on the matviews above):
--   \i geo_marts_tables.sql   -- or re-run the seller_cat / seller_alternatives block

DROP VIEW IF EXISTS weekly_seller, weekly_category, weekly_overview,
  intervention_sellers, healthy_sellers, tracked_categories,
  seller_stats, category_stats CASCADE;

CREATE MATERIALIZED VIEW seller_stats AS
  SELECT seller_id, MIN(seller_state) seller_state, COUNT(DISTINCT order_id) orders,
         SUM(price) revenue, AVG(review_score) avg_review,
         100.0*AVG(CASE WHEN is_late THEN 1 ELSE 0 END) late_rate,
         100.0*AVG(CASE WHEN low_review THEN 1 ELSE 0 END) low_review_rate
  FROM item_base GROUP BY seller_id;
CREATE MATERIALIZED VIEW category_stats AS
  SELECT category, COUNT(*) items, COUNT(DISTINCT order_id) orders, SUM(price) revenue,
         AVG(review_score) avg_review,
         100.0*AVG(CASE WHEN is_late THEN 1 ELSE 0 END) late_rate,
         100.0*AVG(CASE WHEN low_review THEN 1 ELSE 0 END) low_review_rate
  FROM item_base WHERE category IS NOT NULL GROUP BY category;
CREATE MATERIALIZED VIEW intervention_sellers AS
  SELECT * FROM seller_stats WHERE orders>=50 AND (avg_review<3.8 OR late_rate>14 OR low_review_rate>20);
CREATE MATERIALIZED VIEW healthy_sellers AS
  SELECT * FROM seller_stats WHERE orders>=80 AND avg_review>=4.1 AND late_rate<=8;
CREATE MATERIALIZED VIEW tracked_categories AS
  SELECT * FROM category_stats WHERE items>=500;
CREATE MATERIALIZED VIEW weekly_overview AS
  SELECT purchase_week, COUNT(*) orders, COUNT(*) FILTER(WHERE is_delivered) delivered,
         COUNT(*) FILTER(WHERE is_late) late_orders, ROUND(AVG(review_score),2) avg_review,
         ROUND(100.0*AVG(CASE WHEN is_late THEN 1 ELSE 0 END),1) late_rate_pct
  FROM order_base GROUP BY purchase_week;
CREATE MATERIALIZED VIEW weekly_category AS
  SELECT i.purchase_week, i.category, COUNT(DISTINCT i.order_id) orders,
         COUNT(DISTINCT i.order_id) FILTER(WHERE i.is_late) late_orders,
         ROUND(AVG(i.review_score),2) avg_review, ROUND(SUM(i.price),2) revenue
  FROM item_base i JOIN tracked_categories tc ON tc.category=i.category
  GROUP BY i.purchase_week, i.category;
CREATE MATERIALIZED VIEW weekly_seller AS
  SELECT i.purchase_week, i.seller_id, i.seller_state, COUNT(DISTINCT i.order_id) orders,
         COUNT(DISTINCT i.order_id) FILTER(WHERE i.is_late) late_orders,
         ROUND(AVG(i.review_score),2) avg_review, ROUND(SUM(i.price),2) revenue
  FROM item_base i JOIN intervention_sellers isv ON isv.seller_id=i.seller_id
  GROUP BY i.purchase_week, i.seller_id, i.seller_state;

CREATE INDEX ON weekly_overview(purchase_week);
CREATE INDEX ON weekly_category(purchase_week);
CREATE INDEX ON weekly_seller(purchase_week);
CREATE INDEX ON seller_stats(seller_id);

-- seller_cat and seller_alternatives as indexed TABLES (the nearest-neighbour
-- LATERAL is ~40s to compute once; querying the table is ms).
DROP VIEW IF EXISTS seller_alternatives CASCADE;
DROP VIEW IF EXISTS seller_cat CASCADE;
CREATE TABLE seller_cat AS SELECT DISTINCT seller_id, category FROM item_base WHERE category IS NOT NULL;
CREATE INDEX idx_sc_cat ON seller_cat(category);
CREATE INDEX idx_sc_seller ON seller_cat(seller_id);
CREATE TABLE seller_alternatives AS
  SELECT p.seller_id AS poor_seller_id, alt.seller_id AS alt_seller_id, alt.seller_state AS alt_state,
         alt.shared_category, ROUND(alt.dist_km::numeric,0) AS distance_km,
         ROUND(alt.avg_review::numeric,2) AS alt_avg_review, ROUND(alt.late_rate::numeric,1) AS alt_late_rate
  FROM intervention_sellers p JOIN seller_geo pg ON pg.seller_id=p.seller_id
  CROSS JOIN LATERAL (
    SELECT h.seller_id, hg.seller_state, sc.category AS shared_category, h.avg_review, h.late_rate,
      6371*acos(LEAST(1, cos(radians(pg.lat))*cos(radians(hg.lat))*cos(radians(hg.lng)-radians(pg.lng))
        + sin(radians(pg.lat))*sin(radians(hg.lat)))) AS dist_km
    FROM healthy_sellers h JOIN seller_geo hg ON hg.seller_id=h.seller_id
    JOIN seller_cat sc ON sc.seller_id=h.seller_id
    WHERE h.seller_id<>p.seller_id AND sc.category IN (SELECT category FROM seller_cat WHERE seller_id=p.seller_id)
    ORDER BY dist_km ASC LIMIT 1) alt;
CREATE INDEX idx_sa_poor ON seller_alternatives(poor_seller_id);
