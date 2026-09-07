#!/usr/bin/env python3
"""Rebuild per teammate feedback (project-materials doc). Phase 1: content.
- Overview: dynamic cumulative volume (<= selected week), orders-by-state +
  late-delivery choropleth with a named worst-states table, top/bottom 3
  products & sellers for the week. Removes the late-rate/review line.
- Product: merged orders+delayed bar (delays in a second colour), a diverging
  review-change bar (this week vs prior), and a categories-needing-intervention
  table. Removes the Category week-over-week table.
- Seller: same merge + diverging seller review-change bar + sellers-needing-
  attention table (placeholder for the geolocation alternative-seller feature).
- Common KPI strip on every tab; clean de-underscored labels.
"""
from __future__ import annotations
import json, urllib.request, urllib.error, uuid

MB = "http://localhost:3000"
EMAIL, PASS = "admin@dvd.local", "Dvdproj123!"
DEFAULT_WEEK, PARAM, DB_ID = "2018-08-13", "week_param", 2
tok = {"t": None}


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(MB + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if tok["t"]:
        req.add_header("X-Metabase-Session", tok["t"])
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")


def login():
    tok["t"] = api("POST", "/api/session", {"username": EMAIL, "password": PASS})["id"]


def wtag():
    return {"week": {"id": str(uuid.uuid4()), "name": "week", "display-name": "Week (Mon)",
                     "type": "date", "default": DEFAULT_WEEK, "required": True}}


def card(name, sql, display="table", viz=None):
    return api("POST", "/api/card", {
        "name": name, "display": display, "visualization_settings": viz or {},
        "dataset_query": {"type": "native", "database": DB_ID,
                          "native": {"query": sql, "template-tags": wtag()}}})["id"]


def dc(cid, tab, row, col, w, h):
    return {"id": -(abs(tab) * 1000 + row * 30 + col + 1), "card_id": cid,
            "dashboard_tab_id": tab, "row": row, "col": col, "size_x": w, "size_y": h,
            "series": [], "visualization_settings": {},
            "parameter_mappings": [{"parameter_id": PARAM, "card_id": cid,
                                    "target": ["variable", ["template-tag", "week"]]}]}


def main():
    login()
    W = "WHERE purchase_week = {{week}}"

    # KPI strip
    k = {
        "Orders this week": card("Orders this week", f"SELECT orders FROM weekly_overview {W}", "scalar"),
        "Delivered this week": card("Delivered this week", f"SELECT delivered FROM weekly_overview {W}", "scalar"),
        "Delayed this week": card("Delayed this week", f"SELECT late_orders FROM weekly_overview {W}", "scalar"),
        "Avg review this week": card("Avg review this week", f"SELECT avg_review FROM weekly_overview {W}", "scalar"),
        "Orders WoW %": card("Orders WoW %",
            "WITH s AS (SELECT {{week}}::date w) SELECT ROUND(100.0*(c.orders-p.orders)/NULLIF(p.orders,0),1) "
            "FROM s JOIN weekly_overview c ON c.purchase_week=s.w "
            "LEFT JOIN weekly_overview p ON p.purchase_week=s.w-7", "scalar"),
        "Best week (orders)": card("Best week (orders)", "SELECT MAX(orders) FROM weekly_overview", "scalar"),
    }

    def strip(tab):
        ks = list(k.values())
        return [dc(ks[i], tab, 0, i * 4, 4, 2) for i in range(6)]

    # ---- Overview ----
    ov_vol = card("Weekly order volume (up to selected week)",
                  "SELECT purchase_week, orders FROM weekly_overview "
                  "WHERE purchase_week <= {{week}} AND purchase_week >= '2016-12-01' ORDER BY 1", "line",
                  {"graph.dimensions": ["purchase_week"], "graph.metrics": ["orders"]})
    ov_state = card("Orders by state (this week)",
                    f"SELECT customer_state, COUNT(*) AS orders FROM order_base {W} "
                    "GROUP BY 1 ORDER BY orders DESC LIMIT 15", "row",
                    {"graph.dimensions": ["customer_state"], "graph.metrics": ["orders"]})
    ov_map = card("Late-delivery rate by state",
                  "SELECT customer_state, ROUND(100.0*AVG(CASE WHEN is_late THEN 1 ELSE 0 END),1) "
                  f"AS late_rate FROM order_base {W} GROUP BY 1", "map",
                  {"map.type": "region", "map.region": "brazil_states",
                   "map.dimension_column": "customer_state", "map.metric_column": "late_rate"})
    ov_worst = card("Worst states for late delivery (this week)",
                    "SELECT customer_state AS state, "
                    "ROUND(100.0*AVG(CASE WHEN is_late THEN 1 ELSE 0 END),1) AS late_rate_pct, "
                    f"COUNT(*) FILTER (WHERE is_late) AS late_orders FROM order_base {W} "
                    "GROUP BY 1 HAVING COUNT(*) >= 20 ORDER BY late_rate_pct DESC LIMIT 6")
    ov_prod = card("Top / bottom 3 categories (this week)",
                   "(SELECT 'Top' AS rank, INITCAP(REPLACE(category,'_',' ')) AS category, orders, avg_review "
                   f"FROM weekly_category {W} ORDER BY orders DESC LIMIT 3) UNION ALL "
                   "(SELECT 'Bottom', INITCAP(REPLACE(category,'_',' ')), orders, avg_review "
                   f"FROM weekly_category {W} ORDER BY orders ASC LIMIT 3)")
    ov_sell = card("Top / bottom 3 sellers (this week)",
                   "(SELECT 'Top' AS rank, LEFT(seller_id,8) AS seller, orders, avg_review "
                   f"FROM weekly_seller {W} ORDER BY orders DESC LIMIT 3) UNION ALL "
                   "(SELECT 'Bottom', LEFT(seller_id,8), orders, avg_review "
                   f"FROM weekly_seller {W} ORDER BY orders ASC LIMIT 3)")

    # ---- Product ----
    pr_merge = card("Orders vs delayed by category (this week)",
                    "SELECT INITCAP(REPLACE(category,'_',' ')) AS category, orders, late_orders "
                    f"FROM weekly_category {W} ORDER BY orders DESC", "bar",
                    {"graph.dimensions": ["category"], "graph.metrics": ["orders", "late_orders"],
                     "stackable.stack_type": None})
    pr_div = card("Category review change vs prior week",
                  "WITH s AS (SELECT {{week}}::date w) "
                  "SELECT INITCAP(REPLACE(c.category,'_',' ')) AS category, "
                  "ROUND(c.avg_review - p.avg_review, 2) AS review_change "
                  "FROM weekly_category c CROSS JOIN s "
                  "JOIN weekly_category p ON p.category=c.category AND p.purchase_week=s.w-7 "
                  "WHERE c.purchase_week=s.w AND c.avg_review IS NOT NULL AND p.avg_review IS NOT NULL "
                  "ORDER BY review_change", "row",
                  {"graph.dimensions": ["category"], "graph.metrics": ["review_change"]})
    pr_int = card("Categories needing intervention (this week)",
                  "SELECT INITCAP(REPLACE(category,'_',' ')) AS category, avg_review, late_orders, orders "
                  f"FROM weekly_category {W} AND (avg_review < 4 OR late_orders > 0) "
                  "ORDER BY avg_review ASC NULLS LAST, late_orders DESC")

    # ---- Seller ----
    sl_merge = card("Orders vs delayed by seller (this week)",
                    "SELECT LEFT(seller_id,8) AS seller, orders, late_orders "
                    f"FROM weekly_seller {W} ORDER BY orders DESC LIMIT 25", "bar",
                    {"graph.dimensions": ["seller"], "graph.metrics": ["orders", "late_orders"],
                     "stackable.stack_type": None})
    sl_div = card("Seller review change vs prior week",
                  "WITH s AS (SELECT {{week}}::date w) "
                  "SELECT LEFT(c.seller_id,8) AS seller, ROUND(c.avg_review - p.avg_review, 2) AS review_change "
                  "FROM weekly_seller c CROSS JOIN s "
                  "JOIN weekly_seller p ON p.seller_id=c.seller_id AND p.purchase_week=s.w-7 "
                  "WHERE c.purchase_week=s.w AND c.avg_review IS NOT NULL AND p.avg_review IS NOT NULL "
                  "ORDER BY review_change", "row",
                  {"graph.dimensions": ["seller"], "graph.metrics": ["review_change"]})
    sl_att = card("Sellers needing attention (this week)",
                  "SELECT LEFT(seller_id,10) AS seller, seller_state, avg_review, late_orders, orders "
                  f"FROM weekly_seller {W} AND (avg_review < 4 OR late_orders > 0) "
                  "ORDER BY avg_review ASC NULLS LAST, late_orders DESC")

    dash = api("POST", "/api/dashboard", {"name": "Group 3 · Marketplace Weekly Dashboard"})["id"]
    T_O, T_P, T_S = -1, -2, -3
    tabs = [{"id": T_O, "name": "Overview"}, {"id": T_P, "name": "Product"}, {"id": T_S, "name": "Seller"}]

    cards = []
    cards += strip(T_O) + [
        dc(ov_vol, T_O, 2, 0, 12, 5), dc(ov_state, T_O, 2, 12, 12, 5),
        dc(ov_map, T_O, 7, 0, 12, 6), dc(ov_worst, T_O, 7, 12, 12, 6),
        dc(ov_prod, T_O, 13, 0, 12, 4), dc(ov_sell, T_O, 13, 12, 12, 4)]
    cards += strip(T_P) + [
        dc(pr_merge, T_P, 2, 0, 24, 6),
        dc(pr_div, T_P, 8, 0, 12, 5), dc(pr_int, T_P, 8, 12, 12, 5)]
    cards += strip(T_S) + [
        dc(sl_merge, T_S, 2, 0, 24, 6),
        dc(sl_div, T_S, 8, 0, 12, 5), dc(sl_att, T_S, 8, 12, 12, 5)]

    params = [{"id": PARAM, "name": "Week (Mon)", "slug": "week",
               "type": "date/single", "sectionId": "date", "default": DEFAULT_WEEK}]
    api("PUT", f"/api/dashboard/{dash}", {"parameters": params, "tabs": tabs, "dashcards": cards})

    for d in api("GET", "/api/dashboard"):
        if not d.get("archived") and d["id"] != dash and d.get("name", "").startswith("Group 3 ·"):
            try:
                api("PUT", f"/api/dashboard/{d['id']}", {"archived": True})
            except RuntimeError:
                pass

    print(f"Dashboard id={dash}  {MB}/dashboard/{dash}")


if __name__ == "__main__":
    main()
