-- Analytical tables for the Metabase dashboards.
-- Loaded from scripts/build_metabase_tables.py output (metabase/data/*.csv),
-- which reuses the validated cleaning/joins from build_dashboard_data.py.

DROP TABLE IF EXISTS order_base;
CREATE TABLE order_base (
    order_id                      text,
    customer_id                   text,
    customer_state                text,
    customer_city                 text,
    order_status                  text,
    order_purchase_timestamp      timestamp,
    order_delivered_customer_date timestamp,
    order_estimated_delivery_date date,
    review_score                  numeric,
    delivery_days                 numeric,
    delay_days                    numeric,
    is_delivered                  boolean,
    is_late                       boolean,
    low_review                    boolean,
    one_star                      boolean,
    month                         text,
    weekday                       text,
    purchase_week                 date
);

DROP TABLE IF EXISTS item_base;
CREATE TABLE item_base (
    order_id                      text,
    order_item_id                 integer,
    product_id                    text,
    seller_id                     text,
    category                      text,
    price                         numeric,
    freight_value                 numeric,
    freight_ratio                 numeric,
    customer_state                text,
    customer_city                 text,
    seller_state                  text,
    seller_city                   text,
    order_status                  text,
    order_purchase_timestamp      timestamp,
    order_delivered_customer_date timestamp,
    order_estimated_delivery_date date,
    review_score                  numeric,
    delivery_days                 numeric,
    delay_days                    numeric,
    is_delivered                  boolean,
    is_late                       boolean,
    low_review                    boolean,
    one_star                      boolean,
    same_state                    boolean,
    year                          integer,
    month_num                     integer,
    month                         text,
    weekday                       text,
    purchase_week                 date
);

\copy order_base FROM '/data/order_base.csv' WITH (FORMAT csv, HEADER true, NULL '');
\copy item_base  FROM '/data/item_base.csv'  WITH (FORMAT csv, HEADER true, NULL '');

CREATE INDEX idx_order_week   ON order_base (purchase_week);
CREATE INDEX idx_item_week    ON item_base  (purchase_week);
CREATE INDEX idx_item_cat     ON item_base  (category);
CREATE INDEX idx_item_seller  ON item_base  (seller_id);
