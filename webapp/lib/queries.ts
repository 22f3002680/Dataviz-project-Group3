import { q } from "./db";

// state may be null (no filter). Uses ($n::text IS NULL OR col = $n).
const S = "($2::text IS NULL OR customer_state = $2)";
const SS = "($2::text IS NULL OR seller_state = $2)";

// linear-interpolated percentile (0..1)
function pct(arr: number[], p: number): number {
  const s = arr.filter((x) => x != null).sort((a, b) => a - b);
  if (!s.length) return 0;
  const i = (s.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
  return lo === hi ? s[lo] : s[lo] + (s[hi] - s[lo]) * (i - lo);
}

export async function meta() {
  const weeks = await q<{ week: string; orders: number }>(
    `SELECT purchase_week::text AS week, orders FROM weekly_overview
     WHERE purchase_week BETWEEN '2016-12-01' AND '2018-08-27' ORDER BY 1`
  );
  return { weeks };
}

export async function overview(week: string, state: string | null) {
  const p = [week, state];
  const [kpi] = await q<{ orders: number; delivered: number; late: number; avg_review: number }>(
    `SELECT COUNT(*)::int AS orders,
            COUNT(*) FILTER (WHERE is_delivered)::int AS delivered,
            COUNT(*) FILTER (WHERE is_late)::int AS late,
            ROUND(AVG(review_score),2)::float AS avg_review
     FROM order_base WHERE purchase_week = $1 AND ${S}`, p);
  const [prev] = await q<{ orders: number }>(
    `SELECT COUNT(*)::int AS orders FROM order_base
     WHERE purchase_week = $1::date - 7 AND ${S}`, p);
  const [best] = await q<{ best: number }>(
    `SELECT MAX(o)::int AS best FROM (
       SELECT COUNT(*) o FROM order_base WHERE ($1::text IS NULL OR customer_state = $1) GROUP BY purchase_week) t`, [state]);
  const volume = await q(
    `SELECT purchase_week::text AS week, COUNT(*)::int AS orders FROM order_base
     WHERE purchase_week <= $1 AND purchase_week >= '2016-12-01' AND ${S}
     GROUP BY 1 ORDER BY 1`, p);
  const byState = await q(
    `SELECT customer_state AS state, COUNT(*)::int AS orders FROM order_base
     WHERE purchase_week = $1 GROUP BY 1 ORDER BY orders DESC`, [week]);
  const lateByState = await q(
    `SELECT customer_state AS state,
            ROUND(100.0*AVG(CASE WHEN is_late THEN 1 ELSE 0 END),1)::float AS late_rate,
            COUNT(*) FILTER (WHERE is_late)::int AS late_orders,
            COUNT(*)::int AS total
     FROM order_base WHERE purchase_week = $1 GROUP BY 1`, [week]);
  const cats = await q(
    `SELECT INITCAP(REPLACE(category,'_',' ')) AS name,
            COUNT(DISTINCT order_id)::int AS orders, ROUND(AVG(review_score),2)::float AS avg_review
     FROM item_base WHERE purchase_week = $1 AND ${S} AND category IS NOT NULL
     GROUP BY category ORDER BY orders DESC`, p);
  const sellers = await q(
    `SELECT LEFT(seller_id,8) AS name, COUNT(DISTINCT order_id)::int AS orders,
            ROUND(AVG(review_score),2)::float AS avg_review
     FROM item_base WHERE purchase_week = $1 AND ${SS}
     GROUP BY seller_id ORDER BY orders DESC`, p);
  const wow =
    prev?.orders ? Math.round(1000 * (kpi.orders - prev.orders) / prev.orders) / 10 : null;
  return {
    kpi: { ...kpi, wow, best: best?.best ?? null, prev: prev?.orders ?? 0 },
    volume, byState, lateByState,
    topCats: cats.slice(0, 3), bottomCats: cats.slice(-3).reverse(),
    topSellers: sellers.slice(0, 3), bottomSellers: sellers.slice(-3).reverse(),
  };
}

export async function product(week: string, state: string | null) {
  const p = [week, state];
  const merged = await q(
    `SELECT INITCAP(REPLACE(i.category,'_',' ')) AS name,
            COUNT(DISTINCT i.order_id)::int AS orders,
            COUNT(DISTINCT i.order_id) FILTER (WHERE i.is_late)::int AS late_orders
     FROM item_base i JOIN tracked_categories t ON t.category = i.category
     WHERE i.purchase_week = $1 AND ($2::text IS NULL OR i.customer_state = $2)
     GROUP BY i.category ORDER BY orders DESC`, p);
  const reviewChange = await q(
    `WITH cur AS (SELECT category, AVG(review_score) r FROM item_base
                  WHERE purchase_week = $1 AND ${S} GROUP BY 1),
          prev AS (SELECT category, AVG(review_score) r FROM item_base
                   WHERE purchase_week = $1::date - 7 AND ${S} GROUP BY 1)
     SELECT INITCAP(REPLACE(cur.category,'_',' ')) AS name,
            ROUND((cur.r - prev.r)::numeric,2)::float AS review_change
     FROM cur JOIN prev USING (category) JOIN tracked_categories t ON t.category = cur.category
     WHERE cur.r IS NOT NULL AND prev.r IS NOT NULL ORDER BY review_change`, p);
  // PPT criteria (cumulative up to the selected week): categories with >= 11
  // reviewed orders; classification (median revenue x median volume x weak
  // reviews) is done in the chart builder.
  const quadrant = await q(
    `SELECT INITCAP(REPLACE(category,'_',' ')) AS name,
            ROUND(SUM(price))::int AS revenue,
            ROUND(AVG(review_score),2)::float AS avg_review,
            COUNT(DISTINCT order_id)::int AS orders,
            ROUND(100.0*AVG(CASE WHEN low_review THEN 1 ELSE 0 END),1)::float AS low_review_rate
     FROM item_base
     WHERE purchase_week <= $1 AND category IS NOT NULL AND ${S}
     GROUP BY category
     HAVING COUNT(*) FILTER (WHERE review_score IS NOT NULL) >= 11
     ORDER BY revenue DESC`, p);
  const intervention = await q(
    `SELECT INITCAP(REPLACE(category,'_',' ')) AS name, avg_review::float, late_orders::int, orders::int
     FROM weekly_category WHERE purchase_week = $1 AND (avg_review < 4 OR late_orders > 0)
     ORDER BY avg_review ASC NULLS LAST, late_orders DESC LIMIT 10`, [week]);
  return { merged, reviewChange, quadrant, intervention };
}

export async function seller(week: string, state: string | null) {
  const p = [week, state];
  const merged = await q(
    `SELECT LEFT(i.seller_id,8) AS name, COUNT(DISTINCT i.order_id)::int AS orders,
            COUNT(DISTINCT i.order_id) FILTER (WHERE i.is_late)::int AS late_orders
     FROM item_base i JOIN intervention_sellers s ON s.seller_id = i.seller_id
     WHERE i.purchase_week = $1 AND ($2::text IS NULL OR i.seller_state = $2)
     GROUP BY i.seller_id ORDER BY orders DESC LIMIT 25`, p);
  const reviewChange = await q(
    `WITH cur AS (SELECT seller_id, AVG(review_score) r FROM item_base
                  WHERE purchase_week = $1 AND ${SS} GROUP BY 1),
          prev AS (SELECT seller_id, AVG(review_score) r FROM item_base
                   WHERE purchase_week = $1::date - 7 AND ${SS} GROUP BY 1)
     SELECT LEFT(cur.seller_id,8) AS name, ROUND((cur.r - prev.r)::numeric,2)::float AS review_change
     FROM cur JOIN prev USING (seller_id) JOIN intervention_sellers s ON s.seller_id = cur.seller_id
     WHERE cur.r IS NOT NULL AND prev.r IS NOT NULL ORDER BY review_change`, p);
  // PPT criteria (cumulative up to the selected week): priority sellers =
  // revenue > 75th pct, >= 20 delivered orders, late rate > 75th pct,
  // low-review rate > 75th pct. Thresholds recomputed on the cumulative window.
  const srows = await q<{ name: string; revenue: number; delivered: number; late_rate: number | null; low_review_rate: number | null; avg_review: number }>(
    `SELECT LEFT(seller_id,8) AS name,
            SUM(price)::float AS revenue,
            COUNT(DISTINCT order_id) FILTER (WHERE is_delivered)::int AS delivered,
            100.0*AVG(CASE WHEN is_delivered THEN (CASE WHEN is_late THEN 1 ELSE 0 END) END)::float AS late_rate,
            100.0*AVG(CASE WHEN review_score IS NOT NULL THEN (CASE WHEN low_review THEN 1 ELSE 0 END) END)::float AS low_review_rate,
            AVG(review_score)::float AS avg_review
     FROM item_base WHERE purchase_week <= $1 AND ${SS}
     GROUP BY seller_id HAVING AVG(review_score) IS NOT NULL`, p);
  // percentiles over all sellers (matches the PPT's 75th-pct thresholds)
  const revP75 = pct(srows.map((s) => s.revenue), 0.75);
  const lateP75 = pct(srows.map((s) => s.late_rate).filter((x): x is number => x != null), 0.75);
  const lowP75 = pct(srows.map((s) => s.low_review_rate).filter((x): x is number => x != null), 0.75);
  const points = srows.map((s) => ({
    name: s.name, revenue: Math.round(s.revenue),
    avg_review: Math.round(s.avg_review * 100) / 100, orders: s.delivered,
    flagged: s.delivered >= 20 && s.revenue > revP75 && (s.late_rate ?? 0) > lateP75 && (s.low_review_rate ?? 0) > lowP75,
  }));
  const scatter = { points, revP75: Math.round(revP75), reviewThr: 3.8 };
  const watchlist = await q(
    `SELECT LEFT(ws.seller_id,8) AS seller, ws.seller_state AS state,
            ws.avg_review::float, ws.late_orders::int, ws.orders::int,
            LEFT(sa.alt_seller_id,8) AS alt, sa.alt_state,
            INITCAP(REPLACE(sa.shared_category,'_',' ')) AS shared_category,
            sa.distance_km::int, sa.alt_avg_review::float
     FROM weekly_seller ws LEFT JOIN seller_alternatives sa ON sa.poor_seller_id = ws.seller_id
     WHERE ws.purchase_week = $1 AND (ws.avg_review < 4 OR ws.late_orders > 0) AND ${SS.replace(/seller_state/g, "ws.seller_state")}
     ORDER BY ws.avg_review ASC NULLS LAST, ws.late_orders DESC`, p);
  return { merged, reviewChange, scatter, watchlist };
}
