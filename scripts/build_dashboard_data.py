from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


SOURCE_DIR = Path("/tmp/dvd_proj_data")
OUT_FILE = Path("dashboard/data.js")


def pct(series: pd.Series) -> float:
    return round(float(series.mean() * 100), 1)


def records(frame: pd.DataFrame, columns: list[str] | None = None) -> list[dict]:
    if columns:
        frame = frame[columns]
    return json.loads(frame.replace({np.nan: None}).to_json(orient="records"))


def main() -> None:
    customers = pd.read_csv(SOURCE_DIR / "customers_dataset.csv")
    sellers = pd.read_csv(SOURCE_DIR / "sellers_dataset.csv")
    orders = pd.read_csv(SOURCE_DIR / "orders_dataset.csv")
    items = pd.read_csv(SOURCE_DIR / "order_items_dataset.csv")
    reviews = pd.read_csv(SOURCE_DIR / "order_reviews_dataset.csv")
    products = pd.read_csv(SOURCE_DIR / "products_dataset.csv")
    translation = pd.read_csv(SOURCE_DIR / "product_category_name_translation.csv")
    mql = pd.read_csv(SOURCE_DIR / "marketing_qualified_leads_dataset.csv")
    closed = pd.read_csv(SOURCE_DIR / "closed_deals_dataset.csv")

    category_names = dict(
        zip(translation["product_category_name"], translation["product_category_name_english"])
    )
    products["category"] = (
        products["product_category_name"]
        .map(category_names)
        .fillna(products["product_category_name"])
        .fillna("unknown")
    )

    for column in [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]:
        orders[column] = pd.to_datetime(orders[column], errors="coerce")

    review_by_order = (
        reviews.groupby("order_id")
        .agg(review_score=("review_score", "mean"), review_count=("review_id", "count"))
        .reset_index()
    )

    order_base = (
        orders.merge(customers, on="customer_id", how="left")
        .merge(review_by_order, on="order_id", how="left")
    )
    order_base["delivery_days"] = (
        order_base["order_delivered_customer_date"] - order_base["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    order_base["delay_days"] = (
        order_base["order_delivered_customer_date"] - order_base["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400
    order_base["is_delivered"] = (
        order_base["order_status"].eq("delivered")
        & order_base["order_delivered_customer_date"].notna()
    )
    order_base["is_late"] = order_base["is_delivered"] & (order_base["delay_days"] > 0)
    order_base["low_review"] = order_base["review_score"].le(2)
    order_base["one_star"] = order_base["review_score"].le(1)
    order_base["month"] = order_base["order_purchase_timestamp"].dt.to_period("M").astype(str)
    order_base["weekday"] = order_base["order_purchase_timestamp"].dt.day_name()

    item_base = (
        items.merge(
            products[
                [
                    "product_id",
                    "category",
                    "product_weight_g",
                    "product_length_cm",
                    "product_height_cm",
                    "product_width_cm",
                    "product_photos_qty",
                ]
            ],
            on="product_id",
            how="left",
        )
        .merge(
            orders[
                [
                    "order_id",
                    "customer_id",
                    "order_purchase_timestamp",
                    "order_delivered_customer_date",
                    "order_estimated_delivery_date",
                    "order_status",
                ]
            ],
            on="order_id",
            how="left",
        )
        .merge(customers[["customer_id", "customer_state", "customer_city"]], on="customer_id", how="left")
        .merge(sellers, on="seller_id", how="left")
        .merge(review_by_order, on="order_id", how="left")
    )
    item_base["delivery_days"] = (
        item_base["order_delivered_customer_date"] - item_base["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    item_base["delay_days"] = (
        item_base["order_delivered_customer_date"] - item_base["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400
    item_base["is_delivered"] = (
        item_base["order_status"].eq("delivered")
        & item_base["order_delivered_customer_date"].notna()
    )
    item_base["is_late"] = item_base["is_delivered"] & (item_base["delay_days"] > 0)
    item_base["low_review"] = item_base["review_score"].le(2)
    item_base["same_state"] = item_base["customer_state"].eq(item_base["seller_state"])
    item_base["year"] = item_base["order_purchase_timestamp"].dt.year
    item_base["month_num"] = item_base["order_purchase_timestamp"].dt.month
    item_base["freight_ratio"] = item_base["freight_value"] / item_base["price"].replace({0: np.nan})

    summary = {
        "orders": int(len(orders)),
        "items": int(len(items)),
        "customers": int(customers["customer_unique_id"].nunique()),
        "sellers": int(sellers["seller_id"].nunique()),
        "products": int(products["product_id"].nunique()),
        "categories": int(products["category"].nunique()),
        "avgReview": round(float(reviews["review_score"].mean()), 2),
        "highReviewRate": round(float(reviews["review_score"].ge(4).mean() * 100), 1),
        "lowReviewRate": round(float(reviews["review_score"].le(2).mean() * 100), 1),
        "deliveredRate": round(float(order_base["is_delivered"].mean() * 100), 1),
        "lateRate": pct(order_base.loc[order_base["is_delivered"], "is_late"]),
        "avgDeliveryDays": round(float(order_base.loc[order_base["is_delivered"], "delivery_days"].mean()), 1),
        "medianDeliveryDays": round(float(order_base.loc[order_base["is_delivered"], "delivery_days"].median()), 1),
        "lateLowReviewRate": pct(order_base.loc[order_base["is_late"], "low_review"]),
        "onTimeLowReviewRate": pct(
            order_base.loc[order_base["is_delivered"] & ~order_base["is_late"], "low_review"]
        ),
        "mql": int(len(mql)),
        "closedDeals": int(len(closed)),
        "winRate": round(float(len(closed) / len(mql) * 100), 1),
    }

    category = (
        item_base.groupby("category")
        .agg(
            items=("order_item_id", "count"),
            orders=("order_id", "nunique"),
            revenue=("price", "sum"),
            avg_price=("price", "mean"),
            avg_review=("review_score", "mean"),
            late_rate=("is_late", lambda s: s.mean() * 100),
            low_review_rate=("low_review", lambda s: s.mean() * 100),
            avg_delivery=("delivery_days", "mean"),
            freight_ratio=("freight_ratio", "mean"),
        )
        .reset_index()
    )
    for column in ["revenue", "avg_price", "avg_review", "late_rate", "low_review_rate", "avg_delivery", "freight_ratio"]:
        category[column] = category[column].round(2)

    customer_states = (
        item_base.groupby("customer_state")
        .agg(
            items=("order_item_id", "count"),
            revenue=("price", "sum"),
            avg_review=("review_score", "mean"),
            late_rate=("is_late", lambda s: s.mean() * 100),
            avg_delivery=("delivery_days", "mean"),
            low_review_rate=("low_review", lambda s: s.mean() * 100),
        )
        .reset_index()
    )
    for column in ["revenue", "avg_review", "late_rate", "avg_delivery", "low_review_rate"]:
        customer_states[column] = customer_states[column].round(2)

    seller_perf = (
        item_base.groupby(["seller_id", "seller_state", "seller_city"])
        .agg(
            orders=("order_id", "nunique"),
            items=("order_item_id", "count"),
            revenue=("price", "sum"),
            avg_review=("review_score", "mean"),
            late_rate=("is_late", lambda s: s.mean() * 100),
            low_review_rate=("low_review", lambda s: s.mean() * 100),
            avg_delivery=("delivery_days", "mean"),
        )
        .reset_index()
    )
    for column in ["revenue", "avg_review", "late_rate", "low_review_rate", "avg_delivery"]:
        seller_perf[column] = seller_perf[column].round(2)

    delivered = order_base[order_base["is_delivered"] & order_base["review_score"].notna()].copy()
    delivered["delivery_bin"] = pd.cut(
        delivered["delivery_days"],
        bins=[0, 3, 7, 14, 21, 999],
        labels=["0-3 days", "4-7 days", "8-14 days", "15-21 days", "22+ days"],
        include_lowest=True,
    )
    delivery_bins = (
        delivered.groupby("delivery_bin", observed=True)
        .agg(
            orders=("order_id", "count"),
            avg_review=("review_score", "mean"),
            low_review_rate=("low_review", lambda s: s.mean() * 100),
        )
        .reset_index()
        .rename(columns={"delivery_bin": "range"})
    )
    delivery_bins["range"] = delivery_bins["range"].astype(str)
    for column in ["avg_review", "low_review_rate"]:
        delivery_bins[column] = delivery_bins[column].round(2)

    monthly = (
        order_base.groupby("month")
        .agg(orders=("order_id", "count"))
        .reset_index()
        .sort_values("month")
    )

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekdays = (
        order_base.groupby("weekday")
        .agg(orders=("order_id", "count"))
        .reindex(weekday_order)
        .reset_index()
    )

    same_state = (
        item_base[item_base["is_delivered"]]
        .groupby("same_state")
        .agg(
            items=("order_item_id", "count"),
            avg_freight=("freight_value", "mean"),
            avg_delivery=("delivery_days", "mean"),
            late_rate=("is_late", lambda s: s.mean() * 100),
            avg_review=("review_score", "mean"),
        )
        .reset_index()
    )
    same_state["segment"] = same_state["same_state"].map({True: "Same state", False: "Cross state"})
    for column in ["avg_freight", "avg_delivery", "late_rate", "avg_review"]:
        same_state[column] = same_state[column].round(2)

    comp = item_base[
        ((item_base["year"] == 2017) & item_base["month_num"].between(1, 8))
        | ((item_base["year"] == 2018) & item_base["month_num"].between(1, 8))
    ]
    cat_period = (
        comp.groupby(["category", "year"])
        .agg(
            items=("order_item_id", "count"),
            revenue=("price", "sum"),
            avg_review=("review_score", "mean"),
            late_rate=("is_late", lambda s: s.mean() * 100),
        )
        .reset_index()
    )
    pivot = cat_period.pivot(index="category", columns="year", values=["items", "revenue", "avg_review", "late_rate"])
    growth_rows = []
    for cat in pivot.index:
        def val(metric: str, year: int) -> float:
            try:
                value = pivot.loc[cat, (metric, year)]
                return 0.0 if pd.isna(value) else float(value)
            except KeyError:
                return 0.0

        items_2017 = val("items", 2017)
        items_2018 = val("items", 2018)
        revenue_2017 = val("revenue", 2017)
        revenue_2018 = val("revenue", 2018)
        if items_2017 >= 50 and items_2018 >= 100:
            growth_rows.append(
                {
                    "category": cat,
                    "items_2017": int(items_2017),
                    "items_2018": int(items_2018),
                    "item_growth": round((items_2018 - items_2017) / items_2017 * 100, 1),
                    "revenue_2018": round(revenue_2018, 0),
                    "revenue_growth": round((revenue_2018 - revenue_2017) / revenue_2017 * 100, 1)
                    if revenue_2017
                    else None,
                    "avg_review_2018": round(val("avg_review", 2018), 2),
                    "late_rate_2018": round(val("late_rate", 2018), 1),
                }
            )
    growth = pd.DataFrame(growth_rows)
    healthy_growth = growth[
        (growth["avg_review_2018"] >= 4.0) & (growth["late_rate_2018"] <= 10)
    ].sort_values("revenue_2018", ascending=False)

    data = {
        "summary": summary,
        "reviewDistribution": records(
            reviews["review_score"]
            .value_counts()
            .sort_index()
            .rename_axis("score")
            .reset_index(name="count")
            .assign(share=lambda frame: (frame["count"] / len(reviews) * 100).round(1))
        ),
        "monthlyOrders": records(monthly),
        "weekdayOrders": records(weekdays),
        "deliveryBins": records(delivery_bins),
        "sameState": records(same_state[["segment", "items", "avg_freight", "avg_delivery", "late_rate", "avg_review"]]),
        "topCategoriesByItems": records(category.sort_values("items", ascending=False).head(10)),
        "topCategoriesByRevenue": records(category.sort_values("revenue", ascending=False).head(10)),
        "riskCategories": records(
            category[category["items"] >= 500]
            .sort_values(["low_review_rate", "late_rate"], ascending=False)
            .head(12)
        ),
        "topStates": records(customer_states.sort_values("items", ascending=False).head(12)),
        "riskStates": records(
            customer_states[customer_states["items"] >= 500]
            .sort_values(["late_rate", "avg_delivery"], ascending=False)
            .head(12)
        ),
        "riskSellers": records(
            seller_perf[
                (seller_perf["orders"] >= 50)
                & (
                    (seller_perf["avg_review"] < 3.8)
                    | (seller_perf["late_rate"] > 14)
                    | (seller_perf["low_review_rate"] > 20)
                )
            ]
            .sort_values("revenue", ascending=False)
            .head(15)
        ),
        "healthySellers": records(
            seller_perf[
                (seller_perf["orders"] >= 80)
                & (seller_perf["avg_review"] >= 4.1)
                & (seller_perf["late_rate"] <= 8)
            ]
            .sort_values("revenue", ascending=False)
            .head(15)
        ),
        "growthCategories": records(healthy_growth.head(12)),
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        "window.DVD_DASHBOARD_DATA = "
        + json.dumps(data, indent=2, sort_keys=True)
        + ";\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
