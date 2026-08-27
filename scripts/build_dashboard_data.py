from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOK = ROOT_DIR / "Dataviz_proj_all_datasets.xlsx"
DEFAULT_OUT_FILE = ROOT_DIR / "dashboard" / "data.js"


@dataclass(frozen=True)
class TableSpec:
    csv_file: str
    excel_sheet: str
    required_columns: tuple[str, ...]


TABLES: dict[str, TableSpec] = {
    "customers": TableSpec(
        csv_file="customers_dataset.csv",
        excel_sheet="customers_dataset",
        required_columns=(
            "customer_id",
            "customer_unique_id",
            "customer_city",
            "customer_state",
        ),
    ),
    "sellers": TableSpec(
        csv_file="sellers_dataset.csv",
        excel_sheet="sellers_dataset",
        required_columns=("seller_id", "seller_city", "seller_state"),
    ),
    "orders": TableSpec(
        csv_file="orders_dataset.csv",
        excel_sheet="orders_dataset",
        required_columns=(
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ),
    ),
    "items": TableSpec(
        csv_file="order_items_dataset.csv",
        excel_sheet="order_items_dataset",
        required_columns=(
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "price",
            "freight_value",
        ),
    ),
    "reviews": TableSpec(
        csv_file="order_reviews_dataset.csv",
        excel_sheet="order_reviews_dataset",
        required_columns=("review_id", "order_id", "review_score"),
    ),
    "products": TableSpec(
        csv_file="products_dataset.csv",
        excel_sheet="products_dataset",
        required_columns=(
            "product_id",
            "product_category_name",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
            "product_photos_qty",
        ),
    ),
    "translation": TableSpec(
        csv_file="product_category_name_translation.csv",
        excel_sheet="product_category_name_translati",
        required_columns=("product_category_name", "product_category_name_english"),
    ),
    "mql": TableSpec(
        csv_file="marketing_qualified_leads_dataset.csv",
        excel_sheet="marketing_qualified_leads_datas",
        required_columns=("mql_id",),
    ),
    "closed": TableSpec(
        csv_file="closed_deals_dataset.csv",
        excel_sheet="closed_deals",
        required_columns=("mql_id", "seller_id"),
    ),
}

ORDER_DATE_COLUMNS = (
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
)
REVIEW_DATE_COLUMNS = ("review_creation_date", "review_answer_timestamp")
MQL_DATE_COLUMNS = ("first_contact_date",)
CLOSED_DATE_COLUMNS = ("won_date",)

NUMERIC_COLUMNS = {
    "items": ("order_item_id", "price", "freight_value"),
    "reviews": ("review_score",),
    "products": (
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
        "product_photos_qty",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build deterministic dashboard/data.js from the project raw datasets."
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Path to the combined raw dataset workbook. Used by default.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Optional directory of raw CSV files. Faster than the workbook for local reruns.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT_FILE,
        help="Output JavaScript file consumed by the dashboard.",
    )
    return parser.parse_args()


def pct(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return round(float(series.fillna(False).mean() * 100), 1)


def records(frame: pd.DataFrame, columns: list[str] | None = None) -> list[dict]:
    if columns:
        frame = frame[columns]
    return json.loads(frame.replace({np.nan: None}).to_json(orient="records"))


def round_columns(frame: pd.DataFrame, columns: list[str], places: int = 2) -> pd.DataFrame:
    for column in columns:
        frame[column] = frame[column].round(places)
    return frame


def sort_rows(frame: pd.DataFrame, by: list[str], ascending: list[bool] | bool) -> pd.DataFrame:
    return frame.sort_values(by=by, ascending=ascending, kind="mergesort")


def read_csv_tables(source_dir: Path) -> tuple[dict[str, pd.DataFrame], str]:
    if not source_dir.exists():
        raise FileNotFoundError(f"CSV source directory does not exist: {source_dir}")

    tables = {}
    for name, spec in TABLES.items():
        path = source_dir / spec.csv_file
        if not path.exists():
            raise FileNotFoundError(f"Missing required CSV for {name}: {path}")
        tables[name] = pd.read_csv(path)
    return tables, f"csv:{source_dir.name}"


def read_workbook_tables(workbook_path: Path) -> tuple[dict[str, pd.DataFrame], str]:
    if not workbook_path.exists():
        raise FileNotFoundError(
            f"Workbook not found: {workbook_path}. Pass --source-dir with raw CSVs if needed."
        )

    book = pd.ExcelFile(workbook_path)
    try:
        available_sheets = set(book.sheet_names)
        tables = {}
        for name, spec in TABLES.items():
            if spec.excel_sheet not in available_sheets:
                raise ValueError(
                    f"Workbook is missing sheet '{spec.excel_sheet}' required for {name}."
                )
            tables[name] = pd.read_excel(book, sheet_name=spec.excel_sheet)
    finally:
        book.close()
    return tables, f"workbook:{workbook_path.name}"


def clean_column_names(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    cleaned = {}
    for name, frame in tables.items():
        frame = frame.copy()
        frame.columns = [str(column).strip() for column in frame.columns]
        cleaned[name] = frame
    return cleaned


def validate_required_columns(tables: dict[str, pd.DataFrame]) -> None:
    errors = []
    for name, spec in TABLES.items():
        missing = sorted(set(spec.required_columns) - set(tables[name].columns))
        if missing:
            errors.append(f"{name}: missing columns {', '.join(missing)}")
    if errors:
        raise ValueError("Raw dataset validation failed:\n- " + "\n- ".join(errors))


def coerce_numeric_columns(tables: dict[str, pd.DataFrame]) -> None:
    for table_name, columns in NUMERIC_COLUMNS.items():
        frame = tables[table_name]
        for column in columns:
            if column in frame.columns:
                frame[column] = pd.to_numeric(frame[column], errors="coerce")


def coerce_dates(frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")


def normalize_category_names(
    products: pd.DataFrame, translation: pd.DataFrame
) -> pd.DataFrame:
    category_names = dict(
        zip(
            translation["product_category_name"],
            translation["product_category_name_english"],
        )
    )
    products = products.copy()
    products["category"] = (
        products["product_category_name"]
        .map(category_names)
        .fillna(products["product_category_name"])
        .fillna("unknown")
    )
    return products


def prepare_tables(raw_tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    tables = clean_column_names(raw_tables)
    validate_required_columns(tables)
    coerce_numeric_columns(tables)

    coerce_dates(tables["orders"], ORDER_DATE_COLUMNS)
    coerce_dates(tables["reviews"], REVIEW_DATE_COLUMNS)
    coerce_dates(tables["mql"], MQL_DATE_COLUMNS)
    coerce_dates(tables["closed"], CLOSED_DATE_COLUMNS)
    tables["products"] = normalize_category_names(tables["products"], tables["translation"])
    return tables


def build_review_rollup(reviews: pd.DataFrame) -> pd.DataFrame:
    return (
        reviews.groupby("order_id", dropna=False)
        .agg(review_score=("review_score", "mean"), review_count=("review_id", "count"))
        .reset_index()
    )


def add_order_features(order_base: pd.DataFrame) -> pd.DataFrame:
    order_base = order_base.copy()
    order_base["delivery_days"] = (
        order_base["order_delivered_customer_date"]
        - order_base["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    order_base["delay_days"] = (
        order_base["order_delivered_customer_date"]
        - order_base["order_estimated_delivery_date"]
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
    return order_base


def add_item_features(item_base: pd.DataFrame) -> pd.DataFrame:
    item_base = add_order_features(item_base)
    item_base["same_state"] = item_base["customer_state"].eq(item_base["seller_state"])
    item_base["year"] = item_base["order_purchase_timestamp"].dt.year
    item_base["month_num"] = item_base["order_purchase_timestamp"].dt.month
    item_base["freight_ratio"] = (
        item_base["freight_value"] / item_base["price"].replace({0: np.nan})
    )
    return item_base


def build_analysis_tables(tables: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    customers = tables["customers"]
    sellers = tables["sellers"]
    orders = tables["orders"]
    items = tables["items"]
    products = tables["products"]
    reviews = tables["reviews"]

    review_by_order = build_review_rollup(reviews)
    order_base = (
        orders.merge(customers, on="customer_id", how="left")
        .merge(review_by_order, on="order_id", how="left")
        .pipe(add_order_features)
    )

    product_columns = [
        "product_id",
        "category",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
        "product_photos_qty",
    ]
    order_columns = [
        "order_id",
        "customer_id",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "order_status",
    ]
    item_base = (
        items.merge(products[product_columns], on="product_id", how="left")
        .merge(orders[order_columns], on="order_id", how="left")
        .merge(
            customers[["customer_id", "customer_state", "customer_city"]],
            on="customer_id",
            how="left",
        )
        .merge(sellers, on="seller_id", how="left")
        .merge(review_by_order, on="order_id", how="left")
        .pipe(add_item_features)
    )
    return order_base, item_base


def build_summary(
    tables: dict[str, pd.DataFrame], order_base: pd.DataFrame
) -> dict[str, int | float]:
    reviews = tables["reviews"]
    mql = tables["mql"]
    closed = tables["closed"]
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
        "lateRate": pct(order_base.loc[order_base["is_delivered"], "is_late"]),
        "avgDeliveryDays": round(
            float(order_base.loc[order_base["is_delivered"], "delivery_days"].mean()),
            1,
        ),
        "medianDeliveryDays": round(
            float(order_base.loc[order_base["is_delivered"], "delivery_days"].median()),
            1,
        ),
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


def build_category_summary(item_base: pd.DataFrame) -> pd.DataFrame:
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


def build_state_summary(item_base: pd.DataFrame) -> pd.DataFrame:
    customer_states = (
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
        customer_states,
        ["revenue", "avg_review", "late_rate", "avg_delivery", "low_review_rate"],
    )


def build_seller_summary(item_base: pd.DataFrame) -> pd.DataFrame:
    seller_perf = (
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
        seller_perf,
        ["revenue", "avg_review", "late_rate", "low_review_rate", "avg_delivery"],
    )


def build_delivery_bins(order_base: pd.DataFrame) -> pd.DataFrame:
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
    return round_columns(delivery_bins, ["avg_review", "low_review_rate"])


def build_delay_impact_summary(order_base: pd.DataFrame) -> pd.DataFrame:
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
    return round_columns(summary, ["avg_review", "low_review_rate", "avg_delay_days"])


def build_delay_bins(order_base: pd.DataFrame) -> pd.DataFrame:
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
    bins = (
        delivered.groupby("delay_bin", observed=True)
        .agg(
            orders=("order_id", "count"),
            avg_review=("review_score", "mean"),
            low_review_rate=("low_review", lambda s: s.mean() * 100),
        )
        .reset_index()
        .rename(columns={"delay_bin": "range"})
    )
    bins["range"] = bins["range"].astype(str)
    return round_columns(bins, ["avg_review", "low_review_rate"])


def build_time_summaries(order_base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = (
        order_base.groupby("month", dropna=False)
        .agg(orders=("order_id", "count"))
        .reset_index()
        .sort_values("month", kind="mergesort")
    )

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekdays = (
        order_base.groupby("weekday")
        .agg(orders=("order_id", "count"))
        .reindex(weekday_order)
        .fillna({"orders": 0})
        .reset_index()
    )
    return monthly, weekdays


def build_same_state_summary(item_base: pd.DataFrame) -> pd.DataFrame:
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
    return round_columns(
        same_state,
        ["avg_freight", "avg_delivery", "late_rate", "avg_review"],
    )


def build_growth_summary(item_base: pd.DataFrame) -> pd.DataFrame:
    comp = item_base[
        ((item_base["year"] == 2017) & item_base["month_num"].between(1, 8))
        | ((item_base["year"] == 2018) & item_base["month_num"].between(1, 8))
    ]
    cat_period = (
        comp.groupby(["category", "year"], dropna=False)
        .agg(
            items=("order_item_id", "count"),
            revenue=("price", "sum"),
            avg_review=("review_score", "mean"),
            late_rate=("is_late", lambda s: s.mean() * 100),
        )
        .reset_index()
    )
    pivot = cat_period.pivot(
        index="category",
        columns="year",
        values=["items", "revenue", "avg_review", "late_rate"],
    )
    growth_rows = []
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
            growth_rows.append(
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

    growth = pd.DataFrame(growth_rows)
    if growth.empty:
        return growth
    return sort_rows(
        growth[
            (growth["avg_review_2018"] >= 4.0) & (growth["late_rate_2018"] <= 10)
        ],
        ["revenue_2018", "category"],
        [False, True],
    )


def build_dashboard_data(
    tables: dict[str, pd.DataFrame],
    source_label: str,
) -> dict[str, object]:
    order_base, item_base = build_analysis_tables(tables)
    category = build_category_summary(item_base)
    customer_states = build_state_summary(item_base)
    seller_perf = build_seller_summary(item_base)
    delivery_bins = build_delivery_bins(order_base)
    monthly, weekdays = build_time_summaries(order_base)
    same_state = build_same_state_summary(item_base)
    delay_impact = build_delay_impact_summary(order_base)
    delay_bins = build_delay_bins(order_base)
    healthy_growth = build_growth_summary(item_base)

    row_counts = {name: int(len(frame)) for name, frame in sorted(tables.items())}
    summary = build_summary(tables, order_base)

    return {
        "metadata": {
            "source": source_label,
            "rowCounts": row_counts,
            "pipelineVersion": 2,
        },
        "summary": summary,
        "statusCounts": records(
            tables["orders"]["order_status"]
            .value_counts()
            .sort_index()
            .rename_axis("status")
            .reset_index(name="orders")
        ),
        "reviewDistribution": records(
            tables["reviews"]["review_score"]
            .value_counts()
            .sort_index()
            .rename_axis("score")
            .reset_index(name="count")
            .assign(
                share=lambda frame: (
                    frame["count"] / len(tables["reviews"]) * 100
                ).round(1)
            )
        ),
        "monthlyOrders": records(monthly),
        "weekdayOrders": records(weekdays),
        "deliveryBins": records(delivery_bins),
        "delayImpactSummary": records(delay_impact),
        "delayBins": records(delay_bins),
        "sameState": records(
            same_state[
                [
                    "segment",
                    "items",
                    "avg_freight",
                    "avg_delivery",
                    "late_rate",
                    "avg_review",
                ]
            ]
        ),
        "regionalDemand": records(
            sort_rows(customer_states, ["revenue", "customer_state"], [False, True])
        ),
        "regionalRisk": records(
            sort_rows(
                customer_states[customer_states["items"] >= 500],
                ["late_rate", "avg_delivery", "customer_state"],
                [False, False, True],
            )
        ),
        "topCategoriesByItems": records(
            sort_rows(category, ["items", "category"], [False, True]).head(10)
        ),
        "topCategoriesByRevenue": records(
            sort_rows(category, ["revenue", "category"], [False, True]).head(10)
        ),
        "riskCategories": records(
            sort_rows(
                category[category["items"] >= 500],
                ["low_review_rate", "late_rate", "category"],
                [False, False, True],
            ).head(12)
        ),
        "topStates": records(
            sort_rows(customer_states, ["items", "customer_state"], [False, True]).head(12)
        ),
        "riskStates": records(
            sort_rows(
                customer_states[customer_states["items"] >= 500],
                ["late_rate", "avg_delivery", "customer_state"],
                [False, False, True],
            ).head(12)
        ),
        "riskSellers": records(
            sort_rows(
                seller_perf[
                    (seller_perf["orders"] >= 50)
                    & (
                        (seller_perf["avg_review"] < 3.8)
                        | (seller_perf["late_rate"] > 14)
                        | (seller_perf["low_review_rate"] > 20)
                    )
                ],
                ["revenue", "seller_id"],
                [False, True],
            ).head(15)
        ),
        "healthySellers": records(
            sort_rows(
                seller_perf[
                    (seller_perf["orders"] >= 80)
                    & (seller_perf["avg_review"] >= 4.1)
                    & (seller_perf["late_rate"] <= 8)
                ],
                ["revenue", "seller_id"],
                [False, True],
            ).head(15)
        ),
        "growthCategories": records(healthy_growth.head(12)),
    }


def load_raw_tables(args: argparse.Namespace) -> tuple[dict[str, pd.DataFrame], str]:
    if args.source_dir:
        return read_csv_tables(args.source_dir)
    return read_workbook_tables(args.workbook)


def write_dashboard_data(data: dict[str, object], out_file: Path) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(
        "window.DVD_DASHBOARD_DATA = "
        + json.dumps(data, indent=2, sort_keys=True)
        + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    raw_tables, source_label = load_raw_tables(args)
    tables = prepare_tables(raw_tables)
    data = build_dashboard_data(tables, source_label)
    write_dashboard_data(data, args.out)
    print(
        f"Wrote {args.out.relative_to(ROOT_DIR) if args.out.is_relative_to(ROOT_DIR) else args.out} "
        f"from {source_label}"
    )


if __name__ == "__main__":
    main()
