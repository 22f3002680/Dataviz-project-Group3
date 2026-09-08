-- Geolocation marts for the "alternative seller" suggestion feature.
-- Loads seller coordinates and derives, for each intervention seller, the
-- nearest HEALTHY seller that sells at least one of the same categories.

DROP TABLE IF EXISTS seller_geo CASCADE;
CREATE TABLE seller_geo (
    seller_id    text,
    seller_state text,
    lat          double precision,
    lng          double precision
);
\copy seller_geo FROM '/data/seller_geo.csv' WITH (FORMAT csv, HEADER true, NULL '');
CREATE INDEX idx_seller_geo ON seller_geo (seller_id);

-- categories each seller actually sells
DROP VIEW IF EXISTS seller_cat CASCADE;
CREATE VIEW seller_cat AS
SELECT DISTINCT seller_id, category
FROM item_base
WHERE category IS NOT NULL;

-- For every intervention seller, the closest healthy seller sharing a category.
-- Distance via haversine (km). Depends on intervention_sellers + healthy_sellers
-- (marts.sql) and seller_geo/seller_cat above.
DROP VIEW IF EXISTS seller_alternatives CASCADE;
CREATE VIEW seller_alternatives AS
SELECT
    p.seller_id                              AS poor_seller_id,
    alt.seller_id                            AS alt_seller_id,
    alt.seller_state                         AS alt_state,
    alt.shared_category                      AS shared_category,
    ROUND(alt.dist_km::numeric, 0)           AS distance_km,
    ROUND(alt.avg_review::numeric, 2)        AS alt_avg_review,
    ROUND(alt.late_rate::numeric, 1)         AS alt_late_rate
FROM intervention_sellers p
JOIN seller_geo pg ON pg.seller_id = p.seller_id
CROSS JOIN LATERAL (
    SELECT
        h.seller_id, hg.seller_state, sc.category AS shared_category,
        h.avg_review, h.late_rate,
        6371 * acos(LEAST(1,
            cos(radians(pg.lat)) * cos(radians(hg.lat)) * cos(radians(hg.lng) - radians(pg.lng))
            + sin(radians(pg.lat)) * sin(radians(hg.lat)))) AS dist_km
    FROM healthy_sellers h
    JOIN seller_geo hg ON hg.seller_id = h.seller_id
    JOIN seller_cat sc ON sc.seller_id = h.seller_id
    WHERE h.seller_id <> p.seller_id
      AND sc.category IN (SELECT category FROM seller_cat WHERE seller_id = p.seller_id)
    ORDER BY dist_km ASC
    LIMIT 1
) alt;
