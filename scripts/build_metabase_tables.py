"""Export the cleaned analysis tables as CSVs for loading into Postgres/Metabase.

Reuses the validated cleaning, joins, and derived features from
``build_dashboard_data`` so the Metabase dashboards read the same numbers as the
report and the static dashboard. Adds a ``purchase_week`` date (Monday of the
order-purchase week) to support the weekly-tracking dashboards described in the
team dashboard brief.

Usage::

    python3 scripts/build_metabase_tables.py                 # from the workbook
    python3 scripts/build_metabase_tables.py --source-dir /path/to/raw_csvs
    python3 scripts/build_metabase_tables.py --out-dir metabase/data
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from build_dashboard_data import (
    DEFAULT_WORKBOOK,
    build_analysis_tables,
    prepare_tables,
    read_csv_tables,
    read_workbook_tables,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT_DIR / "metabase" / "data"

ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "customer_state",
    "customer_city",
    "order_status",
    "order_purchase_timestamp",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "review_score",
    "delivery_days",
    "delay_days",
    "is_delivered",
    "is_late",
    "low_review",
    "one_star",
    "month",
    "weekday",
    "purchase_week",
]

ITEM_COLUMNS = [
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "category",
    "price",
    "freight_value",
    "freight_ratio",
    "customer_state",
    "customer_city",
    "seller_state",
    "seller_city",
    "order_status",
    "order_purchase_timestamp",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "review_score",
    "delivery_days",
    "delay_days",
    "is_delivered",
    "is_late",
    "low_review",
    "one_star",
    "same_state",
    "year",
    "month_num",
    "month",
    "weekday",
    "purchase_week",
]


def add_purchase_week(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    ts = frame["order_purchase_timestamp"]
    # Monday of the purchase week, as a plain date.
    frame["purchase_week"] = (ts - pd.to_timedelta(ts.dt.weekday, unit="D")).dt.normalize()
    return frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Path to the source workbook (default: committed dataset).",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Optional directory of extracted raw CSVs (faster than the workbook).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Directory to write order_base.csv and item_base.csv.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.source_dir is not None:
        raw_tables, source = read_csv_tables(args.source_dir)
    else:
        raw_tables, source = read_workbook_tables(args.workbook)
    print(f"Loaded raw tables from {source}")

    tables = prepare_tables(raw_tables)
    order_base, item_base = build_analysis_tables(tables)
    order_base = add_purchase_week(order_base)
    item_base = add_purchase_week(item_base)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    order_out = args.out_dir / "order_base.csv"
    item_out = args.out_dir / "item_base.csv"

    order_base[ORDER_COLUMNS].to_csv(order_out, index=False)
    item_base[ITEM_COLUMNS].to_csv(item_out, index=False)

    print(f"Wrote {len(order_base):,} order rows -> {order_out}")
    print(f"Wrote {len(item_base):,} item rows  -> {item_out}")


if __name__ == "__main__":
    main()
