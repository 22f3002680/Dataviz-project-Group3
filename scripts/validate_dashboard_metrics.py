from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from build_dashboard_data import (
    DEFAULT_OUT_FILE,
    DEFAULT_WORKBOOK,
    prepare_tables,
    read_csv_tables,
    read_workbook_tables,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PREFIX = "window.DVD_DASHBOARD_DATA = "


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate dashboard metrics against independent source-data calculations."
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Path to the combined raw dataset workbook.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Optional raw CSV directory for faster local validation.",
    )
    parser.add_argument(
        "--dashboard-data",
        type=Path,
        default=DEFAULT_OUT_FILE,
        help="Path to dashboard/data.js.",
    )
    return parser.parse_args()


def load_dashboard_data(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8").strip()
    if not text.startswith(DATA_PREFIX) or not text.endswith(";"):
        raise ValueError(f"{path} does not look like dashboard/data.js")
    return json.loads(text.removeprefix(DATA_PREFIX).removesuffix(";"))


def pct(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return round(float(series.fillna(False).mean() * 100), 1)


def records(frame: pd.DataFrame, columns: list[str] | None = None) -> list[dict[str, Any]]:
    if columns:
        frame = frame[columns]
    return json.loads(frame.replace({np.nan: None}).to_json(orient="records"))


def round_columns(frame: pd.DataFrame, columns: list[str], places: int = 2) -> pd.DataFrame:
    for column in columns:
        frame[column] = frame[column].round(places)
    return frame


def sort_rows(frame: pd.DataFrame, by: list[str], ascending: list[bool] | bool) -> pd.DataFrame:
    return frame.sort_values(by=by, ascending=ascending, kind="mergesort")


def review_by_order(reviews: pd.DataFrame) -> pd.DataFrame:
    return (
        reviews.groupby("order_id", dropna=False)
        .agg(review_score=("review_score", "mean"), review_count=("review_id", "count"))
        .reset_index()
    )


def order_metrics_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    orders = tables["orders"]
    customers = tables["customers"]
    reviews = review_by_order(tables["reviews"])
    frame = orders.merge(customers, on="customer_id", how="left").merge(
        reviews, on="order_id", how="left"
    )
    frame["delivery_days"] = (
        frame["order_delivered_customer_date"] - frame["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    frame["delay_days"] = (
        frame["order_delivered_customer_date"] - frame["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400
    frame["is_delivered"] = (
        frame["order_status"].eq("delivered")
        & frame["order_delivered_customer_date"].notna()
    )
    frame["is_late"] = frame["is_delivered"] & (frame["delay_days"] > 0)
    frame["low_review"] = frame["review_score"].le(2)
    frame["month"] = frame["order_purchase_timestamp"].dt.to_period("M").astype(str)
    frame["weekday"] = frame["order_purchase_timestamp"].dt.day_name()
    return frame


def item_metrics_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    items = tables["items"]
    products = tables["products"]
    orders = tables["orders"]
    customers = tables["customers"]
    sellers = tables["sellers"]
    reviews = review_by_order(tables["reviews"])

    frame = (
        items.merge(products[["product_id", "category"]], on="product_id", how="left")
        .merge(
            orders[
                [
                    "order_id",
                    "customer_id",
                    "order_status",
                    "order_purchase_timestamp",
                    "order_delivered_customer_date",
                    "order_estimated_delivery_date",
                ]
            ],
            on="order_id",
            how="left",
        )
        .merge(
            customers[["customer_id", "customer_state", "customer_city"]],
            on="customer_id",
            how="left",
        )
        .merge(sellers, on="seller_id", how="left")
        .merge(reviews, on="order_id", how="left")
    )
    frame["delivery_days"] = (
        frame["order_delivered_customer_date"] - frame["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    frame["delay_days"] = (
        frame["order_delivered_customer_date"] - frame["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400
    frame["is_delivered"] = (
        frame["order_status"].eq("delivered")
        & frame["order_delivered_customer_date"].notna()
    )
    frame["is_late"] = frame["is_delivered"] & (frame["delay_days"] > 0)
    frame["low_review"] = frame["review_score"].le(2)
    frame["same_state"] = frame["customer_state"].eq(frame["seller_state"])
    frame["year"] = frame["order_purchase_timestamp"].dt.year
    frame["month_num"] = frame["order_purchase_timestamp"].dt.month
    frame["freight_ratio"] = frame["freight_value"] / frame["price"].replace({0: np.nan})
    return frame


def expected_summary(
    tables: dict[str, pd.DataFrame], order_base: pd.DataFrame
) -> dict[str, int | float]:
    reviews = tables["reviews"]
    mql = tables["mql"]
    closed = tables["closed"]
    delivered = order_base[order_base["is_delivered"]]
    return {
        "orders": int(len(tables["orders"])),
        "items": int(len(tables["items"])),
        "customers": int(tables["customers"]["customer_unique_id"].nunique()),
        "sellers": int(tables["sellers"]["seller_id"].nunique()),
        "products": int(tables["products"]["product_id"].nunique()),
        "categories": int(tables["products"]["category"].nunique()),
        "avgReview": round(float(reviews["review_score"].mean()), 2),
        "highReviewRate": round(float(reviews["review_score"].ge(4).mean() * 100), 1),
        "lowReviewRate": round(float(reviews["review_score"].le(2).mean() * 100), 1),
        "deliveredRate": round(float(order_base["is_delivered"].mean() * 100), 1),
        "lateRate": pct(delivered["is_late"]),
        "avgDeliveryDays": round(float(delivered["delivery_days"].mean()), 1),
        "medianDeliveryDays": round(float(delivered["delivery_days"].median()), 1),
        "lateLowReviewRate": pct(order_base.loc[order_base["is_late"], "low_review"]),
        "onTimeLowReviewRate": pct(
            order_base.loc[
                order_base["is_delivered"] & ~order_base["is_late"], "low_review"
            ]
        ),
        "mql": int(len(mql)),
        "closedDeals": int(len(closed)),
        "winRate": round(float(len(closed) / len(mql) * 100), 1) if len(mql) else 0.0,
    }


def expected_review_distribution(reviews: pd.DataFrame) -> list[dict[str, Any]]:
    return records(
        reviews["review_score"]
        .value_counts()
        .sort_index()
        .rename_axis("score")
        .reset_index(name="count")
        .assign(share=lambda frame: (frame["count"] / len(reviews) * 100).round(1))
    )


def expected_delivery_bins(order_base: pd.DataFrame) -> list[dict[str, Any]]:
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
    return records(round_columns(delivery_bins, ["avg_review", "low_review_rate"]))


def expected_delay_impact_summary(order_base: pd.DataFrame) -> list[dict[str, Any]]:
    delivered = order_base[order_base["is_delivered"]].copy()
    delivered["segment"] = delivered["is_late"].map(
        {True: "Late", False: "On-time or early"}
    )
    summary = (
        delivered.groupby("segment", dropna=False)
        .agg(
            orders=("order_id", "count"),
            avg_review=("review_score", "mean"),
            low_review_rate=("low_review", lambda s: s.mean() * 100),
            avg_delay_days=("delay_days", "mean"),
        )
        .reset_index()
    )
    return records(round_columns(summary, ["avg_review", "low_review_rate", "avg_delay_days"]))


def expected_delay_bins(order_base: pd.DataFrame) -> list[dict[str, Any]]:
    delivered = order_base[order_base["is_delivered"] & order_base["delay_days"].notna()].copy()
    delivered["delay_bin"] = pd.cut(
        delivered["delay_days"],
        bins=[-np.inf, 0, 3, 7, 14, 21, np.inf],
        labels=[
            "Early / on-time",
            "1-3 days late",
            "4-7 days late",
            "8-14 days late",
            "15-21 days late",
            "22+ days late",
        ],
        include_lowest=True,
    )
    delay_bins = (
        delivered.groupby("delay_bin", observed=True)
        .agg(
            orders=("order_id", "count"),
            avg_review=("review_score", "mean"),
            low_review_rate=("low_review", lambda s: s.mean() * 100),
        )
        .reset_index()
        .rename(columns={"delay_bin": "range"})
    )
    delay_bins["range"] = delay_bins["range"].astype(str)
    return records(round_columns(delay_bins, ["avg_review", "low_review_rate"]))


def category_summary(item_base: pd.DataFrame) -> pd.DataFrame:
    category = (
        item_base.groupby("category", dropna=False)
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
    return round_columns(
        category,
        [
            "revenue",
            "avg_price",
            "avg_review",
            "late_rate",
            "low_review_rate",
            "avg_delivery",
            "freight_ratio",
        ],
    )


def state_summary(item_base: pd.DataFrame) -> pd.DataFrame:
    states = (
        item_base.groupby("customer_state", dropna=False)
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
    return round_columns(
        states,
        ["revenue", "avg_review", "late_rate", "avg_delivery", "low_review_rate"],
    )


def seller_summary(item_base: pd.DataFrame) -> pd.DataFrame:
    sellers = (
        item_base.groupby(["seller_id", "seller_state", "seller_city"], dropna=False)
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
    return round_columns(
        sellers,
        ["revenue", "avg_review", "late_rate", "low_review_rate", "avg_delivery"],
    )


def expected_grouped_outputs(item_base: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    categories = category_summary(item_base)
    states = state_summary(item_base)
    sellers = seller_summary(item_base)
    return {
        "topCategoriesByItems": records(
            sort_rows(categories, ["items", "category"], [False, True]).head(10)
        ),
        "topCategoriesByRevenue": records(
            sort_rows(categories, ["revenue", "category"], [False, True]).head(10)
        ),
        "riskCategories": records(
            sort_rows(
                categories[categories["items"] >= 500],
                ["low_review_rate", "late_rate", "category"],
                [False, False, True],
            ).head(12)
        ),
        "topStates": records(
            sort_rows(states, ["items", "customer_state"], [False, True]).head(12)
        ),
        "riskStates": records(
            sort_rows(
                states[states["items"] >= 500],
                ["late_rate", "avg_delivery", "customer_state"],
                [False, False, True],
            ).head(12)
        ),
        "riskSellers": records(
            sort_rows(
                sellers[
                    (sellers["orders"] >= 50)
                    & (
                        (sellers["avg_review"] < 3.8)
                        | (sellers["late_rate"] > 14)
                        | (sellers["low_review_rate"] > 20)
                    )
                ],
                ["revenue", "seller_id"],
                [False, True],
            ).head(15)
        ),
        "healthySellers": records(
            sort_rows(
                sellers[
                    (sellers["orders"] >= 80)
                    & (sellers["avg_review"] >= 4.1)
                    & (sellers["late_rate"] <= 8)
                ],
                ["revenue", "seller_id"],
                [False, True],
            ).head(15)
        ),
    }


def expected_growth_categories(item_base: pd.DataFrame) -> list[dict[str, Any]]:
    comparable = item_base[
        ((item_base["year"] == 2017) & item_base["month_num"].between(1, 8))
        | ((item_base["year"] == 2018) & item_base["month_num"].between(1, 8))
    ]
    category_period = (
        comparable.groupby(["category", "year"], dropna=False)
        .agg(
            items=("order_item_id", "count"),
            revenue=("price", "sum"),
            avg_review=("review_score", "mean"),
            late_rate=("is_late", lambda s: s.mean() * 100),
        )
        .reset_index()
    )
    pivot = category_period.pivot(
        index="category",
        columns="year",
        values=["items", "revenue", "avg_review", "late_rate"],
    )

    rows = []
    for category in pivot.index:

        def val(metric: str, year: int) -> float:
            try:
                value = pivot.loc[category, (metric, year)]
                return 0.0 if pd.isna(value) else float(value)
            except KeyError:
                return 0.0

        items_2017 = val("items", 2017)
        items_2018 = val("items", 2018)
        revenue_2017 = val("revenue", 2017)
        revenue_2018 = val("revenue", 2018)
        if items_2017 >= 50 and items_2018 >= 100:
            rows.append(
                {
                    "category": category,
                    "items_2017": int(items_2017),
                    "items_2018": int(items_2018),
                    "item_growth": round((items_2018 - items_2017) / items_2017 * 100, 1),
                    "revenue_2018": round(revenue_2018, 0),
                    "revenue_growth": round(
                        (revenue_2018 - revenue_2017) / revenue_2017 * 100, 1
                    )
                    if revenue_2017
                    else None,
                    "avg_review_2018": round(val("avg_review", 2018), 2),
                    "late_rate_2018": round(val("late_rate", 2018), 1),
                }
            )

    growth = pd.DataFrame(rows)
    if growth.empty:
        return []
    healthy_growth = sort_rows(
        growth[
            (growth["avg_review_2018"] >= 4.0) & (growth["late_rate_2018"] <= 10)
        ],
        ["revenue_2018", "category"],
        [False, True],
    )
    return records(healthy_growth.head(12))


def same_state_summary(item_base: pd.DataFrame) -> list[dict[str, Any]]:
    same_state = (
        item_base[item_base["is_delivered"]]
        .groupby("same_state", dropna=False)
        .agg(
            items=("order_item_id", "count"),
            avg_freight=("freight_value", "mean"),
            avg_delivery=("delivery_days", "mean"),
            late_rate=("is_late", lambda s: s.mean() * 100),
            avg_review=("review_score", "mean"),
        )
        .reset_index()
    )
    same_state["segment"] = same_state["same_state"].map(
        {True: "Same state", False: "Cross state"}
    )
    same_state = round_columns(
        same_state, ["avg_freight", "avg_delivery", "late_rate", "avg_review"]
    )
    return records(
        same_state[
            ["segment", "items", "avg_freight", "avg_delivery", "late_rate", "avg_review"]
        ]
    )


def metadata_row_counts(tables: dict[str, pd.DataFrame]) -> dict[str, int]:
    return {name: int(len(frame)) for name, frame in sorted(tables.items())}


def compare(label: str, expected: Any, observed: Any, failures: list[str]) -> None:
    if expected != observed:
        failures.append(
            f"{label}: expected {json.dumps(expected, sort_keys=True)[:600]}, "
            f"observed {json.dumps(observed, sort_keys=True)[:600]}"
        )


def load_raw_tables(args: argparse.Namespace) -> tuple[dict[str, pd.DataFrame], str]:
    if args.source_dir:
        return read_csv_tables(args.source_dir)
    return read_workbook_tables(args.workbook)


def main() -> None:
    args = parse_args()
    dashboard = load_dashboard_data(args.dashboard_data)
    raw_tables, source_label = load_raw_tables(args)
    tables = prepare_tables(raw_tables)
    order_base = order_metrics_table(tables)
    item_base = item_metrics_table(tables)

    checks = 0
    failures: list[str] = []

    summary = expected_summary(tables, order_base)
    for metric_name, expected_value in summary.items():
        compare(
            f"summary.{metric_name}",
            expected_value,
            dashboard["summary"].get(metric_name),
            failures,
        )
        checks += 1

    compare("metadata.source", source_label, dashboard["metadata"].get("source"), failures)
    checks += 1
    compare(
        "metadata.rowCounts",
        metadata_row_counts(tables),
        dashboard["metadata"].get("rowCounts"),
        failures,
    )
    checks += 1
    compare(
        "reviewDistribution",
        expected_review_distribution(tables["reviews"]),
        dashboard["reviewDistribution"],
        failures,
    )
    checks += 1
    compare("deliveryBins", expected_delivery_bins(order_base), dashboard["deliveryBins"], failures)
    checks += 1
    compare(
        "delayImpactSummary",
        expected_delay_impact_summary(order_base),
        dashboard["delayImpactSummary"],
        failures,
    )
    checks += 1
    compare("delayBins", expected_delay_bins(order_base), dashboard["delayBins"], failures)
    checks += 1
    compare("sameState", same_state_summary(item_base), dashboard["sameState"], failures)
    checks += 1
    states = state_summary(item_base)
    compare(
        "regionalDemand",
        records(sort_rows(states, ["revenue", "customer_state"], [False, True])),
        dashboard["regionalDemand"],
        failures,
    )
    checks += 1
    compare(
        "regionalRisk",
        records(
            sort_rows(
                states[states["items"] >= 500],
                ["late_rate", "avg_delivery", "customer_state"],
                [False, False, True],
            )
        ),
        dashboard["regionalRisk"],
        failures,
    )
    checks += 1
    compare(
        "growthCategories",
        expected_growth_categories(item_base),
        dashboard["growthCategories"],
        failures,
    )
    checks += 1

    for output_name, expected_rows in expected_grouped_outputs(item_base).items():
        compare(output_name, expected_rows, dashboard[output_name], failures)
        checks += 1

    if failures:
        print(f"Metric validation failed: {len(failures)} of {checks} checks failed")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print(f"Metric validation passed: {checks} checks")
    print(
        "Validated summary KPIs, row counts, review distribution, delivery bins, delay impact, "
        "same-state delivery, category rankings, state rankings, seller lists, "
        "and growth categories."
    )


if __name__ == "__main__":
    main()
