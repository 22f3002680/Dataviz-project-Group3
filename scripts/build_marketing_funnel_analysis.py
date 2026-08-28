"""Build the marketing funnel and seller-acquisition analysis for Issue #10."""

from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOK = ROOT_DIR / "Dataviz_proj_all_datasets.xlsx"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "docs" / "eda"
POST_WIN_DAYS = 30
LANDING_PAGE_MIN_MQLS = 20
UNKNOWN_ORIGIN = "Unknown / missing"

SOURCES = {
    "mql": ("marketing_qualified_leads_dataset.csv", "marketing_qualified_leads_datas"),
    "closed": ("closed_deals_dataset.csv", "closed_deals"),
    "orders": ("orders_dataset.csv", "orders_dataset"),
    "items": ("order_items_dataset.csv", "order_items_dataset"),
    "reviews": ("order_reviews_dataset.csv", "order_reviews_dataset"),
}

REQUIRED_COLUMNS = {
    "mql": {"mql_id", "first_contact_date", "landing_page_id", "origin"},
    "closed": {"mql_id", "seller_id", "won_date"},
    "orders": {"order_id", "order_purchase_timestamp"},
    "items": {"order_id", "order_item_id", "seller_id", "price"},
    "reviews": {"review_id", "order_id", "review_score"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the reproducible Issue #10 marketing-funnel report."
    )
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Optional directory containing the five source CSV files.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def round_half_up(value: float, places: int = 2) -> float:
    quantum = Decimal("1").scaleb(-places)
    return float(Decimal(str(float(value))).quantize(quantum, rounding=ROUND_HALF_UP))


def percentage(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round_half_up(float(numerator) / float(denominator) * 100, 2)


def load_tables(
    workbook: Path = DEFAULT_WORKBOOK, source_dir: Path | None = None
) -> dict[str, pd.DataFrame]:
    if source_dir is not None:
        if not source_dir.exists():
            raise FileNotFoundError(f"CSV source directory not found: {source_dir}")
        tables = {
            name: pd.read_csv(source_dir / csv_name, low_memory=False)
            for name, (csv_name, _) in SOURCES.items()
        }
    else:
        if not workbook.exists():
            raise FileNotFoundError(f"Workbook not found: {workbook}")
        book = pd.ExcelFile(workbook)
        try:
            tables = {
                name: pd.read_excel(book, sheet_name=sheet_name)
                for name, (_, sheet_name) in SOURCES.items()
            }
        finally:
            book.close()

    for name, frame in tables.items():
        frame.columns = [str(column).strip() for column in frame.columns]
        missing = sorted(REQUIRED_COLUMNS[name] - set(frame.columns))
        if missing:
            raise ValueError(f"{name} is missing required columns: {', '.join(missing)}")

    tables["mql"]["first_contact_date"] = pd.to_datetime(
        tables["mql"]["first_contact_date"], errors="coerce"
    )
    tables["closed"]["won_date"] = pd.to_datetime(
        tables["closed"]["won_date"], errors="coerce"
    )
    tables["orders"]["order_purchase_timestamp"] = pd.to_datetime(
        tables["orders"]["order_purchase_timestamp"], errors="coerce"
    )
    tables["items"]["price"] = pd.to_numeric(
        tables["items"]["price"], errors="coerce"
    )
    tables["reviews"]["review_score"] = pd.to_numeric(
        tables["reviews"]["review_score"], errors="coerce"
    )
    return tables


def normalize_origin(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").str.strip()
    missing = normalized.isna() | normalized.eq("") | normalized.str.lower().eq("unknown")
    return normalized.mask(missing, UNKNOWN_ORIGIN)


def validate_source(tables: dict[str, pd.DataFrame]) -> None:
    mql = tables["mql"]
    closed = tables["closed"]
    errors = []
    if mql["mql_id"].isna().any():
        errors.append("MQL IDs contain missing values")
    if closed[["mql_id", "seller_id"]].isna().any().any():
        errors.append("closed deals contain missing MQL or seller IDs")
    if mql["mql_id"].duplicated().any():
        errors.append("MQL IDs are not unique")
    if closed["mql_id"].duplicated().any():
        errors.append("closed-deal MQL IDs are not unique")
    if closed["seller_id"].duplicated().any():
        errors.append("closed-deal seller IDs are not unique")
    unmatched = ~closed["mql_id"].isin(mql["mql_id"])
    if unmatched.any():
        errors.append(f"{int(unmatched.sum())} closed deals do not match an MQL")
    if errors:
        raise ValueError("Marketing-funnel validation failed:\n- " + "\n- ".join(errors))


def conversion_summary(funnel: pd.DataFrame, dimension: str) -> pd.DataFrame:
    result = (
        funnel.groupby(dimension, dropna=False)
        .agg(mqls=("mql_id", "nunique"), observed_wins=("is_won", "sum"))
        .reset_index()
    )
    result["not_observed_as_won"] = result["mqls"] - result["observed_wins"]
    result["conversion_rate_pct"] = [
        percentage(wins, mqls)
        for wins, mqls in zip(result["observed_wins"], result["mqls"])
    ]
    return result.sort_values(
        ["mqls", dimension], ascending=[False, True], kind="mergesort"
    ).reset_index(drop=True)


def build_seller_orders(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    item_orders = tables["items"].merge(
        tables["orders"][["order_id", "order_purchase_timestamp"]],
        on="order_id",
        how="left",
        validate="many_to_one",
    )
    seller_orders = (
        item_orders.dropna(
            subset=["seller_id", "order_id", "order_purchase_timestamp"]
        )
        .groupby(["seller_id", "order_id"], as_index=False)
        .agg(
            order_purchase_timestamp=("order_purchase_timestamp", "first"),
            item_count=("order_item_id", "count"),
            product_revenue=("price", "sum"),
        )
    )
    seller_count = seller_orders.groupby("order_id")["seller_id"].transform("nunique")
    seller_orders["single_seller_order"] = seller_count.eq(1)

    review_rollup = (
        tables["reviews"].groupby("order_id", as_index=False)
        .agg(review_score=("review_score", "mean"))
    )
    seller_orders = seller_orders.merge(
        review_rollup, on="order_id", how="left", validate="many_to_one"
    )
    seller_orders["low_review"] = seller_orders["review_score"].le(2)
    return seller_orders


def analyze(tables: dict[str, pd.DataFrame]) -> dict[str, object]:
    validate_source(tables)
    mql = tables["mql"].copy()
    closed = tables["closed"].copy()
    mql["origin"] = normalize_origin(mql["origin"])

    funnel = mql.merge(
        closed[["mql_id", "seller_id", "won_date"]],
        on="mql_id",
        how="left",
        validate="one_to_one",
    )
    funnel["is_won"] = funnel["seller_id"].notna()
    funnel["first_contact_month"] = (
        funnel["first_contact_date"].dt.to_period("M").astype("string")
    )

    by_origin = conversion_summary(funnel, "origin")
    by_month = conversion_summary(funnel, "first_contact_month").sort_values(
        "first_contact_month", kind="mergesort"
    ).reset_index(drop=True)
    by_landing_page = conversion_summary(funnel, "landing_page_id")
    by_landing_page = by_landing_page[
        by_landing_page["mqls"] >= LANDING_PAGE_MIN_MQLS
    ].reset_index(drop=True)

    closed_sellers = closed.merge(
        mql[["mql_id", "origin"]], on="mql_id", how="left", validate="one_to_one"
    )
    seller_orders = build_seller_orders(tables)
    marketplace_seller_ids = set(seller_orders["seller_id"])
    closed_sellers["linked_to_marketplace"] = closed_sellers["seller_id"].isin(
        marketplace_seller_ids
    )

    data_end = seller_orders["order_purchase_timestamp"].max()
    eligibility_cutoff = data_end - pd.Timedelta(days=POST_WIN_DAYS)
    closed_sellers["full_followup"] = (
        closed_sellers["won_date"].notna()
        & closed_sellers["won_date"].le(eligibility_cutoff)
    )
    eligible = closed_sellers[closed_sellers["full_followup"]].copy()

    events = seller_orders.merge(
        eligible[["seller_id", "origin", "won_date"]],
        on="seller_id",
        how="inner",
        validate="many_to_one",
    )
    events = events[
        events["order_purchase_timestamp"].ge(events["won_date"])
        & events["order_purchase_timestamp"].lt(
            events["won_date"] + pd.Timedelta(days=POST_WIN_DAYS)
        )
    ].copy()

    origin_base = (
        closed_sellers.groupby("origin", as_index=False)
        .agg(
            closed_sellers=("seller_id", "nunique"),
            linked_sellers=("linked_to_marketplace", "sum"),
            eligible_sellers=("full_followup", "sum"),
        )
    )
    event_metrics = (
        events.groupby("origin", as_index=False)
        .agg(
            active_sellers_30d=("seller_id", "nunique"),
            seller_orders_30d=("order_id", "count"),
            product_revenue_30d=("product_revenue", "sum"),
        )
    )
    reviewed = events[
        events["single_seller_order"] & events["review_score"].notna()
    ]
    review_metrics = (
        reviewed.groupby("origin", as_index=False)
        .agg(
            reviewed_seller_orders_30d=("order_id", "count"),
            average_review_30d=("review_score", "mean"),
            low_review_rate_30d=("low_review", lambda values: values.mean() * 100),
        )
    )
    seller_outcomes = (
        origin_base.merge(event_metrics, on="origin", how="left")
        .merge(review_metrics, on="origin", how="left")
        .fillna(
            {
                "active_sellers_30d": 0,
                "seller_orders_30d": 0,
                "product_revenue_30d": 0,
                "reviewed_seller_orders_30d": 0,
            }
        )
    )
    for column in (
        "linked_sellers",
        "eligible_sellers",
        "active_sellers_30d",
        "seller_orders_30d",
        "reviewed_seller_orders_30d",
    ):
        seller_outcomes[column] = seller_outcomes[column].astype(int)
    seller_outcomes["linkage_rate_pct"] = [
        percentage(linked, total)
        for linked, total in zip(
            seller_outcomes["linked_sellers"], seller_outcomes["closed_sellers"]
        )
    ]
    seller_outcomes["activation_rate_30d_pct"] = [
        percentage(active, eligible_count)
        for active, eligible_count in zip(
            seller_outcomes["active_sellers_30d"], seller_outcomes["eligible_sellers"]
        )
    ]
    active_denominator = seller_outcomes["active_sellers_30d"].astype(float).where(
        seller_outcomes["active_sellers_30d"].ne(0)
    )
    seller_outcomes["orders_per_active_seller_30d"] = (
        seller_outcomes["seller_orders_30d"] / active_denominator
    ).round(2)
    seller_outcomes["revenue_per_active_seller_30d"] = (
        seller_outcomes["product_revenue_30d"] / active_denominator
    ).round(2)
    seller_outcomes["product_revenue_30d"] = seller_outcomes[
        "product_revenue_30d"
    ].round(2)
    seller_outcomes["average_review_30d"] = seller_outcomes[
        "average_review_30d"
    ].round(2)
    seller_outcomes["low_review_rate_30d"] = seller_outcomes[
        "low_review_rate_30d"
    ].round(2)
    seller_outcomes = seller_outcomes.sort_values(
        ["eligible_sellers", "origin"], ascending=[False, True], kind="mergesort"
    ).reset_index(drop=True)

    first_orders = seller_orders.groupby("seller_id", as_index=False).agg(
        first_marketplace_order=("order_purchase_timestamp", "min")
    )
    linked_dates = closed_sellers.merge(first_orders, on="seller_id", how="inner")
    pre_win_sellers = int(
        linked_dates["first_marketplace_order"].lt(linked_dates["won_date"]).sum()
    )

    summary = {
        "mqls": int(len(mql)),
        "closed_deals": int(len(closed)),
        "overall_conversion_rate_pct": percentage(len(closed), len(mql)),
        "matched_closed_deals": int(closed["mql_id"].isin(mql["mql_id"]).sum()),
        "linked_sellers": int(closed_sellers["linked_to_marketplace"].sum()),
        "linkage_coverage_pct": percentage(
            closed_sellers["linked_to_marketplace"].sum(), len(closed_sellers)
        ),
        "eligible_sellers": int(closed_sellers["full_followup"].sum()),
        "active_sellers_30d": int(events["seller_id"].nunique()),
        "pre_win_sellers": pre_win_sellers,
        "data_end": data_end,
        "eligibility_cutoff": eligibility_cutoff,
        "mql_start": mql["first_contact_date"].min(),
        "mql_end": mql["first_contact_date"].max(),
        "won_start": closed["won_date"].min(),
        "won_end": closed["won_date"].max(),
        "landing_pages_meeting_threshold": int(len(by_landing_page)),
    }

    result = {
        "summary": summary,
        "by_origin": by_origin,
        "by_month": by_month,
        "by_landing_page": by_landing_page,
        "seller_outcomes": seller_outcomes,
        "events": events,
        "reviewed_events": reviewed,
    }
    validate_analysis(result)
    return result


def validate_analysis(result: dict[str, object]) -> list[str]:
    summary = result["summary"]
    by_origin = result["by_origin"]
    seller_outcomes = result["seller_outcomes"]
    reviewed = result["reviewed_events"]
    checks = []

    def check(condition: bool, label: str) -> None:
        if not condition:
            raise AssertionError(f"Marketing-funnel check failed: {label}")
        checks.append(label)

    check(summary["mqls"] == int(by_origin["mqls"].sum()), "origin MQL counts reconcile")
    check(
        summary["closed_deals"] == int(by_origin["observed_wins"].sum()),
        "origin win counts reconcile",
    )
    check(summary["matched_closed_deals"] == summary["closed_deals"], "all wins match MQLs")
    check(summary["linked_sellers"] <= summary["closed_deals"], "linkage count is bounded")
    check(summary["active_sellers_30d"] <= summary["eligible_sellers"], "activation is bounded")
    check(by_origin["origin"].notna().all(), "origin is fully normalized")
    check(
        by_origin["conversion_rate_pct"].between(0, 100).all(),
        "conversion rates are bounded",
    )
    check(
        seller_outcomes["activation_rate_30d_pct"].between(0, 100).all(),
        "activation rates are bounded",
    )
    check(
        seller_outcomes["average_review_30d"].dropna().between(1, 5).all(),
        "average reviews are bounded",
    )
    check(
        seller_outcomes["low_review_rate_30d"].dropna().between(0, 100).all(),
        "low-review rates are bounded",
    )
    check(reviewed["single_seller_order"].all(), "review metrics exclude multi-seller orders")
    check(
        int(seller_outcomes["reviewed_seller_orders_30d"].sum()) == len(reviewed),
        "review denominators reconcile",
    )
    return checks


def save_origin_chart(by_origin: pd.DataFrame, overall_rate: float, output: Path) -> None:
    plot = by_origin.sort_values("conversion_rate_pct")
    colors = [
        "#6b7280"
        if origin == UNKNOWN_ORIGIN
        else "#177245"
        if rate >= overall_rate
        else "#b45309"
        for origin, rate in zip(plot["origin"], plot["conversion_rate_pct"])
    ]
    fig, ax = plt.subplots(figsize=(10, 6.4))
    bars = ax.barh(plot["origin"], plot["conversion_rate_pct"], color=colors)
    ax.axvline(
        overall_rate,
        color="#9f1239",
        linestyle="--",
        linewidth=1.5,
        label=f"Overall observed conversion: {overall_rate:.2f}%",
    )
    for bar, rate in zip(bars, plot["conversion_rate_pct"]):
        ax.text(
            bar.get_width() + 0.25,
            bar.get_y() + bar.get_height() / 2,
            f"{rate:.2f}%",
            va="center",
            fontsize=9,
        )
    ax.set_title("Observed MQL-to-closed-deal conversion by origin")
    ax.set_xlabel("Observed conversion rate (%)")
    ax.set_ylabel("Marketing origin")
    ax.set_xlim(0, plot["conversion_rate_pct"].max() + 4)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def markdown_rows(frame: pd.DataFrame, columns: list[str], formats: dict[str, str]) -> str:
    rows = []
    for _, row in frame.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if pd.isna(value):
                values.append("n/a")
            elif column in formats:
                rendered = format(value, formats[column])
                is_percentage = column.endswith("_pct") or "_rate_" in column
                values.append(f"{rendered}%" if is_percentage else rendered)
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def build_report(result: dict[str, object]) -> str:
    summary = result["summary"]
    by_origin = result["by_origin"]
    by_month = result["by_month"]
    outcomes = result["seller_outcomes"]

    origin_rows = markdown_rows(
        by_origin,
        ["origin", "mqls", "observed_wins", "not_observed_as_won", "conversion_rate_pct"],
        {"mqls": ",.0f", "observed_wins": ",.0f", "not_observed_as_won": ",.0f", "conversion_rate_pct": ".2f"},
    )
    month_rows = markdown_rows(
        by_month,
        ["first_contact_month", "mqls", "observed_wins", "conversion_rate_pct"],
        {"mqls": ",.0f", "observed_wins": ",.0f", "conversion_rate_pct": ".2f"},
    )
    outcome_rows = markdown_rows(
        outcomes,
        [
            "origin",
            "closed_sellers",
            "linked_sellers",
            "eligible_sellers",
            "active_sellers_30d",
            "activation_rate_30d_pct",
            "orders_per_active_seller_30d",
            "revenue_per_active_seller_30d",
            "average_review_30d",
            "low_review_rate_30d",
        ],
        {
            "closed_sellers": ",.0f",
            "linked_sellers": ",.0f",
            "eligible_sellers": ",.0f",
            "active_sellers_30d": ",.0f",
            "activation_rate_30d_pct": ".2f",
            "orders_per_active_seller_30d": ".2f",
            "revenue_per_active_seller_30d": ",.2f",
            "average_review_30d": ".2f",
            "low_review_rate_30d": ".2f",
        },
    )

    unknown = by_origin.loc[by_origin["origin"].eq(UNKNOWN_ORIGIN)].iloc[0]
    known = by_origin[~by_origin["origin"].eq(UNKNOWN_ORIGIN)]
    large_known = known[known["mqls"] >= 400]
    above = large_known[
        large_known["conversion_rate_pct"] >= summary["overall_conversion_rate_pct"]
    ]["origin"].tolist()
    below = large_known[
        large_known["conversion_rate_pct"] < summary["overall_conversion_rate_pct"]
    ]["origin"].tolist()
    if summary["pre_win_sellers"]:
        pre_win_note = (
            f"- {summary['pre_win_sellers']:,} linked sellers have a marketplace order "
            "before `won_date`; the deal date is therefore not always a clean "
            "first-activation boundary."
        )
    else:
        pre_win_note = (
            "- No linked seller has an item-backed marketplace order before `won_date`, "
            "which supports using that date as the start of the fixed outcome window."
        )

    return f"""# Marketing Funnel and Seller Acquisition Analysis

This Issue #10 report is generated from the committed workbook by
`scripts/build_marketing_funnel_analysis.py`. It replaces the Colab-only workflow
with a deterministic repository-owned analysis.

## Decision

Use the marketing funnel as **supporting evidence**, not as the core marketplace
growth argument. The MQL-to-deal join is complete, but only
**{summary['linked_sellers']:,} of {summary['closed_deals']:,} closed sellers
({summary['linkage_coverage_pct']:.2f}%)** appear in marketplace order items.
Acquisition origin can therefore be associated with observed outcomes for a
limited subset, but it cannot be treated as the cause of those outcomes.

## Funnel baseline

| Metric | Result |
| --- | ---: |
| Marketing-qualified leads | {summary['mqls']:,} |
| Closed deals observed | {summary['closed_deals']:,} |
| Observed conversion rate | {summary['overall_conversion_rate_pct']:.2f}% |
| Closed deals matched to an MQL | {summary['matched_closed_deals']:,} |
| Closed sellers linked to marketplace items | {summary['linked_sellers']:,} |
| Marketplace linkage coverage | {summary['linkage_coverage_pct']:.2f}% |

"Observed conversion" means a matching closed-deal record exists in the dataset.
The remaining leads are **not observed as won by the dataset snapshot**; they are
not proven losses.

## Conversion by marketing origin

![Observed conversion by marketing origin](marketing_funnel_conversion_by_origin.png)

| Origin | MQLs | Observed wins | Not observed as won | Conversion rate |
| --- | ---: | ---: | ---: | ---: |
{origin_rows}

Among known origins with at least 400 MQLs, the origins at or above the overall
rate are **{', '.join(above)}**. The below-benchmark diagnostic queue is
**{', '.join(below)}**. This is a queue for investigation, not a budget-allocation
recommendation, because spend, acquisition cost, lead quality, and opportunity
value are unavailable.

`unknown` and blank origins are normalized into one **{UNKNOWN_ORIGIN}** category.
It contains **{int(unknown['mqls']):,} MQLs** and **{int(unknown['observed_wins']):,}
observed wins**. Its apparent conversion rate is an attribution-quality signal,
not evidence that an unknown channel performs well.

## Contact-month context

| First-contact month | MQLs | Observed wins | Conversion rate |
| --- | ---: | ---: | ---: |
{month_rows}

Contact-month conversion is descriptive. Later cohorts can have less time to
close before the dataset snapshot, so month-to-month changes must not be read as
pure marketing-performance changes without a common lead-maturity window.

Landing-page analysis is retained only as an exploratory check. Pages require at
least **{LANDING_PAGE_MIN_MQLS} MQLs**, leaving
**{summary['landing_pages_meeting_threshold']} pages**. The IDs are opaque and
multiple comparisons remain noisy, so landing pages are excluded from the final
recommendation.

## Comparable seller outcomes

The marketplace seller comparison uses the first **{POST_WIN_DAYS} days after
each seller's `won_date`**. A seller is eligible only if all {POST_WIN_DAYS} days
occur on or before the final item-backed marketplace purchase date,
**{summary['data_end']:%Y-%m-%d}**. The eligibility cutoff is
**{summary['eligibility_cutoff']:%Y-%m-%d}**, leaving
**{summary['eligible_sellers']:,} closed sellers** with equal follow-up and
**{summary['active_sellers_30d']:,}** with at least one observed seller-order in
that window.

| Origin | Closed | Linked | Eligible | Active in 30d | Activation | Orders per active seller | Product revenue per active seller | Average review | Low-review rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{outcome_rows}

Product revenue is the sum of item `price` and excludes freight. Activation uses
all eligible closed sellers as its denominator. Per-seller order and revenue
metrics use active sellers as their denominator.

Review metrics use one order-level review rollup joined only to single-seller
orders. This keeps the review numerator and denominator at the same reviewed
seller-order grain and avoids assigning one multi-seller order review to several
sellers. Low review means an order-level average review score of 2 or less.

## Limitations

- Only {summary['linkage_coverage_pct']:.2f}% of closed sellers link to marketplace items.
{pre_win_note}
- Marketing origin is observational and cannot establish causality.
- The {POST_WIN_DAYS}-day window improves comparability but captures only early
  seller outcomes and may miss later activation.
- Multi-seller orders are excluded from review comparisons; order-level reviews
  cannot be attributed reliably to one seller in those orders.
- Missing/unknown origin represents an attribution problem, not a real channel.
- Funnel dates cover {summary['mql_start']:%Y-%m-%d} to {summary['mql_end']:%Y-%m-%d}
  for first contact and {summary['won_start']:%Y-%m-%d} to
  {summary['won_end']:%Y-%m-%d} for observed wins.

## Recommendation

Use paid, organic, direct, social, and email results to form diagnostic questions
for the marketing team. Investigate why high-volume below-benchmark origins have
many leads not observed as won, and repair origin attribution before comparing
channel efficiency. Do not shift spend from this dataset alone. Keep the final
marketplace-growth story centered on orders, delivery, products, sellers, and
regions; use this funnel section as acquisition context.

## Reproduction and validation

```bash
python3 scripts/build_marketing_funnel_analysis.py
python3 scripts/build_live_report_pages.py
python3 scripts/validate_marketing_funnel_analysis.py
```

The build command regenerates this report and its PNG chart in `docs/eda/`.
The validation command checks source keys, totals, linkage, bounded rates,
equal-window eligibility, single-seller review attribution, report values, and
published-page generation.
"""


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = analyze(load_tables(args.workbook, args.source_dir))
    chart_path = args.output_dir / "marketing_funnel_conversion_by_origin.png"
    save_origin_chart(
        result["by_origin"],
        result["summary"]["overall_conversion_rate_pct"],
        chart_path,
    )
    report_path = args.output_dir / "marketing_funnel_analysis.md"
    report_path.write_text(build_report(result), encoding="utf-8")
    print(f"Wrote marketing funnel report to {report_path}")
    print(f"Wrote marketing funnel chart to {chart_path}")


if __name__ == "__main__":
    main()
